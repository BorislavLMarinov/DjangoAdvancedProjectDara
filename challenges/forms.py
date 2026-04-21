from django import forms
from .models import MazeTask, ArithmeticTask, PatternChallenge, CountingTask, DifficultyLevel


class DifficultyLevelForm(forms.ModelForm):
    class Meta:
        model = DifficultyLevel
        fields = ['name', 'multiplier', 'color_code']
        widgets = {
            'color_code': forms.TextInput(attrs={'type': 'color'}),
        }

class MazeForm(forms.ModelForm):
    class Meta:
        model = MazeTask
        fields = ['title', 'description', 'difficulty', 'base_points', 'grid', 'end_row', 'end_col']
        widgets = {'grid': forms.Textarea(attrs={'rows': 4, 'placeholder': '[[0,1],[0,0]]', 'class': 'font-monospace'})}

class ArithmeticForm(forms.ModelForm):
    class Meta:
        model = ArithmeticTask
        fields = ['title', 'description', 'difficulty', 'base_points', 'number_a', 'number_b', 'operation']

class PatternForm(forms.ModelForm):
    class Meta:
        model = PatternChallenge
        fields = ['title', 'description', 'difficulty', 'base_points', 'sequence_data', 'correct_value', 'choice_1', 'choice_2', 'choice_3']


class CountingForm(forms.ModelForm):
    class Meta:
        model = CountingTask
        fields = ['title', 'description', 'difficulty', 'base_points', 'image', 'correct_answer', 'choice_1', 'choice_2', 'choice_3']