from django.test import TestCase
from accounts.models import AppUser, ParentProfile, ChildProfile

class ParentChildDeletionTest(TestCase):
    def test_delete_parent_with_child_succeeds(self):
        parent_user = AppUser.objects.create_user(
            username='parent_user',
            email='parent@test.com',
            password='password123',
            role=AppUser.Role.PARENT
        )
        parent_profile = parent_user.parent_profile

        child_user = AppUser.objects.create_user(
            username='child_user',
            email='child@test.com',
            password='password123',
            role=AppUser.Role.CHILD
        )
        child_profile = ChildProfile.objects.create(
            user=child_user,
            parent=parent_profile
        )

        self.assertEqual(AppUser.objects.count(), 2)
        self.assertEqual(ParentProfile.objects.count(), 1)
        self.assertEqual(ChildProfile.objects.count(), 1)

        parent_user.delete()

        self.assertEqual(AppUser.objects.count(), 0)
        self.assertEqual(ParentProfile.objects.count(), 0)
        self.assertEqual(ChildProfile.objects.count(), 0)

    def test_delete_profile_directly_deletes_user(self):
        teacher_user = AppUser.objects.create_user(
            username='teacher_user',
            email='teacher@test.com',
            password='password123',
            role=AppUser.Role.TEACHER
        )
        teacher_profile = teacher_user.teacher_profile
        
        teacher_profile.delete()
        
        self.assertFalse(AppUser.objects.filter(username='teacher_user').exists())
