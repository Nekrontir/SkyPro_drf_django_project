from django.contrib import admin

from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ("email", "phone", "city", "is_staff", "date_joined")
