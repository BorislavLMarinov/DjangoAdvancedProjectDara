from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.mixins import ChildRequiredMixin
from .models import Avatar, TraineeProfile, AvatarOwnership, TaskCompletion


class TraineeDashboardView(ChildRequiredMixin, TemplateView):
    template_name = 'trainees/trainee_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trainee = get_object_or_404(TraineeProfile, child__user=self.request.user)
        context['trainee'] = trainee
        context['recent_completions'] = TaskCompletion.objects.filter(trainee=trainee).order_by('-completed_at')[:5]
        return context


class AvatarShopView(ChildRequiredMixin, ListView):
    model = Avatar
    template_name = 'trainees/avatar_shop.html'
    context_object_name = 'avatars'

    def get_queryset(self):
        return Avatar.objects.filter(
            is_active=True, 
            unlock_type=Avatar.UnlockType.PURCHASE
        ).order_by('rarity', 'coin_cost')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trainee = self.request.user.child_profile.trainee_profile
        context['trainee_coins'] = trainee.coins
        context['owned_avatar_ids'] = AvatarOwnership.objects.filter(
            trainee=trainee
        ).values_list('avatar_id', flat=True)
        return context


class AvatarPurchaseView(ChildRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        avatar = get_object_or_404(Avatar, pk=pk, is_active=True, unlock_type=Avatar.UnlockType.PURCHASE)
        trainee = request.user.child_profile.trainee_profile

        if AvatarOwnership.objects.filter(trainee=trainee, avatar=avatar).exists():
            messages.warning(request, f"You already own {avatar.name}!")
            return redirect('trainees:avatar-shop')

        if trainee.spend_coins(avatar.coin_cost):
            AvatarOwnership.objects.create(
                trainee=trainee,
                avatar=avatar,
                acquired_via=AvatarOwnership.AcquiredVia.PURCHASE
            )
            messages.success(request, f"Congratulations! You've unlocked {avatar.name}!")
        else:
            messages.error(request, "Not enough coins! Keep training to earn more.")

        return redirect('trainees:avatar-shop')


class InventoryListView(ChildRequiredMixin, ListView):
    model = AvatarOwnership
    template_name = 'trainees/inventory.html'
    context_object_name = 'ownerships'

    def get_queryset(self):
        trainee = self.request.user.child_profile.trainee_profile
        return AvatarOwnership.objects.filter(trainee=trainee).select_related('avatar')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_avatar'] = self.request.user.child_profile.trainee_profile.active_avatar
        return context


class EquipAvatarView(ChildRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        trainee = request.user.child_profile.trainee_profile
        ownership = get_object_or_404(AvatarOwnership, trainee=trainee, avatar_id=pk)
        
        trainee.active_avatar = ownership.avatar
        trainee.save()
        
        messages.success(request, f"{ownership.avatar.name} equipped!")
        return redirect('trainees:inventory')
