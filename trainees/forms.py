from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Avatar, AvatarOwnership, TaskCompletion, TraineeProfile


def _select_widget():
    return forms.Select(attrs={'class': 'form-select'})


def _text_widget(placeholder=''):
    return forms.TextInput(attrs={'class': 'form-control', 'placeholder': placeholder})


def _textarea_widget(placeholder='', rows=3):
    return forms.Textarea(attrs={'class': 'form-control', 'placeholder': placeholder, 'rows': rows})


def _number_widget(placeholder=''):
    return forms.NumberInput(attrs={'class': 'form-control', 'placeholder': placeholder})


def _checkbox_widget():
    return forms.CheckboxInput(attrs={'class': 'form-check-input'})


class TaskCompletionForm(forms.Form):
    # TODO: Replace with JS-driven auto-submit once timer UI is built.
    task_id = forms.IntegerField(widget=forms.HiddenInput())

    time_taken_seconds = forms.IntegerField(
        min_value=1,
        max_value=7200,   # cap at 2 hours
        label='Time taken (seconds)',
        widget=_number_widget('e.g. 120'),
        help_text='How many seconds did the task take?',
    )

    def clean_time_taken_seconds(self):
        val = self.cleaned_data.get('time_taken_seconds')
        if val <= 0:
            raise ValidationError('Time must be at least 1 second.')
        return val


class AvatarPurchaseForm(forms.Form):
    avatar_id = forms.IntegerField(widget=forms.HiddenInput())

    confirm = forms.BooleanField(
        required=True,
        label='I confirm I want to spend my coins on this avatar.',
        widget=_checkbox_widget(),
        error_messages={'required': 'You must confirm the purchase.'},
    )


class SetActiveAvatarForm(forms.Form):
    avatar = forms.ModelChoiceField(
        queryset=Avatar.objects.none(),
        label='Choose your active avatar',
        widget=_select_widget(),
        empty_label='— No avatar —',
        required=False,
    )

    def __init__(self, *args, trainee: TraineeProfile = None, **kwargs):
        super().__init__(*args, **kwargs)
        if trainee:
            owned_ids = AvatarOwnership.objects.filter(trainee=trainee).values_list('avatar_id', flat=True)
            self.fields['avatar'].queryset = Avatar.objects.filter(pk__in=owned_ids)


class AvatarCreateEditForm(forms.ModelForm):
    # TODO: Add image upload once Pillow is configured.
    class Meta:
        model = Avatar
        fields = (
            'name',
            'description',
            'image_url',
            'rarity',
            'unlock_type',
            'coin_cost',
            'required_task',
            'available_from',
            'available_until',
            'is_active',
        )
        widgets = {
            'name':           _text_widget('Avatar name'),
            'description':    _textarea_widget('Brief description shown to children'),
            'image_url':      _text_widget('https://…'),
            'rarity':         _select_widget(),
            'unlock_type':    _select_widget(),
            'coin_cost':      _number_widget('0'),
            'required_task':  _select_widget(),
            'available_from': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'available_until': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'is_active':      _checkbox_widget(),
        }
        labels = {
            'image_url':      'Image URL',
            'unlock_type':    'How is this avatar unlocked?',
            'coin_cost':      'Coin cost (purchase only)',
            'required_task':  'Required task (achievement only)',
            'available_from': 'Available from (limited-time only)',
            'available_until': 'Available until (limited-time only)',
            'is_active':      'Visible in shop',
        }
        help_texts = {
            'coin_cost':      'Leave 0 for non-purchasable avatars.',
            'required_task':  'Leave blank unless unlock type is Achievement.',
            'available_from': 'Leave blank unless unlock type is Limited-time.',
            'available_until': 'Leave blank unless unlock type is Limited-time.',
        }

    def clean(self):
        cleaned = super().clean()
        unlock_type = cleaned.get('unlock_type')
        coin_cost = cleaned.get('coin_cost', 0)
        required_task = cleaned.get('required_task')
        available_from = cleaned.get('available_from')
        available_until = cleaned.get('available_until')

        if unlock_type == Avatar.UnlockType.PURCHASE and coin_cost == 0:
            raise ValidationError('A purchasable avatar must have a coin cost greater than 0.')

        if unlock_type == Avatar.UnlockType.ACHIEVEMENT and not required_task:
            raise ValidationError('An achievement avatar must have a required task.')

        if unlock_type == Avatar.UnlockType.LIMITED_TIME:
            if not available_from or not available_until:
                raise ValidationError('A limited-time avatar must have both start and end dates.')
            if available_from >= available_until:
                raise ValidationError('The start date must be before the end date.')

        return cleaned


class AvatarDeleteForm(forms.Form):
    avatar_name = forms.CharField(
        disabled=True,
        label='Avatar being deleted',
        widget=_text_widget(),
    )

    confirm = forms.BooleanField(
        required=True,
        label='I understand this will remove this avatar from all children who own it.',
        widget=_checkbox_widget(),
        error_messages={'required': 'You must confirm before deleting.'},
    )
