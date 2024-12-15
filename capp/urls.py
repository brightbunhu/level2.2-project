from django.urls import path
from . import views

urlpatterns = [
    path('', views.rooms, name='rooms'),
    path('<int:room_id>/', views.room, name='room'),
    path('search/', views.search, name='search'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('developers/', views.developers, name='developers'),
    path('create-room/', views.create_room, name='create_room'),
    path('join-room/', views.join_room, name='join_room'),
    path('feedback/', views.feedback, name='feedback'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-feedback/', views.admin_feedback, name='admin_feedback'),
    path('translation-metrics/', views.translation_metrics, name='translation_metrics'),
]
