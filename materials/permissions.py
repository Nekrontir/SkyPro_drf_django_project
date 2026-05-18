from rest_framework.permissions import BasePermission


class IsModerator(BasePermission):
    """Проверяет, входит ли пользователь в группу 'Модераторы'."""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name="Модераторы").exists()


class IsOwner(BasePermission):
    """Проверяет, является ли пользователь владельцем объекта."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsModeratorOrOwner(BasePermission):
    """Доступ для модераторов или владельцев объекта."""

    def has_object_permission(self, request, view, obj):
        return IsModerator().has_permission(request, view) or obj.owner == request.user
