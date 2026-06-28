from urllib.parse import urljoin

import stripe
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiRequest, OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser, Payment
from .serializers import PaymentSerializer, UserSerializer, UserUpdateSerializer
from .stripe_service import create_stripe_checkout_session, create_stripe_price, create_stripe_product


class UserRegisterView(generics.CreateAPIView):
    """Регистрация пользователя – доступна без авторизации."""

    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class UserProfileView(generics.RetrieveUpdateDestroyAPIView):
    """Профиль – только авторизованному пользователю."""

    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema(
    description="Список платежей с возможностью фильтрации и сортировки.",
    parameters=[
        OpenApiParameter(
            name="course",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="ID курса для фильтрации платежей",
        ),
        OpenApiParameter(
            name="lesson",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="ID урока для фильтрации платежей",
        ),
        OpenApiParameter(
            name="payment_method",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Способ оплаты: 'cash' или 'transfer'",
        ),
        OpenApiParameter(
            name="ordering",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description="Сортировка по полю, например: 'payment_date' или '-payment_date'",
        ),
    ],
)
class PaymentListView(generics.ListAPIView):
    """Информация об оплате"""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["course", "lesson", "payment_method"]
    ordering_fields = ["payment_date"]


@extend_schema(
    description="Создать платеж и получить ссылку на оплату через Stripe.\n"
    "Необходимо передать course_id (или lesson_id) и amount.\n"
    "Создаётся продукт и цена в Stripe, затем Checkout Session.\n"
    "В ответ возвращается URL для оплаты.",
    request=OpenApiRequest(
        {
            "application/json": {
                "type": "object",
                "properties": {
                    "course_id": {
                        "type": "integer",
                        "description": "ID курса, который оплачивается (обязательно, если lesson_id не указан)",
                    },
                    "lesson_id": {
                        "type": "integer",
                        "description": "ID урока, который оплачивается (обязательно, если course_id не указан)",
                    },
                    "amount": {
                        "type": "number",
                        "format": "double",
                        "description": "Сумма оплаты (в рублях с копейками, например 1500.00)",
                    },
                },
                "required": ["amount"],
            }
        }
    ),
    responses={
        201: OpenApiResponse(
            description="Платёж создан, ссылка на оплату возвращена",
            response={
                "type": "object",
                "properties": {
                    "payment_id": {"type": "integer", "example": 1},
                    "checkout_url": {"type": "string", "example": "https://checkout.stripe.com/..."},
                    "stripe_product_id": {"type": "string", "example": "prod_XXX"},
                    "stripe_price_id": {"type": "string", "example": "price_XXX"},
                    "stripe_session_id": {"type": "string", "example": "cs_XXX"},
                },
            },
        ),
        400: OpenApiResponse(
            description="Ошибочный запрос (не передан course_id/lesson_id или amount)",
            response={
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Не указан course_id или lesson_id"},
                },
            },
        ),
        401: OpenApiResponse(description="Неавторизованный пользователь"),
    },
)
class PaymentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user

        course_id = request.data.get("course_id")
        lesson_id = request.data.get("lesson_id")
        amount = request.data.get("amount")

        if not amount:
            return Response(
                {"error": "Не указана сумма оплаты (amount)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not course_id and not lesson_id:
            return Response(
                {"error": "Не указан course_id или lesson_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from materials.models import Course, Lesson

        course = None
        lesson = None

        if course_id:
            try:
                course = Course.objects.get(id=course_id)
            except Course.DoesNotExist:
                return Response(
                    {"error": "Курс не найден"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        if lesson_id:
            try:
                lesson = Lesson.objects.get(id=lesson_id)
            except Lesson.DoesNotExist:
                return Response(
                    {"error": "Урок не найден"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Формируем название продукта
        if course:
            product_name = f"Курс: {course.title}"
            product_description = course.description or "Оплата курса"
        else:
            product_name = f"Урок: {lesson.title}"
            product_description = lesson.description or "Оплата урока"

        # Сумма в копейках (центах)
        amount_cents = int(float(amount) * 100)

        # Создаём продукт в Stripe
        try:
            stripe_product_id = create_stripe_product(product_name, product_description)
        except Exception as e:
            return Response(
                {"error": f"Ошибка при создании продукта в Stripe: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаём цену в Stripe
        try:
            stripe_price_id = create_stripe_price(stripe_product_id, amount_cents, currency="rub")
        except Exception as e:
            return Response(
                {"error": f"Ошибка при создании цены в Stripe: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Формируем success_url и cancel_url
        base_url = request.build_absolute_uri("/").rstrip("/")
        success_url = urljoin(base_url, "/api/payment-success/")
        cancel_url = urljoin(base_url, "/api/payment-cancel/")

        # Создаём Checkout Session
        try:
            stripe_session_id, checkout_url = create_stripe_checkout_session(
                stripe_price_id,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except Exception as e:
            return Response(
                {"error": f"Ошибка при создании Checkout Session в Stripe: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Создаём платеж в нашей БД
        payment = Payment.objects.create(
            user=user,
            course=course,
            lesson=lesson,
            amount=amount,
            payment_method="transfer",
            stripe_product_id=stripe_product_id,
            stripe_price_id=stripe_price_id,
            stripe_session_id=stripe_session_id,
            checkout_url=checkout_url,
            stripe_payment_status="open",
        )

        return Response(
            {
                "payment_id": payment.id,
                "checkout_url": payment.checkout_url,
                "stripe_product_id": payment.stripe_product_id,
                "stripe_price_id": payment.stripe_price_id,
                "stripe_session_id": payment.stripe_session_id,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    description="Получить статус платежа по payment_id и синхронизировать его с данными в модели Payment.",
    parameters=[
        OpenApiParameter(
            name="payment_id",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description="ID платежа в системе",
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Статус платежа успешно получен",
            response={
                "type": "object",
                "properties": {
                    "payment_id": {"type": "integer"},
                    "stripe_payment_status": {"type": "string", "example": "complete"},
                },
            },
        ),
        400: OpenApiResponse(
            description="Ошибочный запрос",
            response={
                "type": "object",
                "properties": {
                    "error": {"type": "string", "example": "Не указан payment_id"},
                },
            },
        ),
        401: OpenApiResponse(description="Неавторизованный пользователь"),
    },
)
class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        payment_id = request.query_params.get("payment_id")
        if not payment_id:
            return Response(
                {"error": "Не указан payment_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(id=payment_id, user=request.user)
        except Payment.DoesNotExist:
            return Response(
                {"error": "Платёж не найден"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not payment.stripe_session_id:
            return Response(
                {"error": "У платежа нет привязанной Stripe сессии"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe.api_key = settings.STRIPE_SECRET_KEY

        try:
            session = stripe.checkout.Session.retrieve(payment.stripe_session_id)
        except Exception as e:
            return Response(
                {"error": f"Ошибка при получении статуса сессии в Stripe: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment.stripe_payment_status = session.status
        payment.save()

        return Response(
            {
                "payment_id": payment.id,
                "stripe_payment_status": payment.stripe_payment_status,
            },
            status=status.HTTP_200_OK,
        )
