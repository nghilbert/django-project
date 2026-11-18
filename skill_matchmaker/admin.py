from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Admin, Comment, Post, Reaction, Skill, User, UserSkill


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Use email instead of the default username
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "is_admin"]
    # The default filters include is_staff, which isn't a field anymore
    list_filter = ["is_superuser", "is_active", "groups"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        ("Personal info", {"fields": ["first_name", "last_name", "bio", "profile_picture"]}),
        (
            "Permissions",
            {"fields": ["is_active", "is_superuser", "groups", "user_permissions"]},
        ),
        ("Important dates", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (None, {"fields": ["email", "usable_password", "password1", "password2"]}),
    ]
    actions = ["make_admin", "remove_admin"]

    @admin.display(boolean=True, description="Admin")
    def is_admin(self, obj):
        return obj.is_staff

    @admin.action(description="Make admin")
    def make_admin(self, request, queryset):
        users = queryset.filter(admin__isnull=True)
        for user in users:
            Admin.promote(user)
        self.message_user(request, f"Made {len(users)} user(s) admin.", messages.SUCCESS)

    @admin.action(description="Remove admin")
    def remove_admin(self, request, queryset):
        if queryset.contains(request.user):
            self.message_user(
                request,
                "You cannot remove admin from yourself. No users were changed.",
                messages.WARNING,
            )
            return
        users = queryset.filter(admin__isnull=False)
        for user in users:
            user.admin.demote()
        self.message_user(request, f"Removed admin from {len(users)} user(s).", messages.SUCCESS)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "created_at"]
    search_fields = ["title", "content", "author__email"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["author", "post", "created_at"]
    search_fields = ["author__email", "post__title", "content"]


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ["emoji", "user", "post", "created_at"]
    list_filter = ["emoji"]
    search_fields = ["user__email", "post__title"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name", "category"]
    list_filter = ["category"]
    search_fields = ["name", "category"]


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ["user", "skill", "skill_type", "level"]
    list_filter = ["skill_type", "level"]
    search_fields = ["user__email", "skill__name"]
