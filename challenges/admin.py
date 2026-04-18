from django.contrib import admin
from .models import DifficultyLevel, CountingTask, ArithmeticTask, MazeTask, PatternChallenge

admin.site.register(DifficultyLevel)
admin.site.register(CountingTask)
admin.site.register(ArithmeticTask)
admin.site.register(PatternChallenge)

@admin.register(MazeTask)
class MazeTaskAdmin(admin.ModelAdmin):
    exclude = ('choice_1', 'choice_2', 'choice_3')
    list_display = ('title', 'difficulty', 'base_points')
    list_filter = ('difficulty',)
    search_fields = ('title',)