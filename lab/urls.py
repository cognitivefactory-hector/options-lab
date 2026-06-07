from django.urls import path

from . import views

urlpatterns = [
    path("", views.builder, name="builder"),
    path("vol", views.vol, name="vol"),
    path("backtest", views.backtest, name="backtest"),
    path("healthz", views.healthz, name="healthz"),
]
