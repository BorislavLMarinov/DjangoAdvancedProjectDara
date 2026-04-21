from celery import shared_task
from django.db import transaction
from trainees.models import TraineeProfile, TaskCompletion, AvatarOwnership
from challenges.models import BaseTask
from .models import Badge, Quest

@shared_task
def check_achievements_async(trainee_id, task_id, time_taken):
    try:
        trainee = TraineeProfile.objects.get(id=trainee_id)
        task = BaseTask.objects.get(id=task_id)
    except (TraineeProfile.DoesNotExist, BaseTask.DoesNotExist):
        return "Trainee or Task not found."

    _check_speed_achievements(trainee, time_taken)
    
    _check_count_achievements(trainee)
    
    _check_quest_completions(trainee, task)

    return f"Processed achievements for {trainee.child.user.username}"

def _check_speed_achievements(trainee, time_taken):
    if time_taken <= 10:
        badge, created = Badge.objects.get_or_create(
            name="Speedrunner",
            defaults={
                'description': "Complete any mission in under 10 seconds.",
                'badge_type': Badge.BadgeType.SPEED
            }
        )
        if not trainee.badges.filter(id=badge.id).exists():
            trainee.badges.add(badge)
            _award_avatar_if_any(trainee, badge)

def _check_count_achievements(trainee):
    count = TaskCompletion.objects.filter(trainee=trainee).count()
    if count >= 10:
        badge, created = Badge.objects.get_or_create(
            name="Dedication",
            defaults={
                'description': "Complete 10 missions.",
                'badge_type': Badge.BadgeType.COUNT
            }
        )
        if not trainee.badges.filter(id=badge.id).exists():
            trainee.badges.add(badge)
            _award_avatar_if_any(trainee, badge)

def _check_quest_completions(trainee, last_task):
    active_quests = Quest.objects.filter(is_active=True, tasks=last_task)
    
    for quest in active_quests:
        if quest.reward_badge and trainee.badges.filter(id=quest.reward_badge.id).exists():
            continue
            
        required_task_ids = set(quest.tasks.values_list('id', flat=True))
        completed_task_ids = set(TaskCompletion.objects.filter(
            trainee=trainee
        ).values_list('task_id', flat=True))
        
        if required_task_ids.issubset(completed_task_ids):
            with transaction.atomic():
                if quest.reward_badge:
                    trainee.badges.add(quest.reward_badge)
                    _award_avatar_if_any(trainee, quest.reward_badge)
                trainee.award_xp(quest.reward_xp)

def _award_avatar_if_any(trainee, badge):
    if badge.reward_avatar:
        AvatarOwnership.objects.get_or_create(
            trainee=trainee,
            avatar=badge.reward_avatar,
            defaults={'acquired_via': AvatarOwnership.AcquiredVia.ACHIEVEMENT}
        )
