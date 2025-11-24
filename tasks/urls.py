from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Researcher views
    path('', views.task_list, name='task_list'),
    path('<int:pk>/preview/', views.task_preview, name='task_preview'),

    # Participant views
    path('<int:pk>/run/', views.task_run, name='task_run'),
    path('<int:pk>/complete/', views.task_complete, name='task_complete'),

    # API endpoint
    path('<int:pk>/submit/', views.task_submit, name='task_submit'),
]
