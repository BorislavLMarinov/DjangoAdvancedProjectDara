from rest_framework import serializers
from trainees.models import TraineeProfile
from challenges.models import DifficultyLevel, BaseTask
from achievements.models import Badge, Quest

class TraineeStatsSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='child.user.username', read_only=True)
    class Meta:
        model = TraineeProfile
        fields = ['username', 'level', 'total_xp', 'current_xp', 'coins']

class DifficultySerializer(serializers.ModelSerializer):
    class Meta:
        model = DifficultyLevel
        fields = ['name', 'multiplier']

class ChallengeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    base_points = serializers.IntegerField()
    total_points = serializers.IntegerField(source='calculate_total_points')
    difficulty = DifficultySerializer()
    task_type = serializers.CharField(source='_meta.verbose_name')

class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['name', 'description', 'badge_type', 'created_at']

class QuestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quest
        fields = ['title', 'description', 'reward_xp', 'is_active']

