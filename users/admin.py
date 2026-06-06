from django.contrib import admin

from .models import CustomUser, Payment


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "phone", "city", "is_staff", "date_joined")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "payment_date", "course", "lesson", "payment_method", "amount", "stripe_product_id", "stripe_payment_status")

