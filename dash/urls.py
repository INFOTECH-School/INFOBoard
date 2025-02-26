from django.shortcuts import redirect
from django.urls import path

from dash import views

urlpatterns = [
    path('', views.redirect_to_my, name='index'),
    path('login', views.login, name='custom_login'),
    path('boards', views.MyBoardView.as_view(), name='my'),
    path('boards/shared', views.shared_board, name='shared'),
    path('group', views.MyBoardGroup.as_view(), name='my_board_groups'),
    path('group/shared', views.SharedBoardGroup.as_view(), name='shared_board_groups'),
    path('share_board', views.share_board, name='share_board'),
    path('manage_group_boards', views.manage_group_boards, name='manage_group_boards'),
    path('manage_group_users', views.manage_group_users, name='manage_group_users'),
    path('get-group-users/<uuid:group_id>/', views.get_group_users, name='get_group_users'),
]
