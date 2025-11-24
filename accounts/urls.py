from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('invite/accept/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
]
