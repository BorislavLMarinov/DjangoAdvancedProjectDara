from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AppUser, TeacherProfile, ParentProfile, ChildProfile


class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    can_delete = False


class ParentProfileInline(admin.StackedInline):
    model = ParentProfile
    can_delete = False


class ChildProfileInline(admin.StackedInline):
    model = ChildProfile
    can_delete = False


@admin.register(AppUser)
class AppUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'age', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)


    def get_inlines(self, request, obj=None):
        if obj:
            if obj.is_teacher:
                return [TeacherProfileInline]
            elif obj.is_parent:
                return [ParentProfileInline]
            elif obj.is_child:
                return [ChildProfileInline]
        return []

    fieldsets = UserAdmin.fieldsets + (
        ('ProjectDara', {
            'fields': ('role', 'age'),
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('ProjectDara', {
            'fields': ('role', 'age', 'email'),
        }),
    )


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')


@admin.register(ChildProfile)
class ChildProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'parent', 'created_at', 'updated_at')
    list_filter = ('parent',)
    search_fields = ('user__username', 'parent__user__username')