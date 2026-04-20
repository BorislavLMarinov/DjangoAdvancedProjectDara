from django.test import TestCase, Client
from django.urls import reverse
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from accounts.models import ChildProfile
from challenges.models import DifficultyLevel, BaseTask
from trainees.models import Avatar, AvatarOwnership, TaskCompletion
from trainees.services import purchase_avatar, set_active_avatar

User = get_user_model()

class TraineesTests(TestCase):
    def setUp(self):
        # Create a parent user (signal handles ParentProfile creation)
        self.parent_user = User.objects.create_user(
            username='parent', email='parent@example.com', password='password123', role='parent'
        )
        self.parent_profile = self.parent_user.parent_profile
        
        # Create a child user
        self.child_user = User.objects.create_user(
            username='child', email='child@example.com', password='password123', role='child'
        )
        # Create ChildProfile manually (needs parent), signal handles TraineeProfile
        self.child_profile = ChildProfile.objects.create(user=self.child_user, parent=self.parent_profile)
        self.trainee_profile = self.child_profile.trainee_profile
        
        # Create common dependencies
        self.difficulty = DifficultyLevel.objects.create(name='Trainee', multiplier=1.0)
        
        self.avatar = Avatar.objects.create(
            name='Cool Avatar',
            coin_cost=100,
            unlock_type=Avatar.UnlockType.PURCHASE,
            is_active=True
        )
        
        self.client = Client()

    def test_award_xp_logic(self):
        result = self.trainee_profile.award_xp(50)
        self.trainee_profile.refresh_from_db()
        
        self.assertEqual(self.trainee_profile.total_xp, 50)
        self.assertEqual(self.trainee_profile.current_xp, 50)
        self.assertEqual(self.trainee_profile.coins, 50)
        self.assertEqual(result['xp_gained'], 50)
        self.assertEqual(result['coins_gained'], 50)

    def test_level_up_logic(self):
        # LEVEL_SCALING_FACTOR = 100, BASE_XP = 100
        self.trainee_profile.award_xp(250)
        self.trainee_profile.refresh_from_db()
        
        self.assertEqual(self.trainee_profile.level, 2)
        self.assertEqual(self.trainee_profile.current_xp, 50)

    def test_purchase_avatar_success(self):
        self.trainee_profile.coins = 200
        self.trainee_profile.save()
        
        result = purchase_avatar(self.trainee_profile, self.avatar)
        
        self.assertTrue(result['success'])
        self.trainee_profile.refresh_from_db()
        self.assertEqual(self.trainee_profile.coins, 100)
        self.assertTrue(AvatarOwnership.objects.filter(trainee=self.trainee_profile, avatar=self.avatar).exists())

    def test_purchase_avatar_insufficient_coins(self):
        self.trainee_profile.coins = 50
        self.trainee_profile.save()
        
        result = purchase_avatar(self.trainee_profile, self.avatar)
        
        self.assertFalse(result['success'])
        self.assertIn('Not enough coins', result['error'])
        self.assertFalse(AvatarOwnership.objects.filter(trainee=self.trainee_profile, avatar=self.avatar).exists())

    def test_set_active_avatar_success(self):
        AvatarOwnership.objects.create(trainee=self.trainee_profile, avatar=self.avatar)
        
        result = set_active_avatar(self.trainee_profile, self.avatar)
        
        self.assertTrue(result['success'])
        self.trainee_profile.refresh_from_db()
        self.assertEqual(self.trainee_profile.active_avatar, self.avatar)

    def test_trainee_dashboard_view(self):
        self.client.login(username='child', password='password123')
        
        # Create a completion
        task = BaseTask.objects.create(title='Test Task', difficulty=self.difficulty, base_points=10)
        TaskCompletion.objects.create(
            trainee=self.trainee_profile, 
            task=task, 
            time_taken_seconds=30, 
            xp_earned=10, 
            coins_earned=10
        )
        
        response = self.client.get(reverse('trainees:trainee-dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['trainee'], self.trainee_profile)
        self.assertEqual(len(response.context['recent_completions']), 1)
        self.assertEqual(response.context['recent_completions'][0].task, task)

    def test_avatar_ownership_uniqueness(self):
        AvatarOwnership.objects.create(trainee=self.trainee_profile, avatar=self.avatar)
        
        # Trying to create the same ownership should raise IntegrityError due to unique_together
        with self.assertRaises(IntegrityError):
            AvatarOwnership.objects.create(trainee=self.trainee_profile, avatar=self.avatar)
