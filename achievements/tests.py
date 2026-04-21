from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.models import ParentProfile, ChildProfile
from trainees.models import TraineeProfile, Avatar, AvatarOwnership, TaskCompletion
from challenges.models import BaseTask, DifficultyLevel
from achievements.models import Badge, Quest
from achievements.tasks import check_achievements_async

User = get_user_model()

class AchievementsTests(TestCase):
    def setUp(self):
        # Setup basic data
        self.difficulty = DifficultyLevel.objects.create(name="Normal", multiplier=1.0)
        
        self.parent_user = User.objects.create_user(
            username="parent", 
            email="p@test.com", 
            password="password", 
            role=User.Role.PARENT
        )
        # ParentProfile created by signal
        self.parent_profile = self.parent_user.parent_profile
        
        self.child_user = User.objects.create_user(
            username="child", 
            email="c@test.com", 
            password="password", 
            role=User.Role.CHILD
        )
        self.child_profile = ChildProfile.objects.create(user=self.child_user, parent=self.parent_profile)
        # TraineeProfile created by signal
        self.trainee = self.child_profile.trainee_profile

        self.task = BaseTask.objects.create(
            title="Test Task",
            description="Test Description",
            difficulty=self.difficulty,
            base_points=10
        )

    def test_speedrunner_badge_awarded(self):
        """1. Speed-based badge awarding (Speedrunner)."""
        # Call the task with time <= 10
        check_achievements_async(self.trainee.id, self.task.id, 5)
        
        self.assertTrue(self.trainee.badges.filter(name="Speedrunner").exists())
        badge = self.trainee.badges.get(name="Speedrunner")
        self.assertEqual(badge.badge_type, Badge.BadgeType.SPEED)

    def test_dedication_badge_awarded(self):
        """2. Count-based badge awarding (Dedication)."""
        # Create 10 completions
        for i in range(10):
            TaskCompletion.objects.create(
                trainee=self.trainee,
                task=self.task,
                time_taken_seconds=20,
                xp_earned=10
            )
        
        check_achievements_async(self.trainee.id, self.task.id, 20)
        
        self.assertTrue(self.trainee.badges.filter(name="Dedication").exists())
        badge = self.trainee.badges.get(name="Dedication")
        self.assertEqual(badge.badge_type, Badge.BadgeType.COUNT)

    def test_quest_completion_logic(self):
        """3. Quest completion logic (verify bonus XP and badges are awarded when all tasks are done)."""
        task2 = BaseTask.objects.create(
            title="Test Task 2",
            description="Test Description 2",
            difficulty=self.difficulty,
            base_points=10
        )
        
        quest_badge = Badge.objects.create(
            name="Quest Master",
            description="Complete the test quest.",
            badge_type=Badge.BadgeType.QUEST
        )
        
        quest = Quest.objects.create(
            title="Starter Quest",
            description="Complete two tasks.",
            reward_xp=500,
            reward_badge=quest_badge
        )
        quest.tasks.add(self.task, task2)
        
        # Complete first task
        TaskCompletion.objects.create(
            trainee=self.trainee,
            task=self.task,
            time_taken_seconds=15,
            xp_earned=10
        )
        check_achievements_async(self.trainee.id, self.task.id, 15)
        
        # Should not have quest badge yet
        self.assertFalse(self.trainee.badges.filter(name="Quest Master").exists())
        
        initial_xp = self.trainee.total_xp
        
        # Complete second task
        TaskCompletion.objects.create(
            trainee=self.trainee,
            task=task2,
            time_taken_seconds=15,
            xp_earned=10
        )
        check_achievements_async(self.trainee.id, task2.id, 15)
        
        # Should now have quest badge and bonus XP
        self.assertTrue(self.trainee.badges.filter(name="Quest Master").exists())
        self.trainee.refresh_from_db()
        self.assertEqual(self.trainee.total_xp, initial_xp + 500)

    def test_badge_to_avatar_reward_link(self):
        """4. Badge to Avatar reward link (ensure avatar ownership is granted)."""
        reward_avatar = Avatar.objects.create(
            name="Golden Idol",
            unlock_type=Avatar.UnlockType.ACHIEVEMENT
        )
        
        badge = Badge.objects.create(
            name="Avatar Giver",
            description="Gives an avatar.",
            badge_type=Badge.BadgeType.COUNT,
            reward_avatar=reward_avatar
        )
        
        self.trainee.badges.add(badge)
        from achievements.tasks import _award_avatar_if_any
        _award_avatar_if_any(self.trainee, badge)
        
        self.assertTrue(AvatarOwnership.objects.filter(
            trainee=self.trainee, 
            avatar=reward_avatar,
            acquired_via=AvatarOwnership.AcquiredVia.ACHIEVEMENT
        ).exists())

    def test_async_task_call_verification(self):
        """5. Asynchronous task call verification (ensure check_achievements_async does its job when called)."""
        result = check_achievements_async(self.trainee.id, self.task.id, 5)
        self.assertEqual(result, f"Processed achievements for {self.child_user.username}")
        self.assertTrue(self.trainee.badges.filter(name="Speedrunner").exists())
