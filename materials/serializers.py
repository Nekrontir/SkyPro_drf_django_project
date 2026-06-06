from rest_framework import serializers

from .models import Course, Lesson, Subscription
from .validators import validate_youtube_link


class LessonSerializer(serializers.ModelSerializer):
    # Применяем валидатор только к полю link
    link = serializers.URLField(validators=[validate_youtube_link])

    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ('owner',)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки (для вложенного отображения)"""

    class Meta:
        model = Subscription
        fields = ('id', 'course', 'created_at')


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ('owner',)

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на курс"""
        if self.context.get('request') and self.context['request'].user.is_authenticated:
            return Subscription.objects.filter(
                user=self.context['request'].user,
                course=obj
            ).exists()
        return False