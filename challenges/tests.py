from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages
from accounts.models import AppUser, ChildProfile
from challenges.models import DifficultyLevel, BaseTask, ArithmeticTask

class ChallengesTests(TestCase):
    def setUp(self):
        # 1. Create DifficultyLevel
        self.difficulty = DifficultyLevel.objects.create(name="Trainee", multiplier=1.5)
        
        # 2. Create Users and Profiles
        # Teacher - Profile created via signal
        self.teacher_user = AppUser.objects.create_user(
            username='teacher_user', 
            email='teacher@example.com', 
            password='password123', 
            role=AppUser.Role.TEACHER
        )
        self.teacher_profile = self.teacher_user.teacher_profile
        
        # Parent - Profile created via signal
        self.parent_user = AppUser.objects.create_user(
            username='parent_user', 
            email='parent@example.com', 
            password='password123', 
            role=AppUser.Role.PARENT
        )
        self.parent_profile = self.parent_user.parent_profile
        
        # Child - ChildProfile not created by signal, but TraineeProfile is
        self.child_user = AppUser.objects.create_user(
            username='child_user', 
            email='child@example.com', 
            password='password123', 
            role=AppUser.Role.CHILD
        )
        self.child_profile = ChildProfile.objects.create(user=self.child_user, parent=self.parent_profile)
        self.trainee_profile = self.child_profile.trainee_profile
        
        # 3. Create an ArithmeticTask for testing play logic
        self.arithmetic_task = ArithmeticTask.objects.create(
            title="Math Mission",
            description="Add numbers",
            difficulty=self.difficulty,
            base_points=10,
            number_a=5,
            number_b=3,
            operation='+',
            created_by=self.teacher_profile
        )

    # 1. DifficultyLevel multiplier point calculation (ArithmeticTask)
    def test_arithmetic_task_point_calculation(self):
        expected_points = int(10 * 1.5)
        self.assertEqual(self.arithmetic_task.calculate_total_points(), expected_points)

    # 2. BaseTask point calculation logic
    def test_base_task_point_calculation(self):
        base_task = BaseTask.objects.create(
            title="Base Mission",
            description="Basic",
            difficulty=self.difficulty,
            base_points=20
        )
        expected_points = int(20 * 1.5)
        self.assertEqual(base_task.calculate_total_points(), expected_points)

    # 3. ArithmeticTask logic: Ensure correct_answer is saved and unique decoys are generated
    def test_arithmetic_task_logic(self):
        task = ArithmeticTask.objects.create(
            title="Math Logic",
            description="Subtraction test",
            difficulty=self.difficulty,
            base_points=10,
            number_a=10,
            number_b=4,
            operation='-',
        )
        # 10 - 4 = 6
        self.assertEqual(task.correct_answer, 6)
        
        # Check decoys are generated and are unique
        choices = [task.choice_1, task.choice_2, task.choice_3]
        # Decoys should be unique from each other
        self.assertEqual(len(set(choices)), 3)
        # Decoys should not be the correct answer
        self.assertNotIn(str(task.correct_answer), choices)
        # Decoys should be strings
        for choice in choices:
            self.assertIsInstance(choice, str)

    # 4. MissionListView access (all roles should be able to access the Mission Board now)
    def test_mission_list_view_access(self):
        url = reverse('challenges:mission-list')
        users = [self.teacher_user, self.parent_user, self.child_user]
        
        for user in users:
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Role {user.role} should be able to access mission list.")

    # 5. TaskPlayView (Child role): Reward awarding after correct answer
    def test_task_play_child_reward(self):
        self.client.force_login(self.child_user)
        url = reverse('challenges:arithmetic_play', kwargs={'pk': self.arithmetic_task.pk})
        
        initial_xp = self.trainee_profile.total_xp
        
        # correct_answer for 5+3 is 8
        response = self.client.post(url, {'answer': '8'})
        
        self.trainee_profile.refresh_from_db()
        self.assertGreater(self.trainee_profile.total_xp, initial_xp)
        self.assertRedirects(response, reverse('trainees:trainee-dashboard'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Mission Clear" in str(m) for m in messages))

    # 6. TaskPlayView (Teacher role): No rewards awarded after correct answer (testing mode)
    def test_task_play_teacher_no_reward(self):
        self.client.force_login(self.teacher_user)
        url = reverse('challenges:arithmetic_play', kwargs={'pk': self.arithmetic_task.pk})
        
        response = self.client.post(url, {'answer': '8'})
        
        self.assertRedirects(response, reverse('challenges:mission-list'))
        
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Testing mode" in str(m) for m in messages))

    # 7. TaskPlayView (Wrong answer): No rewards awarded to anyone
    def test_task_play_wrong_answer_no_reward(self):
        self.client.force_login(self.child_user)
        url = reverse('challenges:arithmetic_play', kwargs={'pk': self.arithmetic_task.pk})
        
        initial_xp = self.trainee_profile.total_xp
        # 5+3 != 9
        response = self.client.post(url, {'answer': '9'})
        
        self.trainee_profile.refresh_from_db()
        self.assertEqual(self.trainee_profile.total_xp, initial_xp)
        
        # Status should be 200 as it renders the same page with error message
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Not quite" in str(m) for m in messages))
