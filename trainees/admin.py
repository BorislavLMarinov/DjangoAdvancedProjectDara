from django.contrib import admin
from .models import Avatar, TraineeProfile, AvatarOwnership, TaskCompletion


@admin.register(Avatar)
class AvatarAdmin(admin.ModelAdmin):
    list_display = ('name', 'rarity', 'unlock_type', 'coin_cost', 'is_active', 'created_at')
    list_filter = ('rarity', 'unlock_type', 'is_active')
    search_fields = ('name', 'description')


@admin.register(TraineeProfile)
class TraineeProfileAdmin(admin.ModelAdmin):
    list_display = ('child', 'level', 'total_xp', 'coins', 'active_avatar', 'created_at')
    list_filter = ('level',)
    search_fields = ('child__user__username', 'child__user__email')


@admin.register(AvatarOwnership)
class AvatarOwnershipAdmin(admin.ModelAdmin):
    list_display = ('trainee', 'avatar', 'acquired_via', 'acquired_at')
    list_filter = ('acquired_via',)
    search_fields = ('trainee__child__user__username', 'avatar__name')


@admin.register(TaskCompletion)
class TaskCompletionAdmin(admin.ModelAdmin):
    list_display = ('trainee', 'task', 'xp_earned', 'coins_earned', 'completed_at')
    list_filter = ('completed_at', 'difficulty_snapshot')
    search_fields = ('trainee__child__user__username', 'task__title')
