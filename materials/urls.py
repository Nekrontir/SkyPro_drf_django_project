from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (CourseViewSet, LessonCreateView, LessonDeleteView, LessonDetailView, LessonListView,
                    LessonUpdateView)

app_name = "materials"

router = DefaultRouter()
router.register(r"courses", CourseViewSet)

urlpatterns = [
    # Уроки
    path("lessons/create/", LessonCreateView.as_view(), name="lesson-create"),           # POST -> создать
    path("lessons/", LessonListView.as_view(), name="lesson-list"),                      # GET -> список
    path("lessons/<int:pk>/", LessonDetailView.as_view(), name="lesson-detail"),         # GET -> один урок
    path("lessons/<int:pk>/update/", LessonUpdateView.as_view(), name="lesson-update"),  # PUT/PATCH
    path("lessons/<int:pk>/delete/", LessonDeleteView.as_view(), name="lesson-delete"),  # DELETE
    # Курсы
    path("", include(router.urls)),
]
