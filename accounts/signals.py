from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver

from .models import AppUser, TeacherProfile, ParentProfile, ChildProfile


@receiver(post_save, sender=AppUser)
def create_role_profile(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.is_teacher and not hasattr(instance, 'teacher_profile'):
        TeacherProfile.objects.create(user=instance)

    elif instance.is_parent and not hasattr(instance, 'parent_profile'):
        ParentProfile.objects.create(user=instance)


@receiver(pre_delete, sender=ParentProfile)
def delete_associated_children(sender, instance, **kwargs):
    child_user_ids = instance.child_profiles.values_list('user_id', flat=True)
    if child_user_ids:
        AppUser.objects.filter(pk__in=child_user_ids).delete()


@receiver(post_delete, sender=TeacherProfile)
@receiver(post_delete, sender=ParentProfile)
@receiver(post_delete, sender=ChildProfile)
def delete_user_on_profile_delete(sender, instance, **kwargs):
    user_id = getattr(instance, 'user_id', None)
    if user_id:
        AppUser.objects.filter(pk=user_id).delete()
