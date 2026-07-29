"""Root URL configuration for the MDM project."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path("admin/", admin.site.urls),
    # ── REST API for other systems ────────────────────────────────────────────
    path("api/", include("mdm.api.urls")),
    path("api/auth/token/", obtain_auth_token, name="api-token"),  # POST user/pass -> token
    path("api-auth/", include("rest_framework.urls")),  # login for the browsable API
    # ── Authentication (web search UI) ────────────────────────────────────────
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/", include("django.contrib.auth.urls")),  # password change/reset
    # ── Web UI: unified search + detail pages ─────────────────────────────────
    path("", include("mdm.search.urls", namespace="search")),
]
