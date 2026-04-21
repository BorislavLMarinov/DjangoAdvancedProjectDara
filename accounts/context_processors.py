from trainees.models import TraineeProfile, TaskCompletion
from challenges.models import BaseTask, CountingTask, ArithmeticTask, PatternChallenge, MazeTask
from accounts.models import ChildProfile

def aside_stats(request):
    stats = {}
    
    if request.user.is_authenticated:
        if request.user.is_child:
            try:
                trainee = request.user.child_profile.trainee_profile
                stats['type'] = 'trainee'
                stats['level'] = trainee.level
                stats['coins'] = trainee.coins
                stats['xp_percent'] = trainee.xp_progress_percent
                stats['completions_count'] = TaskCompletion.objects.filter(trainee=trainee).count()
            except Exception:
                pass
        
        elif request.user.is_teacher:
            stats['type'] = 'teacher'
            teacher = request.user.teacher_profile
            count = 0
            for model in [CountingTask, ArithmeticTask, PatternChallenge, MazeTask]:
                count += model.objects.filter(created_by=teacher).count()
            stats['missions_created'] = count
            
        elif request.user.is_parent:
            stats['type'] = 'parent'
            parent = request.user.parent_profile
            stats['children_count'] = ChildProfile.objects.filter(parent=parent).count()
    
    else:
        stats['type'] = 'public'
        total_missions = 0
        for model in [CountingTask, ArithmeticTask, PatternChallenge, MazeTask]:
            total_missions += model.objects.count()
        stats['total_missions'] = total_missions
        
    return {'aside_stats': stats}
