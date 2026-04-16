from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AppUser, TeacherProfile, ParentProfile         #ChildProfile when todo done


@receiver(post_save, sender=AppUser)
def create_role_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.is_teacher and not hasattr(instance, 'teacher_profile'):
        TeacherProfile.objects.create(user=instance)

    elif instance.is_parent and not hasattr(instance, 'parent_profile'):
        ParentProfile.objects.create(user=instance)

    # TODO: Consider raising a warning log if a child user is created
    #       without a ChildProfile, so it's easier to catch during development.