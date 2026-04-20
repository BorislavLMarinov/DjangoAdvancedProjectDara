from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('challenges/', views.ChallengeListAPIView.as_view(), name='challenge-list'),
    path('stats/', views.TraineeStatsAPIView.as_view(), name='trainee-stats'),
]
