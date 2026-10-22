"""
The main URLs of the project.

    /admin/        -> the Django administration (login: admin / admin)
    /              -> the application "students" (list, form, CSV export)
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("students.urls")),
]
