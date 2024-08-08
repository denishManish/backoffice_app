from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, GroupDescription

from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('email', 'first_name', 'last_name', 'gender')
    list_filter = ('email', 'first_name', 'last_name', 'gender')

    """
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'patronymic', 'phone_number')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'birthday', 'password1', 'password2'),
        }),
    )
    """

    # add image here
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('patronymic', 'gender', 'birthday', 'image', 'phone_number', 'note')}),
        ('Address', {'fields': ('country', 'region', 'city', 'street', 'house', 'address_note')}),
    )
    add_fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('patronymic', 'gender', 'birthday', 'image', 'phone_number', 'note')}),
        ('Address', {'fields': ('country', 'region', 'city', 'street', 'house', 'address_note')}),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)


admin.site.register(User, CustomUserAdmin)
admin.site.register(GroupDescription)
