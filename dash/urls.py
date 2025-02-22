from django.urls import path

from dash import views

urlpatterns = [
    path('my', views.my_tables, name='my'),
    path('login', views.login, name='custom_login'),
    path('new_table', views.new_table, name='new_table'),
]
