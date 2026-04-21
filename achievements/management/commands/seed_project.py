import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import TeacherProfile, ParentProfile, ChildProfile
from challenges.models import DifficultyLevel, ArithmeticTask, CountingTask, PatternChallenge, MazeTask
from trainees.models import Avatar
from achievements.models import Badge, Quest

User = get_user_model()

class Command(BaseCommand):
    help = "Populates the database with sample K-POP trainee data for evaluation."

    def handle(self, *args, **options):
        self.stdout.write("🌟 Starting ProjectDara Data Seeding...")

        # 1. Create Difficulty Levels
        easy, _ = DifficultyLevel.objects.get_or_create(name="Trainee", defaults={'multiplier': 1.0, 'color_code': "#00D4FF"})
        medium, _ = DifficultyLevel.objects.get_or_create(name="Idol", defaults={'multiplier': 2.0, 'color_code': "#FFEA00"})
        hard, _ = DifficultyLevel.objects.get_or_create(name="Legend", defaults={'multiplier': 3.0, 'color_code': "#FF007A"})

        # 2. Create a Demo Architect (Teacher)
        architect_user, created = User.objects.get_or_create(
            username="demo_architect",
            defaults={'email': "architect@projectdara.com", 'role': User.Role.TEACHER, 'age': 30}
        )
        if created:
            architect_user.set_password("pass1234")
            architect_user.save()
        
        teacher_profile = architect_user.teacher_profile

        # 3. Create Sample Avatars
        avatar_gold, _ = Avatar.objects.get_or_create(
            name="Golden Maknae",
            defaults={
                'description': "A rare trainee with unlimited potential.",
                'rarity': Avatar.Rarity.EPIC,
                'unlock_type': Avatar.UnlockType.PURCHASE,
                'coin_cost': 500
            }
        )
        
        avatar_neon, _ = Avatar.objects.get_or_create(
            name="Neon Dancer",
            defaults={
                'description': "Lighting up the stage with every move.",
                'rarity': Avatar.Rarity.RARE,
                'unlock_type': Avatar.UnlockType.PURCHASE,
                'coin_cost': 200
            }
        )

        avatar_reward, _ = Avatar.objects.get_or_create(
            name="Stage King",
            defaults={
                'description': "Unlocked only by the most dedicated trainees.",
                'rarity': Avatar.Rarity.ACHIEVEMENT,
                'unlock_type': Avatar.UnlockType.ACHIEVEMENT
            }
        )

        # 4. Create Badges
        speed_badge, _ = Badge.objects.get_or_create(
            name="Speedrunner",
            defaults={'description': "Complete a mission in under 10 seconds.", 'badge_type': Badge.BadgeType.SPEED}
        )
        
        king_badge, _ = Badge.objects.get_or_create(
            name="Stage Master",
            defaults={
                'description': "Complete the Starter Quest.", 
                'badge_type': Badge.BadgeType.QUEST,
                'reward_avatar': avatar_reward
            }
        )

        # 5. Create Missions
        # Arithmetic
        math1, _ = ArithmeticTask.objects.get_or_create(
            title="Album Math",
            defaults={
                'description': "Calculate the total albums sold!",
                'difficulty': easy,
                'base_points': 10,
                'number_a': 5,
                'number_b': 3,
                'operation': '+',
                'created_by': teacher_profile
            }
        )

        # Pattern
        pat1, _ = PatternChallenge.objects.get_or_create(
            title="Dance Sequence",
            defaults={
                'description': "What's the missing move?",
                'difficulty': medium,
                'base_points': 20,
                'sequence_data': ["Slide", "Spin", "?", "Jump"],
                'correct_value': "Pose",
                'choice_1': "Walk", 'choice_2': "Sit", 'choice_3': "Run",
                'created_by': teacher_profile
            }
        )

        # Maze
        maze1, _ = MazeTask.objects.get_or_create(
            title="Backstage Navigation",
            defaults={
                'description': "Find your way to the stage!",
                'difficulty': hard,
                'base_points': 50,
                'grid': [[0,0,1],[1,0,1],[1,0,0]],
                'start_row': 0, 'start_col': 0,
                'end_row': 2, 'end_col': 2,
                'created_by': teacher_profile
            }
        )

        # 6. Create Quest
        quest, _ = Quest.objects.get_or_create(
            title="Trainee Debut",
            defaults={
                'description': "Complete your first set of training missions.",
                'reward_xp': 500,
                'reward_badge': king_badge
            }
        )
        quest.tasks.add(math1, pat1, maze1)

        self.stdout.write(self.style.SUCCESS("✅ ProjectDara successfully seeded!"))
        self.stdout.write(self.style.WARNING(f"Architect Login: demo_architect / pass1234"))
