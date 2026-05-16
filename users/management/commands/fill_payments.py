import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from materials.models import Course, Lesson
from users.models import CustomUser, Payment


class Command(BaseCommand):
    """
    Заполняет БД тестовыми платежами и необходимыми связанными объектами
    """

    def handle(self, *args, **kwargs):
        # Создаём пользователя
        user, _ = CustomUser.objects.get_or_create(email="test@example.com", defaults={"password": "testpass123"})
        # Создаём курс
        course, _ = Course.objects.get_or_create(
            title="Тестовый курс", defaults={"description": "Описание тестового курса"}
        )
        # Создаём урок
        lesson, _ = Lesson.objects.get_or_create(
            title="Тестовый урок",
            defaults={"description": "Описание урока", "course": course, "link": "https://example.com/video"},
        )

        # Удаляем старые платежи
        Payment.objects.all().delete()

        # Создаём три платежа
        Payment.objects.create(
            user=user,
            payment_date=timezone.make_aware(datetime.datetime(2026, 5, 15, 12, 0, 0)),
            course=course,
            lesson=None,
            amount=5000.00,
            payment_method="transfer",
        )
        Payment.objects.create(
            user=user,
            payment_date=timezone.make_aware(datetime.datetime(2026, 5, 16, 10, 30, 0)),
            course=None,
            lesson=lesson,
            amount=1500.00,
            payment_method="cash",
        )
        Payment.objects.create(
            user=user,
            payment_date=timezone.make_aware(datetime.datetime(2026, 5, 14, 9, 0, 0)),
            course=course,
            lesson=None,
            amount=5000.00,
            payment_method="cash",
        )

        self.stdout.write(self.style.SUCCESS("Тестовые данные успешно загружены"))
