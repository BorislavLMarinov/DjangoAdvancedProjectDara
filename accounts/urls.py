from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutConfirmView.as_view(), name='logout'),
    path('teacher/<int:pk>/', views.TeacherProfileView.as_view(), name='teacher-profile'),
    path('teacher/<int:pk>/edit/', views.TeacherProfileEditView.as_view(), name='teacher-profile-edit'),
    path('teacher/<int:pk>/delete/', views.TeacherProfileDeleteView.as_view(), name='teacher-profile-delete'),
    path('parent/<int:pk>/', views.ParentProfileView.as_view(), name='parent-profile'),
    path('parent/<int:pk>/edit/', views.ParentProfileEditView.as_view(), name='parent-profile-edit'),
    path('parent/<int:pk>/delete/', views.ParentProfileDeleteView.as_view(), name='parent-profile-delete'),
    path('parent/children/', views.ParentChildListView.as_view(), name='parent-child-list'),
    path('parent/children/add/', views.ParentChildCreateView.as_view(), name='parent-child-create'),
    path('parent/children/<int:pk>/edit/', views.ParentChildEditView.as_view(), name='parent-child-edit'),
    path('parent/children/<int:pk>/delete/', views.ParentChildDeleteView.as_view(), name='parent-child-delete'),
    path('child/<int:pk>/', views.ChildProfileView.as_view(), name='child-profile'),
    path('child/<int:pk>/edit/', views.ChildProfileEditView.as_view(), name='child-profile-edit'),
    path('child/<int:pk>/delete/', views.ChildProfileDeleteView.as_view(), name='child-profile-delete'),
    path('users/', views.UserListView.as_view(), name='user-list'),
]