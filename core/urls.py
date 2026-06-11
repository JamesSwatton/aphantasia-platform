from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('messages/', views.messages_view, name='messages'),
    path('messages/<int:message_id>/mark-read/', views.mark_read, name='mark_read'),
    path('messages/mark-all-read/', views.mark_all_read, name='mark_all_read'),
]
