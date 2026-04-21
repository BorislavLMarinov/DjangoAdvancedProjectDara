from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import ParentProfile, ChildProfile, TeacherProfile
from trainees.models import TraineeProfile
from challenges.models import ArithmeticTask, CountingTask, DifficultyLevel
import json

User = get_user_model()

class APITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.difficulty = DifficultyLevel.objects.create(name="Idol", multiplier=1.5)
        
        # Create users
        self.teacher_user = User.objects.create_user(
            username="teacher", 
            role=User.Role.TEACHER, 
            password="password", 
            email="t@t.com"
        )
        # TeacherProfile created by signal
        self.teacher_profile = self.teacher_user.teacher_profile
        
        self.parent_user = User.objects.create_user(
            username="parent", 
            role=User.Role.PARENT, 
            password="password", 
            email="p@p.com"
        )
        # ParentProfile created by signal
        self.parent_profile = self.parent_user.parent_profile
        
        self.child_user = User.objects.create_user(
            username="child", 
            role=User.Role.CHILD, 
            password="password", 
            email="c@c.com"
        )
        self.child_profile = ChildProfile.objects.create(
            user=self.child_user, 
            parent=self.parent_profile
        )
        
        # TraineeProfile created by signal
        self.trainee = self.child_profile.trainee_profile
        self.trainee.award_xp(200) # Give some stats

    def test_challenge_list_returns_missions(self):
        """1. ChallengeListAPIView (ensure it returns a list of missions)."""
        CountingTask.objects.create(
            title="Count the Albums",
            description="How many albums are there?",
            difficulty=self.difficulty,
            base_points=10,
            correct_answer=5
        )
        
        self.client.login(username="child", password="password")
        response = self.client.get(reverse('api:challenge-list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 1)
        self.assertEqual(data[0]['title'], "Count the Albums")

    def test_trainee_stats_authenticated(self):
        """2. TraineeStatsAPIView (ensure it returns correct stats for the logged-in trainee)."""
        self.client.login(username="child", password="password")
        response = self.client.get(reverse('api:trainee-stats'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['username'], "child")
        self.assertEqual(data['total_xp'], 200)
        self.assertEqual(data['coins'], 200)

    def test_role_based_permission(self):
        """3. Role-based permission (Parent/Teacher should get 403 on stats endpoint)."""
        # Teacher
        self.client.login(username="teacher", password="password")
        response = self.client.get(reverse('api:trainee-stats'))
        self.assertEqual(response.status_code, 403)
        
        # Parent
        self.client.login(username="parent", password="password")
        response = self.client.get(reverse('api:trainee-stats'))
        self.assertEqual(response.status_code, 403)

    def test_serialization_check(self):
        """4. Serialization check (ensure mission points and difficulty are present in JSON)."""
        ArithmeticTask.objects.create(
            title="K-Pop Math",
            description="Add the Lightsticks",
            difficulty=self.difficulty,
            base_points=20,
            number_a=10,
            number_b=5,
            operation='+'
        )
        
        self.client.login(username="child", password="password")
        response = self.client.get(reverse('api:challenge-list'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find the task
        task_data = next(t for t in data if t['title'] == "K-Pop Math")
        self.assertIn('total_points', task_data)
        self.assertIn('difficulty', task_data)
        self.assertEqual(task_data['difficulty']['name'], "Idol")
        # 20 * 1.5 = 30
        self.assertEqual(task_data['total_points'], 30)
