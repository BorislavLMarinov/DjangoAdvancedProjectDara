from django.db import models
from challenges.models import BaseTask

class Badge(models.Model):
    class BadgeType(models.TextChoices):
        COUNT = 'count', 'Count-based'
        SPEED = 'speed', 'Speed-based'
        QUEST = 'quest', 'Quest-completion'
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    badge_type = models.CharField(max_length=10, choices=BadgeType.choices)

    earners = models.ManyToManyField('trainees.TraineeProfile', related_name='badges', blank=True)
    
    reward_avatar = models.ForeignKey(
        'trainees.Avatar', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        help_text="Optional avatar unlocked when this badge is earned."
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_badge_type_display()})"

class Quest(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    
    tasks = models.ManyToManyField(BaseTask, related_name='quests')
    
    reward_xp = models.PositiveIntegerField(default=100)
    reward_badge = models.ForeignKey(
        Badge, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        limit_choices_to={'badge_type': Badge.BadgeType.QUEST}
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
