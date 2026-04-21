from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from accounts.models import ChildProfile

LEVEL_SCALING_FACTOR = 100
BASE_XP = 100
COINS_PER_XP_POINT = 1


def xp_threshold_for_level(level: int) -> int:
    if level <= 1:
        return 0
    total = 0
    for i in range(1, level):
        total += BASE_XP + (i * LEVEL_SCALING_FACTOR)
    return total


def xp_needed_for_next_level(current_level: int) -> int:
    return BASE_XP + (current_level * LEVEL_SCALING_FACTOR)


class Avatar(models.Model):
    class Rarity(models.TextChoices):
        COMMON      = 'common',      'Common'
        RARE        = 'rare',        'Rare'
        EPIC        = 'epic',        'Epic'
        LEGENDARY   = 'legendary',   'Legendary'
        LIMITED     = 'limited',     'Limited'
        ACHIEVEMENT = 'achievement', 'Achievement'

    class UnlockType(models.TextChoices):
        PURCHASE     = 'purchase',     'Purchase with coins'
        ACHIEVEMENT  = 'achievement',  'Achievement unlock'
        LIMITED_TIME = 'limited_time', 'Limited-time unlock'

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')

    image = models.ImageField(upload_to='avatars/', blank=True, null=True)

    rarity = models.CharField(
        max_length=20,
        choices=Rarity.choices,
        default=Rarity.COMMON,
        db_index=True,
    )

    unlock_type = models.CharField(
        max_length=20,
        choices=UnlockType.choices,
        default=UnlockType.PURCHASE,
    )

    coin_cost = models.PositiveIntegerField(
        default=0,
        help_text='Cost in coins. Only relevant when unlock_type=PURCHASE.',
    )

    # TODO: If strict typing, replace with FK to BaseTask directly.
    required_task = models.ForeignKey(
        'challenges.BaseTask',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='unlocks_avatar',
        help_text='Task that must be completed to unlock. Only for ACHIEVEMENT type.',
    )

    available_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Start of availability window. Only for LIMITED_TIME type.',
    )
    available_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='End of availability window. Only for LIMITED_TIME type.',
    )

    is_active = models.BooleanField(default=True, help_text='Inactive avatars are hidden from the shop.')

    created_at = models.DateTimeField(auto_now_add=True)


    @property
    def is_currently_available(self) -> bool:
        if not self.is_active:
            return False
        if self.unlock_type == self.UnlockType.LIMITED_TIME:
            now = timezone.now()
            if self.available_from and now < self.available_from:
                return False
            if self.available_until and now > self.available_until:
                return False
        return True

    def __str__(self):
        return f"{self.name} [{self.get_rarity_display()}]"

    class Meta:
        verbose_name = 'Avatar'
        verbose_name_plural = 'Avatars'
        ordering = ['rarity', 'name']


class TraineeProfile(models.Model):
    child = models.OneToOneField(
        ChildProfile,
        on_delete=models.CASCADE,
        related_name='trainee_profile',
    )

    level = models.PositiveIntegerField(default=1)
    total_xp = models.PositiveIntegerField(default=0)
    current_xp = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)

    active_avatar = models.ForeignKey(
        Avatar,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text='The avatar currently displayed for this child.',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    @property
    def xp_for_next_level(self) -> int:
        return xp_needed_for_next_level(self.level)

    @property
    def xp_progress_percent(self) -> float:
        needed = self.xp_for_next_level
        if needed == 0:
            return 100.0
        return round((self.current_xp / needed) * 100, 1)

    def award_xp(self, amount: int) -> dict:
        if amount <= 0:
            return {'xp_gained': 0, 'coins_gained': 0, 'levels_gained': 0}

        self.total_xp += amount
        self.current_xp += amount
        coins_gained = amount * COINS_PER_XP_POINT
        self.coins += coins_gained

        levels_gained = 0
        while self.current_xp >= self.xp_for_next_level:
            self.current_xp -= self.xp_for_next_level
            self.level += 1
            levels_gained += 1

        self.save()
        return {
            'xp_gained': amount,
            'coins_gained': coins_gained,
            'levels_gained': levels_gained,
            'new_level': self.level,
        }


    def spend_coins(self, amount: int) -> bool:
        if amount <= 0 or self.coins < amount:
            return False
        self.coins -= amount
        self.save()
        return True


    def __str__(self):
        return f"{self.child.user.username} — Level {self.level} ({self.total_xp} XP)"

    class Meta:
        verbose_name = 'Trainee Profile'
        verbose_name_plural = 'Trainee Profiles'


class AvatarOwnership(models.Model):
    class AcquiredVia(models.TextChoices):
        PURCHASE     = 'purchase',     'Purchased with coins'
        ACHIEVEMENT  = 'achievement',  'Achievement reward'
        LIMITED_TIME = 'limited_time', 'Limited-time event'
        ADMIN_GRANT  = 'admin_grant',  'Granted by admin'

    trainee = models.ForeignKey(
        TraineeProfile,
        on_delete=models.CASCADE,
        related_name='owned_avatars',
    )

    avatar = models.ForeignKey(
        Avatar,
        on_delete=models.CASCADE,
        related_name='owners',
    )

    acquired_via = models.CharField(
        max_length=20,
        choices=AcquiredVia.choices,
        default=AcquiredVia.PURCHASE,
    )

    acquired_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trainee', 'avatar')
        verbose_name = 'Avatar Ownership'
        verbose_name_plural = 'Avatar Ownerships'
        ordering = ['-acquired_at']

    def __str__(self):
        return f"{self.trainee.child.user.username} owns {self.avatar.name}"


class TaskCompletion(models.Model):
    # TODO: Add a `score` field (e.g. 0-100 %) once task scoring is designed
    #       in the challenges app.
    # TODO: Consider a `attempts` counter if we want to track retries.

    trainee = models.ForeignKey(
        TraineeProfile,
        on_delete=models.CASCADE,
        related_name='task_completions',
    )

    task = models.ForeignKey(
        'challenges.BaseTask',
        on_delete=models.SET_NULL,
        null=True,
        related_name='completions',
    )

    completed_at = models.DateTimeField(auto_now_add=True)

    time_taken_seconds = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text='How long (in seconds) the child took to complete the task.',
    )

    difficulty_snapshot = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Difficulty level of the task at the time of completion.',
    )

    xp_earned = models.PositiveIntegerField(default=0)
    coins_earned = models.PositiveIntegerField(default=0)

    avatar_unlocked = models.ForeignKey(
        Avatar,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='unlocked_by_completions',
        help_text='Avatar unlocked as a result of this completion, if any.',
    )

    class Meta:
        verbose_name = 'Task Completion'
        verbose_name_plural = 'Task Completions'
        ordering = ['-completed_at']

    def __str__(self):
        task_name = self.task.title if self.task else '(deleted task)'
        return f"{self.trainee.child.user.username} completed {task_name} — {self.xp_earned} XP"
