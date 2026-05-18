from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Payment, CustomUser
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


class PaymentListView(generics.ListAPIView):
    """Информация об оплате"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["course", "lesson", "payment_method"]
    ordering_fields = ["payment_date"]
