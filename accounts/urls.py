from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('invite/accept/<uuid:token>/', views.accept_invitation, name='accept_invitation'),
    path('account/', views.account, name='account'),
    path('account/feedback/submit/', views.feedback_submit, name='feedback_submit'),
    path('account/withdraw/', views.exit_survey, name='exit_survey'),
    path('account/withdraw/submit/', views.exit_survey_submit, name='exit_survey_submit'),
    path('account/withdraw/complete/', views.withdrawal_complete, name='withdrawal_complete'),
]
