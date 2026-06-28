from rest_framework.pagination import PageNumberPagination


class CourseLessonPagination(PageNumberPagination):
    """Пагинация для курсов и уроков"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50
