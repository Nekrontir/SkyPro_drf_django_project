from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from users.models import CustomUser

from .models import Course, Subscription


@shared_task
def send_course_update_email(course_id):
    """
    Отправка писем подписчикам курса об обновлении материалов.
    """
    course = Course.objects.get(id=course_id)
    subscriptions = Subscription.objects.filter(course=course)

    subject = f"Обновление материала курса: {course.title}"
    message = f'Курс "{course.title}" был обновлён! Проверьте новые материалы.'

    emails = [s.user.email for s in subscriptions if s.user.email]

    if not emails:
        return

    # Отправка одним вызовом — Recipient list батчем
    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=emails,
        fail_silently=True,
    )


@shared_task
def block_inactive_users():
    """
    Блокирует пользователей, которые не заходили более месяца.
    """
    one_month_ago = timezone.now() - timedelta(days=30)

    # Выборка только активных, у кого last_login старый или None
    qs = CustomUser.objects.filter(
        is_active=True,
        last_login__lt=one_month_ago,
    )

    # Обновление батчем
    qs.update(is_active=False)
