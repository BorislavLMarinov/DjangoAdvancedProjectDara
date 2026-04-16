from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, UpdateView, DeleteView, DetailView, TemplateView, ListView, FormView,
)

from .forms import (
    RegisterForm,
    LoginForm,
    TeacherProfileEditForm,
    ParentProfileEditForm,
    ChildProfileEditForm,
    ChildCreateForm,
    ChildEditByParentForm,
    DeleteConfirmForm,
)
from .mixins import TeacherRequiredMixin, ParentRequiredMixin, ChildRequiredMixin, OwnerRequiredMixin
from .models import AppUser, TeacherProfile, ParentProfile, ChildProfile


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('home')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Welcome, {user.username}! Your account has been created.')
        return redirect(user.get_dashboard_url())


class LoginView(DjangoLoginView):
    # TODO: Add "remember me" checkbox (SESSION_COOKIE_AGE) when needed.
    form_class = LoginForm
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return self.request.user.get_dashboard_url()

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)


class LogoutConfirmView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/logout_confirm.html'

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('home')


class TeacherProfileView(LoginRequiredMixin, DetailView):
    # TODO: Show list of created challenges/tasks here once that app is built.
    model = TeacherProfile
    template_name = 'accounts/teacher_profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        user = get_object_or_404(AppUser, pk=self.kwargs['pk'])
        return get_object_or_404(TeacherProfile, user=user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_owner'] = self.request.user == self.object.user
        return ctx


class TeacherProfileEditView(TeacherRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = TeacherProfile
    form_class = TeacherProfileEditForm
    template_name = 'accounts/profile_edit.html'

    def get_object(self, queryset=None):
        user = get_object_or_404(AppUser, pk=self.kwargs['pk'])
        return get_object_or_404(TeacherProfile, user=user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your profile has been updated.')
        return redirect('accounts:teacher-profile', pk=self.request.user.pk)

    def get_success_url(self):
        return reverse_lazy('accounts:teacher-profile', kwargs={'pk': self.request.user.pk})


class TeacherProfileDeleteView(TeacherRequiredMixin, OwnerRequiredMixin, FormView):
    form_class = DeleteConfirmForm
    template_name = 'accounts/profile_delete.html'

    def get_object(self):
        return get_object_or_404(AppUser, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['target_user'] = self.get_object()
        return ctx

    def form_valid(self, form):
        user = self.get_object()
        logout(self.request)
        user.delete()
        messages.success(self.request, 'Your account has been permanently deleted.')
        return redirect('home')


class ParentProfileView(LoginRequiredMixin, DetailView):
    # TODO: Display aggregated children progress statistics when the achievements app is complete.
    model = ParentProfile
    template_name = 'accounts/parent_profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        user = get_object_or_404(AppUser, pk=self.kwargs['pk'])
        return get_object_or_404(ParentProfile, user=user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_owner'] = self.request.user == self.object.user
        ctx['children'] = self.object.children
        return ctx


class ParentProfileEditView(ParentRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = ParentProfile
    form_class = ParentProfileEditForm
    template_name = 'accounts/profile_edit.html'

    def get_object(self, queryset=None):
        user = get_object_or_404(AppUser, pk=self.kwargs['pk'])
        return get_object_or_404(ParentProfile, user=user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your profile has been updated.')
        return redirect('accounts:parent-profile', pk=self.request.user.pk)

    def get_success_url(self):
        return reverse_lazy('accounts:parent-profile', kwargs={'pk': self.request.user.pk})


class ParentProfileDeleteView(ParentRequiredMixin, OwnerRequiredMixin, FormView):
    # TODO: Warn parent in the template that child accounts will also be deleted.
    form_class = DeleteConfirmForm
    template_name = 'accounts/profile_delete.html'

    def get_object(self):
        return get_object_or_404(AppUser, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['target_user'] = self.get_object()
        return ctx

    def form_valid(self, form):
        user = self.get_object()
        logout(self.request)
        user.delete()
        messages.success(self.request, 'Your account and all linked child accounts have been deleted.')
        return redirect('home')


class ChildProfileView(LoginRequiredMixin, DetailView):
    # TODO: Show avatar, points, and challenge progress here.
    model = ChildProfile
    template_name = 'accounts/child_profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        user = get_object_or_404(AppUser, pk=self.kwargs['pk'])
        return get_object_or_404(ChildProfile, user=user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['is_owner'] = self.request.user == self.object.user
        return ctx


class ChildProfileEditView(ChildRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = ChildProfile
    form_class = ChildProfileEditForm
    template_name = 'accounts/profile_edit.html'

    def get_object(self, queryset=None):
        user = get_object_or_404(AppUser, pk=self.kwargs['pk'])
        return get_object_or_404(ChildProfile, user=user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Your profile has been updated.')
        return redirect('accounts:child-profile', pk=self.request.user.pk)

    def get_success_url(self):
        return reverse_lazy('accounts:child-profile', kwargs={'pk': self.request.user.pk})


class ChildProfileDeleteView(ChildRequiredMixin, OwnerRequiredMixin, FormView):
    # TODO: Decide whether children should be allowed to delete their own
    #       account or whether only the parent can do this. For now both
    #       are allowed — see also ParentChildDeleteView below.
    form_class = DeleteConfirmForm
    template_name = 'accounts/profile_delete.html'

    def get_object(self):
        return get_object_or_404(AppUser, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['target_user'] = self.get_object()
        return ctx

    def form_valid(self, form):
        user = self.get_object()
        logout(self.request)
        user.delete()
        messages.success(self.request, 'Your account has been permanently deleted.')
        return redirect('home')


class ParentChildListView(ParentRequiredMixin, ListView):
    model = ChildProfile
    template_name = 'accounts/parent_child_list.html'
    context_object_name = 'children'

    def get_queryset(self):
        parent_profile = get_object_or_404(ParentProfile, user=self.request.user)
        return ChildProfile.objects.filter(parent=parent_profile).select_related('user')


class ParentChildCreateView(ParentRequiredMixin, CreateView):
    form_class = ChildCreateForm
    template_name = 'accounts/parent_child_form.html'

    def form_valid(self, form):
        parent_profile = get_object_or_404(ParentProfile, user=self.request.user)
        form.save(parent_profile=parent_profile)
        messages.success(self.request, 'Child account created successfully.')
        return redirect('accounts:parent-child-list')

    def get_success_url(self):
        return reverse_lazy('accounts:parent-child-list')


class ParentChildEditView(ParentRequiredMixin, UpdateView):
    model = ChildProfile
    form_class = ChildEditByParentForm
    template_name = 'accounts/parent_child_form.html'
    context_object_name = 'child_profile'

    def get_object(self, queryset=None):
        parent_profile = get_object_or_404(ParentProfile, user=self.request.user)
        return get_object_or_404(
            ChildProfile,
            pk=self.kwargs['pk'],
            parent=parent_profile,   # security: parent can only edit their own children
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.object.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Child profile updated.')
        return redirect('accounts:parent-child-list')

    def get_success_url(self):
        return reverse_lazy('accounts:parent-child-list')


class ParentChildDeleteView(ParentRequiredMixin, FormView):
    form_class = DeleteConfirmForm
    template_name = 'accounts/profile_delete.html'

    def get_child_profile(self):
        parent_profile = get_object_or_404(ParentProfile, user=self.request.user)
        return get_object_or_404(
            ChildProfile,
            pk=self.kwargs['pk'],
            parent=parent_profile,
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['target_user'] = self.get_child_profile().user
        return ctx

    def form_valid(self, form):
        child_profile = self.get_child_profile()
        child_user = child_profile.user
        child_user.delete()   # cascades to ChildProfile
        messages.success(self.request, f'Child account "{child_user.username}" has been deleted.')
        return redirect('accounts:parent-child-list')