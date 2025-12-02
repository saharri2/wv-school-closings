from django.contrib import admin
from django.urls import path
from closings import views

urlpatterns = [
    path('school-closings-admin-page-120225/', admin.site.urls),
    path('', views.map_view, name='map'),
]