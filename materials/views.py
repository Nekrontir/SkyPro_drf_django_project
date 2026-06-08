from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiRequest, OpenApiResponse, extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Course, Lesson, Subscription
from .paginators import CourseLessonPagination
from .permissions import IsModeratorOrOwner, IsOwner
from .serializers import CourseSerializer, LessonSerializer
from .tasks import send_course_update_email


# CRUD для курса через ViewSet
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('id')
    serializer_class = CourseSerializer
    pagination_class = CourseLessonPagination

    def get_permissions(self):
        if self.action in ["create", "destroy"]:
            # модераторам запрещено создавать и удалять
            self.permission_classes = [IsAuthenticated]
        elif self.action in ["update", "partial_update", "retrieve"]:
            self.permission_classes = [IsAuthenticated, IsModeratorOrOwner]
        else:  # list
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        if self.action == "list" and not user.groups.filter(name="Модераторы").exists():
            return Course.objects.filter(owner=user).order_by('id')
        return super().get_queryset()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        course = serializer.save()
        # Проверяем, когда курс обновлялся последний раз
        if course.updated_at and timezone.now() - course.updated_at < timedelta(hours=4):
            return
        send_course_update_email.delay(course.id)


# CRUD для урока через Generic классы
# 1. Получение списка уроков
class LessonListView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = CourseLessonPagination

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.all().order_by('id')
        return Lesson.objects.filter(owner=user).order_by('id')


# 2. Создание нового урока
class LessonCreateView(generics.CreateAPIView):
    queryset = Lesson.objects.all().order_by('id')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


# 3. Получение одного урока
class LessonDetailView(generics.RetrieveAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrOwner]
    queryset = Lesson.objects.all().order_by('id')


# 4. Обновление (PUT + PATCH)
class LessonUpdateView(generics.UpdateAPIView):
    queryset = Lesson.objects.all().order_by('id')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsModeratorOrOwner]


# 5. Удаление
class LessonDeleteView(generics.DestroyAPIView):
    queryset = Lesson.objects.all().order_by('id')
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def perform_destroy(self, instance):
        # Проверяем, что пользователь является владельцем
        if instance.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Вы можете удалять только свои уроки")
        instance.delete()


# Эндпоинт для управления подпиской на курс
@extend_schema(
    methods=["POST"],
    description="Создать или удалить подписку текущего пользователя на курс.\n"
                "Если подписки нет — создаётся, если есть — удаляется.",
    request=OpenApiRequest(
        {
            "application/json": {
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "ID курса, на который оформляется подписка",
                    }
                },
                "required": ["course_id"],
            }
        }
    ),
    responses={
        200: OpenApiResponse(
            description="Успешное добавление или удаление подписки",
            response={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Подписка добавлена",
                    }
                },
            },
        ),
        400: OpenApiResponse(
            description="Ошибочный запрос (например, не передан course_id)",
            response={
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Не указан course_id",
                    }
                },
            },
        ),
        401: OpenApiResponse(description="Неавторизованный пользователь"),
    },
)
class SubscriptionView(APIView):
    """
    Эндпоинт для установки/удаления подписки пользователя на курс.
    POST: {course_id}: создать подписку или удалить, если уже есть.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {"error": "Не указан course_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        course_item = get_object_or_404(Course, id=course_id)

        subs_item = Subscription.objects.filter(user=user, course=course_item)

        if subs_item.exists():
            subs_item.delete()
            message = 'Подписка удалена'
        else:
            Subscription.objects.create(user=user, course=course_item)
            message = 'Подписка добавлена'

        return Response({"message": message}, status=status.HTTP_200_OK)