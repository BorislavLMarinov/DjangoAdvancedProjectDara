from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView, DetailView, CreateView, UpdateView, DeleteView

from accounts.mixins import TeacherRequiredMixin, ChildRequiredMixin
from trainees.models import TaskCompletion
from .models import MazeTask, ArithmeticTask, PatternChallenge, CountingTask, BaseTask
from .forms import MazeForm, ArithmeticForm, PatternForm, CountingForm

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
        context['mazes'] = MazeTask.objects.filter(created_by=teacher_profile)
        context['maths'] = ArithmeticTask.objects.filter(created_by=teacher_profile)
        context['patterns'] = PatternChallenge.objects.filter(created_by=teacher_profile)
        context['countings'] = CountingTask.objects.filter(created_by=teacher_profile)
        return context

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


class MissionListView(ChildRequiredMixin, TemplateView):
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


class TaskPlayView(ChildRequiredMixin, DetailView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = self.get_object()
        correct_val = getattr(task, 'correct_answer', None) or getattr(task, 'correct_value', None)
        context['options'] = task.get_all_options(correct_val)
        return context

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        user_answer = request.POST.get('answer')

        if task.check_answer(user_answer):
            trainee = request.user.child_profile.trainee_profile
            points = task.calculate_total_points()

            feedback = trainee.award_xp(points)

            TaskCompletion.objects.create(
                trainee=trainee,
                task=task,
                time_taken_seconds=30,  # TODO: Implement timer on frontend
                difficulty_snapshot=task.difficulty.name,
                xp_earned=points,
                coins_earned=feedback['coins_gained']
            )

            msg = f"🎉 Mission Clear! You earned {points} Stars!"
            if feedback['levels_gained'] > 0:
                msg += f" LEVEL UP! You are now level {feedback['new_level']}!"

            messages.success(request, msg)
            return redirect('home')
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