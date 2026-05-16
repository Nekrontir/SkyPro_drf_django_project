from django.urls import path
from .views import PaymentListView

app_name = 'users'

urlpatterns = [
    path('payments/', PaymentListView.as_view(), name='payment-list'),
]