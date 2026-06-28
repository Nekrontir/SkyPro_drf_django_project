from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Course, Lesson, Subscription

User = get_user_model()


class TestCourseLessonCRUD(APITestCase):
    """Тесты для CRUD уроков и курсов"""

    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = APIClient()

        # Создаём пользователей разных групп
        self.normal_user = User.objects.create_user(email="user@test.com", password="testpass123", first_name="Normal")

        self.moderator = User.objects.create_user(email="mod@test.com", password="testpass123", first_name="Moderator")
        self.moderator.groups.create(name="Модераторы")

        self.admin = User.objects.create_superuser(
            email="admin@test.com",
            password="testpass123",
        )

        # Создаём курс и урок для тестов
        self.course = Course.objects.create(
            title="Тестовый курс", description="Описание курса", owner=self.normal_user
        )

        self.lesson = Lesson.objects.create(
            title="Тестовый урок",
            description="Описание урока",
            link="https://www.youtube.com/watch?v=test",
            course=self.course,
            owner=self.normal_user,
        )

    # === ТЕСТЫ СОЗДАНИЯ ===

    def test_create_lesson_authenticated(self):
        """Тест создания урока авторизованным пользователем"""
        self.client.force_authenticate(user=self.normal_user)

        url = "/api/lessons/create/"
        data = {
            "title": "Новый урок",
            "description": "Новое описание",
            "link": "https://www.youtube.com/watch?v=newvideo",
            "course": self.course.id,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lesson.objects.filter(title="Новый урок").exists())

    def test_create_lesson_unauthenticated(self):
        """Тест создания урока без авторизации"""
        url = "/api/lessons/create/"
        data = {"title": "Новый урок", "link": "https://www.youtube.com/watch?v=newvideo", "course": self.course.id}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_lesson_invalid_link(self):
        """Тест создания урока с невалидной ссылкой (не youtube)"""
        self.client.force_authenticate(user=self.normal_user)

        url = "/api/lessons/create/"
        data = {
            "title": "Невалидный урок",
            "link": "https://example.com/video",  # не youtube
            "course": self.course.id,
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # === ТЕСТЫ ПОЛУЧЕНИЯ ===

    def test_get_lesson_list_authenticated(self):
        """Тест получения списка уроков"""
        self.client.force_authenticate(user=self.normal_user)

        url = "/api/lessons/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_lesson_detail(self):
        """Тест получения одного урока"""
        self.client.force_authenticate(user=self.normal_user)

        url = f"/api/lessons/{self.lesson.id}/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.lesson.title)

    # === ТЕСТЫ ОБНОВЛЕНИЯ (используем PATCH) ===

    def test_update_lesson_owner(self):
        """Тест обновления урока владельцем"""
        self.client.force_authenticate(user=self.normal_user)

        url = f"/api/lessons/{self.lesson.id}/update/"
        data = {"title": "Обновлённый урок"}

        response = self.client.patch(url, data)  # PATCH вместо PUT

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Обновлённый урок")

    def test_update_lesson_moderator(self):
        """Тест обновления урока модератором"""
        self.client.force_authenticate(user=self.moderator)

        url = f"/api/lessons/{self.lesson.id}/update/"
        data = {"title": "Обновлённый модератором"}

        response = self.client.patch(url, data)  # PATCH вместо PUT

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # === ТЕСТЫ УДАЛЕНИЯ ===

    def test_delete_lesson_owner(self):
        """Тест удаления урока владельцем"""
        self.client.force_authenticate(user=self.normal_user)

        url = f"/api/lessons/{self.lesson.id}/delete/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(id=self.lesson.id).exists())

    def test_delete_lesson_moderator_forbidden(self):
        """Тест: модератор не может удалять уроки"""
        # Пересоздаём урок для теста
        self.lesson = Lesson.objects.create(
            title="Тестовый урок 2",
            description="Описание урока",
            link="https://www.youtube.com/watch?v=test",
            course=self.course,
            owner=self.normal_user,
        )

        self.client.force_authenticate(user=self.moderator)

        url = f"/api/lessons/{self.lesson.id}/delete/"
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # === ТЕСТЫ ПОДПИСКИ ===

    def test_subscription_create(self):
        """Тест создания подписки"""
        self.client.force_authenticate(user=self.normal_user)

        url = "/api/subscribe/"
        data = {"course_id": self.course.id}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка добавлена")
        self.assertTrue(Subscription.objects.filter(user=self.normal_user, course=self.course).exists())

    def test_subscription_delete(self):
        """Тест удаления подписки"""
        # Сначала создаём подписку
        Subscription.objects.create(user=self.normal_user, course=self.course)

        self.client.force_authenticate(user=self.normal_user)

        url = "/api/subscribe/"
        data = {"course_id": self.course.id}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка удалена")
        self.assertFalse(Subscription.objects.filter(user=self.normal_user, course=self.course).exists())

    def test_subscription_unauthenticated(self):
        """Тест подписки без авторизации"""
        url = "/api/subscribe/"
        data = {"course_id": self.course.id}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_subscription_missing_course_id(self):
        """Тест подписки без указания course_id"""
        self.client.force_authenticate(user=self.normal_user)

        url = "/api/subscribe/"
        data = {}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # === ТЕСТЫ ДОСТУПА ДЛЯ РАЗНЫХ ГРУПП ===

    def test_moderator_can_view_all_lessons(self):
        """Модератор видит все уроки"""
        self.client.force_authenticate(user=self.moderator)

        url = "/api/lessons/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
