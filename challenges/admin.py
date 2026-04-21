from django.contrib import admin
from .models import DifficultyLevel, CountingTask, ArithmeticTask, MazeTask, PatternChallenge

admin.site.register(DifficultyLevel)

class BaseTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'difficulty', 'base_points', 'created_by')
    list_filter = ('difficulty', 'created_by')
    search_fields = ('title',)
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            # Try to find a TeacherProfile for the admin user
            if hasattr(request.user, 'teacher_profile'):
                obj.created_by = request.user.teacher_profile
        super().save_model(request, obj, form, change)

@admin.register(CountingTask)
class CountingTaskAdmin(BaseTaskAdmin):
    pass

@admin.register(ArithmeticTask)
class ArithmeticTaskAdmin(BaseTaskAdmin):
    exclude = ('correct_answer', 'choice_1', 'choice_2', 'choice_3')

@admin.register(PatternChallenge)
class PatternChallengeAdmin(BaseTaskAdmin):
    pass

@admin.register(MazeTask)
class MazeTaskAdmin(BaseTaskAdmin):
    exclude = ('choice_1', 'choice_2', 'choice_3')