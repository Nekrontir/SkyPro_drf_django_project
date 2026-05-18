from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import PaymentListView, UserRegisterView, UserProfileView

app_name = "users"

urlpatterns = [
    # JWT
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Пользователи
    path('register/', UserRegisterView.as_view(), name='register'),
    path('profile/', UserProfileView.as_view(), name='profile'),
    # Платежи
    path("payments/", PaymentListView.as_view(), name="payment-list"),
]