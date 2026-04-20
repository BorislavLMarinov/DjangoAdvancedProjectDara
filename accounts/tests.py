from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import AppUser, TeacherProfile, ParentProfile, ChildProfile


class AccountsAppTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_01_user_registration_teacher_and_parent(self):
        # Teacher registration
        teacher_data = {
            'username': 'teacher_maria',
            'email': 'maria@example.com',
            'age': 30,
            'role': AppUser.Role.TEACHER,
            'password1': 'securepassword123',
            'password2': 'securepassword123',
        }
        response = self.client.post(reverse('accounts:register'), data=teacher_data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(AppUser.objects.filter(username='teacher_maria').exists())
        user = AppUser.objects.get(username='teacher_maria')
        self.assertEqual(user.role, AppUser.Role.TEACHER)
        self.assertRedirects(response, reverse('accounts:teacher-profile', kwargs={'pk': user.pk}))

        # Logout before next registration
        self.client.logout()

        # Parent registration
        parent_data = {
            'username': 'parent_ivan',
            'email': 'ivan@example.com',
            'age': 40,
            'role': AppUser.Role.PARENT,
            'password1': 'securepassword123',
            'password2': 'securepassword123',
        }
        response = self.client.post(reverse('accounts:register'), data=parent_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AppUser.objects.filter(username='parent_ivan').exists())
        user = AppUser.objects.get(username='parent_ivan')
        self.assertEqual(user.role, AppUser.Role.PARENT)
        self.assertRedirects(response, reverse('accounts:parent-profile', kwargs={'pk': user.pk}))

    def test_02_signal_verification(self):
        # Test Teacher signal
        teacher_user = AppUser.objects.create_user(
            username='teacher_signal',
            email='tsignal@example.com',
            password='password123',
            role=AppUser.Role.TEACHER
        )
        self.assertTrue(TeacherProfile.objects.filter(user=teacher_user).exists())

        # Test Parent signal
        parent_user = AppUser.objects.create_user(
            username='parent_signal',
            email='psignal@example.com',
            password='password123',
            role=AppUser.Role.PARENT
        )
        self.assertTrue(ParentProfile.objects.filter(user=parent_user).exists())

    def test_03_user_list_view_access(self):
        teacher = AppUser.objects.create_user(
            username='teacher_user', email='t@t.com', password='p', role=AppUser.Role.TEACHER
        )
        parent = AppUser.objects.create_user(
            username='parent_user', email='p@p.com', password='p', role=AppUser.Role.PARENT
        )
        child_user = AppUser.objects.create_user(
            username='child_user', email='c@c.com', password='p', role=AppUser.Role.CHILD
        )

        url = reverse('accounts:user-list')

        self.client.force_login(teacher)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(parent)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.client.force_login(child_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_04_parent_creating_child_account(self):
        parent = AppUser.objects.create_user(
            username='parent_test', email='pt@t.com', password='password123', role=AppUser.Role.PARENT
        )
        self.client.force_login(parent)

        child_data = {
            'username': 'child_test',
            'email': 'ct@t.com',
            'age': 8,
            'password1': 'childpass123',
            'password2': 'childpass123',
        }
        url = reverse('accounts:parent-child-create')
        response = self.client.post(url, data=child_data)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(AppUser.objects.filter(username='child_test', role=AppUser.Role.CHILD).exists())
        child_user = AppUser.objects.get(username='child_test')
        self.assertTrue(ChildProfile.objects.filter(user=child_user, parent=parent.parent_profile).exists())

    def test_05_child_profile_deletion_by_parent(self):
        parent = AppUser.objects.create_user(
            username='parent_del', email='pd@t.com', password='p', role=AppUser.Role.PARENT
        )
        child_user = AppUser.objects.create_user(
            username='child_del', email='cd@t.com', password='p', role=AppUser.Role.CHILD
        )
        child_profile = ChildProfile.objects.create(user=child_user, parent=parent.parent_profile)

        self.client.force_login(parent)
        url = reverse('accounts:parent-child-delete', kwargs={'pk': child_profile.pk})
        
        # Initial POST to confirm deletion
        response = self.client.post(url, data={'confirmation': 'CONFIRM'})
        
        self.assertEqual(response.status_code, 302)
        self.assertFalse(AppUser.objects.filter(username='child_del').exists())
        self.assertFalse(ChildProfile.objects.filter(pk=child_profile.pk).exists())

    def test_06_custom_user_model_properties(self):
        teacher = AppUser(role=AppUser.Role.TEACHER)
        parent = AppUser(role=AppUser.Role.PARENT)
        child = AppUser(role=AppUser.Role.CHILD)

        self.assertTrue(teacher.is_teacher)
        self.assertFalse(teacher.is_parent)
        self.assertFalse(teacher.is_child)

        self.assertTrue(parent.is_parent)
        self.assertFalse(parent.is_teacher)
        self.assertFalse(parent.is_child)

        self.assertTrue(child.is_child)
        self.assertFalse(child.is_teacher)
        self.assertFalse(child.is_parent)

    def test_07_redirect_logic_after_login(self):
        teacher = AppUser.objects.create_user(
            username='teacher_log', email='tl@t.com', password='password123', role=AppUser.Role.TEACHER
        )
        parent = AppUser.objects.create_user(
            username='parent_log', email='pl@t.com', password='password123', role=AppUser.Role.PARENT
        )
        child_user = AppUser.objects.create_user(
            username='child_log', email='cl@t.com', password='password123', role=AppUser.Role.CHILD
        )

        ChildProfile.objects.create(user=child_user, parent=parent.parent_profile)

        login_url = reverse('accounts:login')

        # Teacher Login
        response = self.client.post(login_url, data={'username': 'teacher_log', 'password': 'password123'}, follow=True)
        self.assertRedirects(response, reverse('accounts:teacher-profile', kwargs={'pk': teacher.pk}))

        # Parent Login
        self.client.logout()
        response = self.client.post(login_url, data={'username': 'parent_log', 'password': 'password123'}, follow=True)
        self.assertRedirects(response, reverse('accounts:parent-profile', kwargs={'pk': parent.pk}))

        # Child Login
        self.client.logout()
        response = self.client.post(login_url, data={'username': 'child_log', 'password': 'password123'}, follow=True)
        self.assertRedirects(response, reverse('accounts:child-profile', kwargs={'pk': child_user.pk}))
