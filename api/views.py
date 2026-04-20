from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from challenges.models import CountingTask, ArithmeticTask, PatternChallenge, MazeTask
from .serializers import ChallengeSerializer, TraineeStatsSerializer

class ChallengeListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tasks = []
        for model in [CountingTask, ArithmeticTask, PatternChallenge, MazeTask]:
            tasks.extend(list(model.objects.select_related('difficulty').all()))
        
        serializer = ChallengeSerializer(tasks, many=True)
        return Response(serializer.data)

class TraineeStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_child:
            return Response(
                {"error": "Only trainees have stats endpoints."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        trainee = request.user.child_profile.trainee_profile
        serializer = TraineeStatsSerializer(trainee)
        return Response(serializer.data)
