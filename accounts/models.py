from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse


class AppUser(AbstractUser):


    class Role(models.TextChoices):
        TEACHER = 'teacher', 'Teacher'
        PARENT = 'parent', 'Parent'
        CHILD = 'child', 'Child'

    role = models.CharField(
        max_length=10,
        choices=[(tag.value, tag.label) for tag in Role],
        default=Role.CHILD,
    )

    age = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        null=True,
        blank=True,
    )

    email = models.EmailField(unique=True)


    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_parent(self):
        return self.role == self.Role.PARENT

    @property
    def is_child(self):
        return self.role == self.Role.CHILD


    def get_dashboard_url(self):
        if self.is_teacher:
            return reverse('accounts:teacher-profile', kwargs={'pk': self.pk})
        if self.is_parent:
            return reverse('accounts:parent-profile', kwargs={'pk': self.pk})
        if self.is_child:
            return reverse('accounts:child-profile', kwargs={'pk': self.pk})
        return reverse('home')


    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class TeacherProfile(models.Model):
    # TODO: Add subject/specialisation field when the challenges app is built.
    # TODO: Link to groups/classrooms when that model is created.


    user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        limit_choices_to={'role': AppUser.Role.TEACHER},
    )

    bio = models.TextField(blank=True, default='')

    # TODO: Add profile picture field

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Teacher profile — {self.user.username}"

    class Meta:
        verbose_name = 'Teacher Profile'
        verbose_name_plural = 'Teacher Profiles'


class ParentProfile(models.Model):
    # TODO: Add statistics when the challenges/achievements apps are complete (e.g. total_points_across_children()).

    user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        limit_choices_to={'role': AppUser.Role.PARENT},
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parent profile — {self.user.username}"

    @property
    def children(self):
        return self.child_profiles.all()

    class Meta:
        verbose_name = 'Parent Profile'
        verbose_name_plural = 'Parent Profiles'


class ChildProfile(models.Model):
    # TODO: Add total_points, current_level computed fields once the achievements app is ready.
    # TODO: Avatar FK/M2M will be added.

    user = models.OneToOneField(
        AppUser,
        on_delete=models.CASCADE,
        related_name='child_profile',
        limit_choices_to={'role': AppUser.Role.CHILD},
    )

    parent = models.ForeignKey(
        ParentProfile,
        on_delete=models.CASCADE,
        related_name='child_profiles',
    )

    # TODO: Add avatar = models.ForeignKey('Avatar', ...) when Avatar model is built
    # TODO: Add progress/statistics fields when challenges app is ready

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Child profile — {self.user.username} (parent: {self.parent.user.username})"

    class Meta:
        verbose_name = 'Child Profile'
        verbose_name_plural = 'Child Profiles'