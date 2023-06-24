from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscription


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'pk', 'username', 'email', 'first_name', 'last_name',
        'is_active', 'is_staff',
    )
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'subscriber', 'author'
    )
    search_fields = ('subscriber', 'author')
    empty_value_display = '-пусто-'
