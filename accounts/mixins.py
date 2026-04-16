from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):


    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_teacher


    def handle_no_permission(self):
        messages.error(self.request, 'This area is for teachers only.')
        return redirect('home')


class ParentRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):


    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_parent


    def handle_no_permission(self):
        messages.error(self.request, 'This area is for parents only.')
        return redirect('home')


class ChildRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):


    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_child


    def handle_no_permission(self):
        messages.error(self.request, 'This area is for children only.')
        return redirect('home')


class OwnerRequiredMixin(LoginRequiredMixin):
    # TODO: Extend to allow admin/staff bypass when admin tools are built.
    owner_field = 'pk'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        obj_pk = self.kwargs.get(self.owner_field)
        if obj_pk and request.user.pk != int(obj_pk):
            messages.error(request, 'You can only edit your own profile.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)