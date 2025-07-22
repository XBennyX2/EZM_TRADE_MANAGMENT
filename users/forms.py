# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

class ChangeUserRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['role', 'store']

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput, label="Old Password")
    new_password1 = forms.CharField(widget=forms.PasswordInput, label="New Password")
    new_password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        if new_password1 != new_password2:
            raise forms.ValidationError(
                "New passwords must match"
            )

class CustomUserCreationFormAdmin(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    phone_number = forms.CharField(max_length=20, required=False)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('first_name', 'last_name', 'email', 'role', 'phone_number')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']

class AdminSettingsForm(forms.Form):
    CHOICES = [
        ('edit_profile', 'Edit Profile Information'),
        ('change_password', 'Change Password'),
    ]
    selection = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect, label="Select Action")

class AccountResetForm(forms.Form):
    """Form for admin account reset with email update capability"""

    new_email = forms.EmailField(
        max_length=254,
        required=True,
        label="New Email Address",
        help_text="The new email address where credentials will be sent",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new email address'
        })
    )

    reset_reason = forms.CharField(
        required=False,
        label="Reset Reason",
        help_text="Optional reason for the account reset (will be recorded in audit trail)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter the reason for resetting this account (e.g., user forgot credentials, security concern, etc.)'
        })
    )

    confirm_reset = forms.BooleanField(
        required=True,
        label="I understand the consequences and want to proceed with resetting this account",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user_being_reset = kwargs.pop('user_being_reset', None)
        super().__init__(*args, **kwargs)

        # Pre-populate with current email if available
        if self.user_being_reset:
            self.fields['new_email'].initial = self.user_being_reset.email

    def clean_new_email(self):
        """Validate that the new email is unique (except for the user being reset)"""
        new_email = self.cleaned_data.get('new_email')

        if new_email:
            # Check if email exists for other users
            existing_user = CustomUser.objects.filter(email=new_email).first()

            if existing_user and existing_user != self.user_being_reset:
                raise forms.ValidationError(
                    "This email address is already in use by another user. Please choose a different email."
                )

        return new_email
