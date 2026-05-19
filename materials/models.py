from django.conf import settings
from django.db import models


class Course(models.Model):
    """
    Курс:
        название,
        превью (картинка),
        описание.
    """

    title = models.CharField(max_length=100, verbose_name="Курс")
    preview = models.ImageField(upload_to="course_previews/", blank=True, null=True, verbose_name="Превью курса")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Владелец",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """
    Урок:
        название,
        описание,
        превью (картинка),
        ссылка на видео.
    """

    title = models.CharField(max_length=100, verbose_name="Урок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    preview = models.ImageField(upload_to="lesson_previews/", blank=True, null=True, verbose_name="Превью урока")
    link = models.URLField(blank=True, null=True, verbose_name="Ссылка на видео")

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Владелец",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"

    def __str__(self):
        return self.title
