from django.urls import path

from . import views

urlpatterns = [
    path("", views.canvas, name="canvas"),
    path("api/save/", views.save_drawing, name="save_drawing"),
]
