from django.urls import path
from . import views

app_name = 'surveys'

urlpatterns = [
    # List all surveys
    path('', views.survey_list, name='survey_list'),

    # Preview survey (for researchers)
    path('<int:pk>/preview/', views.survey_preview, name='survey_preview'),

    # Take survey (for participants)
    path('<int:pk>/take/', views.survey_take, name='survey_take'),
]
