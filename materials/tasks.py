import os
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from celery import shared_task
from .models import Course, Subscription
from users.models import CustomUser


@shared_task
def send_course_update_email(course_id):
    """
    Задача для отправки писем пользователям о обновлении курса.
    Вызывается строго после успешного обновления курса.
    """
    from django.core.mail import send_mail

    course = Course.objects.get(id=course_id)

    # Получаем всех подписчиков курса
    subscriptions = Subscription.objects.filter(course=course)

    # Формируем сообщение
    subject = f'Обновление материала курса: {course.title}'
    message = f'Курс "{course.title}" был обновлен! Проверьте новые материалы.'

    # Отправляем письма всем подписчикам батчем (не по одному)
    for subscription in subscriptions:
        user_email = subscription.user.email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user_email],
            )
        except Exception:
            # Если письмо не отправилось, продолжаем дальше
            pass


@shared_task
def block_inactive_users():
    """
    Периодическая задача для блокировки пользователей,
    которые не заходили более месяца.
    Использует timezone.now() для корректной работы с таймзоной.
    """
    # Проверяем: last_login < (текущее время - 1 месяц)
    one_month_ago = timezone.now() - timedelta(days=30)

    # Выборка пользователей, которые не заходили более месяца
    # и ещё активны
    inactive_users = CustomUser.objects.filter(
        last_login__lt=one_month_ago,
        is_active=True
    )

    # Блокируем всех батчем (не по одному)
    for user in inactive_users:
        user.is_active = False
        user.save()