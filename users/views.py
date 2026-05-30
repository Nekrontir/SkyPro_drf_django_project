from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import CustomUser, Payment
from .serializers import PaymentSerializer, UserSerializer, UserUpdateSerializer


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
