from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import ChildProfile
from .models import TraineeProfile


@receiver(post_save, sender=ChildProfile)
def create_trainee_profile(sender, instance, created, **kwargs):
    if created:
        TraineeProfile.objects.get_or_create(child=instance)


@receiver(post_save, sender=ChildProfile)
def save_trainee_profile(sender, instance, **kwargs):
    if hasattr(instance, 'trainee_profile'):
        instance.trainee_profile.save()
