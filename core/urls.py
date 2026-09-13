from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my-dogs/', views.my_dogs, name='my_dogs'),
    path('add-dog/', views.add_dog, name='add_dog'),
    path('dog/<int:dog_id>/', views.dog_detail, name='dog_detail'),
    path('dog/<int:dog_id>/edit/', views.edit_dog, name='edit_dog'),
    path('dog/<int:dog_id>/delete/', views.delete_dog, name='delete_dog'),
    path('profile/', views.profile_view, name='profile'),
    path('explore/', views.explore_dogs, name='explore_dogs'),
    path('dog/<int:dog_id>/like/', views.send_match_request, name='send_match_request'),
    path('requests/', views.match_requests_dashboard, name='match_requests_dashboard'),
    path('requests/<int:request_id>/<str:action>/', views.respond_match_request, name='respond_match_request'),
    path('chats/', views.chats_inbox, name='chats_inbox'),
    path('chat/<int:match_id>/', views.chat_room, name='chat_room'),
    path('chat/<int:match_id>/send/', views.send_message_api, name='send_message_api'),
    path('chat/<int:match_id>/get/', views.get_messages_api, name='get_messages_api'),
    path('chat/message/<int:message_id>/edit/', views.edit_message_api, name='edit_message_api'),
    path('chat/message/<int:message_id>/delete/', views.delete_message_api, name='delete_message_api'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/dog/<int:dog_id>/<str:action>/', views.admin_approve_reject_dog, name='admin_approve_reject_dog'),
    path('vets/', views.vets_directory, name='vets_directory'),
]