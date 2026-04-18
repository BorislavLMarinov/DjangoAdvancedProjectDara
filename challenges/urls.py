from django.urls import path
from . import views

app_name = 'challenges'

urlpatterns = [
    # Teacher Management
    path('dashboard/', views.TeacherDashboardView.as_view(), name='teacher-dashboard'),
    path('<str:task_type>/create/', views.TaskCreateView.as_view(), name='task-create'),
    path('<str:task_type>/<int:pk>/edit/', views.TaskEditView.as_view(), name='task-edit'),
    path('<str:task_type>/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task-delete'),

    # Trainee Gameplay
    path('missions/', views.MissionListView.as_view(), name='mission-list'),
    path('play/counting/<int:pk>/', views.CountingPlayView.as_view(), name='counting_play'),
    path('play/arithmetic/<int:pk>/', views.ArithmeticPlayView.as_view(), name='arithmetic_play'),
    path('play/pattern/<int:pk>/', views.PatternPlayView.as_view(), name='pattern_play'),
    path('play/maze/<int:pk>/', views.MazePlayView.as_view(), name='maze_play'),
]
