from django.db import transaction

from .models import TraineeProfile, Avatar, AvatarOwnership, TaskCompletion


@transaction.atomic
def complete_task(trainee: TraineeProfile, task, time_taken_seconds: int) -> dict:
    if time_taken_seconds <= 0:
        return {'success': False, 'error': 'Invalid time value.'}

    xp = task.calculate_total_points()
    coins = xp

    completion = TaskCompletion.objects.create(
        trainee=trainee,
        task=task,
        time_taken_seconds=time_taken_seconds,
        difficulty_snapshot=task.difficulty.name,
        xp_earned=xp,
        coins_earned=coins,
    )

    level_result = trainee.award_xp(xp)

    from achievements.tasks import check_achievements_async
    check_achievements_async.delay(trainee.id, task.id, time_taken_seconds)

    avatar_unlocked = _check_achievement_unlock(trainee, task, completion)

    return {
        'success': True,
        'error': None,
        'xp_earned': xp,
        'coins_earned': coins,
        'levels_gained': level_result['levels_gained'],
        'new_level': level_result['new_level'],
        'avatar_unlocked': avatar_unlocked,
        'completion': completion,
    }


def _check_achievement_unlock(trainee: TraineeProfile, task, completion: TaskCompletion):
    try:
        avatar = Avatar.objects.get(
            unlock_type=Avatar.UnlockType.ACHIEVEMENT,
            required_task=task,
            is_active=True,
        )
    except Avatar.DoesNotExist:
        return None
    except Avatar.MultipleObjectsReturned:
        avatar = Avatar.objects.filter(
            unlock_type=Avatar.UnlockType.ACHIEVEMENT,
            required_task=task,
            is_active=True,
        ).first()

    already_owned = AvatarOwnership.objects.filter(trainee=trainee, avatar=avatar).exists()
    if already_owned:
        return None

    ownership = AvatarOwnership.objects.create(
        trainee=trainee,
        avatar=avatar,
        acquired_via=AvatarOwnership.AcquiredVia.ACHIEVEMENT,
    )
    completion.avatar_unlocked = avatar
    completion.save(update_fields=['avatar_unlocked'])
    return avatar


@transaction.atomic
def purchase_avatar(trainee: TraineeProfile, avatar: Avatar) -> dict:
    if avatar.unlock_type != Avatar.UnlockType.PURCHASE:
        return {
            'success': False,
            'error': 'This avatar cannot be purchased with coins.',
            'ownership': None,
            'coins_remaining': trainee.coins,
        }

    if not avatar.is_currently_available:
        return {
            'success': False,
            'error': 'This avatar is not currently available.',
            'ownership': None,
            'coins_remaining': trainee.coins,
        }

    already_owned = AvatarOwnership.objects.filter(trainee=trainee, avatar=avatar).exists()
    if already_owned:
        return {
            'success': False,
            'error': 'You already own this avatar.',
            'ownership': None,
            'coins_remaining': trainee.coins,
        }

    if not trainee.spend_coins(avatar.coin_cost):
        return {
            'success': False,
            'error': f'Not enough coins. You need {avatar.coin_cost} but have {trainee.coins}.',
            'ownership': None,
            'coins_remaining': trainee.coins,
        }

    ownership = AvatarOwnership.objects.create(
        trainee=trainee,
        avatar=avatar,
        acquired_via=AvatarOwnership.AcquiredVia.PURCHASE,
    )

    return {
        'success': True,
        'error': None,
        'ownership': ownership,
        'coins_remaining': trainee.coins,
    }


@transaction.atomic
def set_active_avatar(trainee: TraineeProfile, avatar: Avatar) -> dict:
    owned = AvatarOwnership.objects.filter(trainee=trainee, avatar=avatar).exists()
    if not owned:
        return {'success': False, 'error': 'You do not own this avatar.'}

    trainee.active_avatar = avatar
    trainee.save(update_fields=['active_avatar'])
    return {'success': True, 'error': None}


@transaction.atomic
def remove_active_avatar(trainee: TraineeProfile) -> dict:
    trainee.active_avatar = None
    trainee.save(update_fields=['active_avatar'])
    return {'success': True, 'error': None}



@transaction.atomic
def claim_limited_avatar(trainee: TraineeProfile, avatar: Avatar) -> dict:
    if avatar.unlock_type != Avatar.UnlockType.LIMITED_TIME:
        return {'success': False, 'error': 'This avatar is not a limited-time avatar.'}

    if not avatar.is_currently_available:
        return {
            'success': False,
            'error': 'This limited-time avatar is no longer available.',
        }

    already_owned = AvatarOwnership.objects.filter(trainee=trainee, avatar=avatar).exists()
    if already_owned:
        return {'success': False, 'error': 'You already own this avatar.'}

    ownership = AvatarOwnership.objects.create(
        trainee=trainee,
        avatar=avatar,
        acquired_via=AvatarOwnership.AcquiredVia.LIMITED_TIME,
    )
    return {'success': True, 'error': None, 'ownership': ownership}
