from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, DeleteView

from django.contrib.auth.mixins import LoginRequiredMixin
from accounts.mixins import TeacherRequiredMixin, ChildRequiredMixin
from trainees.services import complete_task
from .models import MazeTask, ArithmeticTask, PatternChallenge, CountingTask, BaseTask, DifficultyLevel
from .forms import MazeForm, ArithmeticForm, PatternForm, CountingForm, DifficultyLevelForm

TASK_MAP = {
    'maze': {'model': MazeTask, 'form_class': MazeForm, 'label': 'Maze Navigation'},
    'arithmetic': {'model': ArithmeticTask, 'form_class': ArithmeticForm, 'label': 'Math Challenge'},
    'pattern': {'model': PatternChallenge, 'form_class': PatternForm, 'label': 'Pattern Puzzle'},
    'counting': {'model': CountingTask, 'form_class': CountingForm, 'label': 'Counting Mission'},
}

class TeacherDashboardView(TeacherRequiredMixin, TemplateView):
    template_name = 'challenges/teacher_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teacher_profile = self.request.user.teacher_profile
        search_query = self.request.GET.get('q', '')

        mazes = MazeTask.objects.filter(created_by=teacher_profile)
        maths = ArithmeticTask.objects.filter(created_by=teacher_profile)
        patterns = PatternChallenge.objects.filter(created_by=teacher_profile)
        countings = CountingTask.objects.filter(created_by=teacher_profile)
        difficulties = DifficultyLevel.objects.all()

        if search_query:
            mazes = mazes.filter(title__icontains=search_query)
            maths = maths.filter(title__icontains=search_query)
            patterns = patterns.filter(title__icontains=search_query)
            countings = countings.filter(title__icontains=search_query)
            difficulties = difficulties.filter(name__icontains=search_query)

        context['mazes'] = mazes
        context['maths'] = maths
        context['patterns'] = patterns
        context['countings'] = countings
        context['difficulties'] = difficulties
        context['search_query'] = search_query
        return context

class DifficultyLevelCreateView(TeacherRequiredMixin, CreateView):
    model = DifficultyLevel
    form_class = DifficultyLevelForm
    template_name = 'challenges/difficulty_form.html'
    success_url = reverse_lazy('challenges:teacher-dashboard')

    def form_valid(self, form):
        messages.success(self.request, f"New difficulty level '{form.instance.name}' created!")
        return super().form_valid(form)

class DifficultyLevelEditView(TeacherRequiredMixin, UpdateView):
    model = DifficultyLevel
    form_class = DifficultyLevelForm
    template_name = 'challenges/difficulty_form.html'
    success_url = reverse_lazy('challenges:teacher-dashboard')

    def form_valid(self, form):
        messages.success(self.request, f"Difficulty level '{form.instance.name}' updated.")
        return super().form_valid(form)

class DifficultyLevelDeleteView(TeacherRequiredMixin, DeleteView):
    model = DifficultyLevel
    template_name = 'challenges/difficulty_confirm_delete.html'
    success_url = reverse_lazy('challenges:teacher-dashboard')

    def delete(self, request, *args, **kwargs):
        difficulty = self.get_object()
        try:
            response = super().delete(request, *args, **kwargs)
            messages.error(request, f"Difficulty level '{difficulty.name}' removed.")
            return response
        except models.ProtectedError:
            messages.error(request, f"Cannot delete '{difficulty.name}' because it is being used by missions.")
            return redirect('challenges:teacher-dashboard')

class BaseTaskMixin(TeacherRequiredMixin):
    context_object_name = 'task'

    def get_config(self):
        task_type = self.kwargs.get('task_type')
        return TASK_MAP.get(task_type)

    def get_queryset(self):
        config = self.get_config()
        if config:
            return config['model'].objects.all()
        return super().get_queryset()

    def get_form_class(self):
        config = self.get_config()
        if config:
            return config['form_class']
        return super().get_form_class()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        config = self.get_config()
        context['label'] = config['label'] if config else 'Mission'
        context['task_type'] = self.kwargs.get('task_type')
        return context

    def get_success_url(self):
        return reverse_lazy('challenges:teacher-dashboard')


class TaskCreateView(BaseTaskMixin, CreateView):
    template_name = 'challenges/task_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user.teacher_profile
        messages.success(self.request, f"Successfully debuted new {self.get_config()['label']}!")
        return super().form_valid(form)


class TaskEditView(BaseTaskMixin, UpdateView):
    template_name = 'challenges/task_form.html'

    def form_valid(self, form):
        messages.success(self.request, "Mission configuration updated.")
        return super().form_valid(form)


class TaskDeleteView(BaseTaskMixin, DeleteView):
    template_name = 'challenges/task_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        task = self.get_object()
        messages.error(request, f"Mission '{task.title}' has been permanently removed.")
        return super().delete(request, *args, **kwargs)


class MissionListView(LoginRequiredMixin, TemplateView):
    template_name = 'challenges/mission_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task_subclasses = [CountingTask, ArithmeticTask, PatternChallenge, MazeTask]
        disciplines = []

        for model in task_subclasses:
            missions = model.objects.all()
            if missions.exists():
                disciplines.append({
                    'name': model._meta.verbose_name_plural,
                    'missions': missions
                })

        context['disciplines'] = disciplines
        return context


class TaskPlayView(LoginRequiredMixin, DetailView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        context['options'] = task.get_all_options(task.correct_answer_value)
        return context

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        user_answer = request.POST.get('answer')

        if task.check_answer(user_answer):
            if request.user.is_child:
                trainee = request.user.child_profile.trainee_profile
                # Use the service layer logic
                result = complete_task(trainee, task, time_taken_seconds=30)

                msg = f"🎉 Mission Clear! You earned {result['xp_earned']} Stars!"
                if result['levels_gained'] > 0:
                    msg += f" LEVEL UP! You are now level {result['new_level']}!"

                if result['avatar_unlocked']:
                    msg += f" 🎁 New Avatar Unlocked: {result['avatar_unlocked'].name}!"
                
                messages.success(request, msg)
                return redirect('trainees:trainee-dashboard')
            else:
                messages.success(request, "🎉 Correct! (Testing mode: No rewards awarded for non-trainees)")
                return redirect('challenges:mission-list')
        else:
            messages.error(request, "❌ Not quite! Review your training and try again.")
            return self.get(request, *args, **kwargs)


class CountingPlayView(TaskPlayView):
    model = CountingTask
    context_object_name = 'task'
    template_name = 'challenges/counting_play.html'


class ArithmeticPlayView(TaskPlayView):
    model = ArithmeticTask
    context_object_name = 'task'
    template_name = 'challenges/arithmetic_play.html'


class PatternPlayView(TaskPlayView):
    model = PatternChallenge
    context_object_name = 'task'
    template_name = 'challenges/pattern_play.html'


class MazePlayView(TaskPlayView):
    model = MazeTask
    context_object_name = 'task'
    template_name = 'challenges/maze_play.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['grid_json'] = self.object.grid
        return context