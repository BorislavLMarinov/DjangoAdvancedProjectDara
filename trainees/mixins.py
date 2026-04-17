from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

from accounts.mixins import ChildRequiredMixin, TeacherRequiredMixin
from .models import TraineeProfile


class TraineeOwnerMixin(ChildRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not request.user.is_authenticated:
            return response

        trainee = get_object_or_404(TraineeProfile, pk=self.kwargs.get('pk'))
        if trainee.child.user != request.user:
            messages.error(request, 'You can only access your own profile.')
            return redirect('home')

        self.trainee = trainee
        return response
