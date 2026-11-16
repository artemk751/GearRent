from django.urls import path

from .views import LoginView, MeView, RefreshView, RegisterView, UserListView

urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="register"),
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/refresh", RefreshView.as_view(), name="token-refresh"),
    path("users/me", MeView.as_view(), name="me"),
    path("users", UserListView.as_view(), name="user-list"),
]
