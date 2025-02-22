from django.shortcuts import redirect
from django.urls import path

from dash import views

urlpatterns = [
    path('', views.redirect_to_my, name='index'),
    path('login', views.login, name='custom_login'),
    path('my', views.MyBoardView.as_view(), name='my'),
]
