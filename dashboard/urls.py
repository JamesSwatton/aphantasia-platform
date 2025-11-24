from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Participant dashboard
    path('', views.participant_dashboard, name='participant_dashboard'),
]
