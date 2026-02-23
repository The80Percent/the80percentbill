from django.urls import path

from . import views

app_name = "data"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/district-counts/", views.district_counts, name="district_counts"),
]
