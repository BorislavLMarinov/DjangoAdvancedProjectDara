from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import AppUser, TeacherProfile, ParentProfile, ChildProfile


def _text_widget(placeholder='', css='form-control'):
    return forms.TextInput(attrs={'class': css, 'placeholder': placeholder})


def _email_widget(placeholder=''):
    return forms.EmailInput(attrs={'class': 'form-control', 'placeholder': placeholder})


def _password_widget(placeholder=''):
    return forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': placeholder})


def _select_widget():
    return forms.Select(attrs={'class': 'form-select'})


def _textarea_widget(placeholder='', rows=4):
    return forms.Textarea(attrs={'class': 'form-control', 'placeholder': placeholder, 'rows': rows})


class RegisterForm(UserCreationForm):
    REGISTER_ROLE_CHOICES = [
        ('', '— Select your role —'),
        (AppUser.Role.TEACHER, 'Teacher'),
        (AppUser.Role.PARENT, 'Parent'),
    ]

    role = forms.ChoiceField(
        choices=REGISTER_ROLE_CHOICES,
        label='I am a',
        widget=_select_widget(),
        help_text='Children accounts are created by their parent after the parent registers.',
    )

    email = forms.EmailField(
        required=True,
        label='Email address',
        widget=_email_widget('you@example.com'),
    )

    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=120,
        label='Age',
        widget=_text_widget('Your age'),
        help_text='Must be between 1 and 120.',
    )

    class Meta:
        model = AppUser
        fields = ('username', 'email', 'age', 'role', 'password1', 'password2')
        widgets = {
            'username': _text_widget('Choose a username'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = _password_widget('Password')
        self.fields['password2'].widget = _password_widget('Confirm password')
        self.fields['password1'].help_text = 'At least 8 characters.'
        self.fields['password2'].help_text = ''
        self.fields['username'].help_text = ''

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if not role:
            raise ValidationError('Please select a role.')
        if role == AppUser.Role.CHILD:
            raise ValidationError(
                'Child accounts cannot be registered publicly. '
                'Ask your parent to create your account.'
            )
        return role

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if AppUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email.lower()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.age = self.cleaned_data['age']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    # TODO: Consider adding rate-limiting / lockout after failed attempts.
    ROLE_CHOICES = [
        ('', '— I am a… —'),
        (AppUser.Role.CHILD, 'Child'),
        (AppUser.Role.TEACHER, 'Teacher'),
        (AppUser.Role.PARENT, 'Parent'),
    ]

    role_hint = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=False,
        label='I am a',
        widget=_select_widget(),
        help_text='Optional — helps redirect you to the right dashboard.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = _text_widget('Username')
        self.fields['username'].label = 'Username'
        self.fields['password'].widget = _password_widget('Password')
        self.fields['password'].label = 'Password'


class TeacherProfileEditForm(forms.ModelForm):
    # TODO: Add profile picture field.
    username = forms.CharField(
        required=False,
        disabled=True,
        label='Username',
        widget=_text_widget(),
        help_text='Username cannot be changed here.',
    )

    email = forms.EmailField(
        required=True,
        label='Email address',
        widget=_email_widget(),
    )

    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=120,
        label='Age',
        widget=_text_widget(),
    )

    class Meta:
        model = TeacherProfile
        fields = ('bio',)
        widgets = {
            'bio': _textarea_widget('Tell children and parents a little about yourself.'),
        }
        labels = {
            'bio': 'About me',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['age'].initial = self.user.age

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = AppUser.objects.filter(email__iexact=email).exclude(pk=self.user.pk)
        if qs.exists():
            raise ValidationError('This email is already in use by another account.')
        return email.lower()

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.email = self.cleaned_data['email']
            self.user.age = self.cleaned_data['age']
            if commit:
                self.user.save()
                profile.save()
        return profile


class ParentProfileEditForm(forms.ModelForm):
    username = forms.CharField(
        required=False,
        disabled=True,
        label='Username',
        widget=_text_widget(),
        help_text='Username cannot be changed here.',
    )

    email = forms.EmailField(
        required=True,
        label='Email address',
        widget=_email_widget(),
    )

    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=120,
        label='Age',
        widget=_text_widget(),
    )

    class Meta:
        model = ParentProfile
        fields = ()
        # TODO: Add fields (e.g. preferred language, notification prefs) as needed

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
            self.fields['age'].initial = self.user.age

    def clean_email(self):
        email = self.cleaned_data.get('email')
        qs = AppUser.objects.filter(email__iexact=email).exclude(pk=self.user.pk)
        if qs.exists():
            raise ValidationError('This email is already in use by another account.')
        return email.lower()

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.email = self.cleaned_data['email']
            self.user.age = self.cleaned_data['age']
            if commit:
                self.user.save()
                profile.save()
        return profile


class ChildProfileEditForm(forms.ModelForm):
    # TODO: Add avatar selection field once Avatar model is built.
    username = forms.CharField(
        required=False,
        disabled=True,
        label='Username',
        widget=_text_widget(),
        help_text='Your username was chosen by your parent.',
    )

    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=120,
        label='Age',
        widget=_text_widget(),
    )

    class Meta:
        model = ChildProfile
        fields = ()
        # TODO: fields = ('avatar',) once Avatar FK is added

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['age'].initial = self.user.age

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.age = self.cleaned_data['age']
            if commit:
                self.user.save()
                profile.save()
        return profile


class ChildCreateForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        label='Email address (optional)',
        widget=_email_widget('child@example.com'),
    )

    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=18,
        label="Child's age",
        widget=_text_widget("Child's age"),
        help_text='Must be between 1 and 18.',
    )

    class Meta:
        model = AppUser
        fields = ('username', 'email', 'age', 'password1', 'password2')
        widgets = {
            'username': _text_widget("Child's username"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget = _password_widget('Password for the child')
        self.fields['password2'].widget = _password_widget('Confirm password')
        self.fields['password1'].help_text = 'At least 8 characters.'
        self.fields['password2'].help_text = ''
        self.fields['username'].help_text = 'The child will use this to log in.'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and AppUser.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email.lower() if email else ''

    def save(self, commit=True, parent_profile=None):
        user = super().save(commit=False)
        user.role = AppUser.Role.CHILD
        user.age = self.cleaned_data['age']
        user.email = self.cleaned_data.get('email', '')
        if commit:
            user.save()
            if parent_profile:
                ChildProfile.objects.create(user=user, parent=parent_profile)
        return user


class ChildEditByParentForm(forms.ModelForm):
    # TODO: Allow parent to assign an avatar once Avatar model exists.
    username = forms.CharField(
        required=False,
        disabled=True,
        label='Username',
        widget=_text_widget(),
        help_text='Username cannot be changed.',
    )

    age = forms.IntegerField(
        required=True,
        min_value=1,
        max_value=18,
        label="Child's age",
        widget=_text_widget(),
    )

    email = forms.EmailField(
        required=False,
        label='Email address (optional)',
        widget=_email_widget(),
    )

    class Meta:
        model = ChildProfile
        fields = ()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['age'].initial = self.user.age
            self.fields['email'].initial = self.user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            qs = AppUser.objects.filter(email__iexact=email).exclude(pk=self.user.pk)
            if qs.exists():
                raise ValidationError('This email is already used by another account.')
            return email.lower()
        return ''

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user:
            self.user.age = self.cleaned_data['age']
            self.user.email = self.cleaned_data.get('email', '')
            if commit:
                self.user.save()
                profile.save()
        return profile


class DeleteConfirmForm(forms.Form):
    # TODO: Consider adding password re-entry for extra security on deletion.
    confirmation = forms.CharField(
        label='Type CONFIRM to permanently delete your account',
        max_length=10,
        widget=_text_widget('CONFIRM'),
    )

    def clean_confirmation(self):
        value = self.cleaned_data.get('confirmation', '')
        if value.strip().upper() != 'CONFIRM':
            raise ValidationError('Please type CONFIRM (in capitals) to proceed.')
        return value