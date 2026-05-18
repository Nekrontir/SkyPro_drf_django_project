from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import CustomUser, Payment


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ("id", "email", "phone", "city", "avatar", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            phone=validated_data.get("phone"),
            city=validated_data.get("city"),
            avatar=validated_data.get("avatar"),
        )
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Обновление профиля – без пароля"""

    class Meta:
        model = CustomUser
        fields = ("email", "phone", "city", "avatar")
        read_only_fields = ("email",)


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
