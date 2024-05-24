from django.contrib import admin
from .models import Profile, Reply, Tweet, ProfileImage, Likes, Vote, Choice, Question
from django.contrib.auth import get_user_model
from mptt.admin import MPTTModelAdmin


class ProfileImageAdmin(admin.ModelAdmin):
    fields = ["background_picture", "picture"]
    list_display = ("picture",)


class ProfileAdmin(admin.ModelAdmin):
    fields = ["bio", "website", "locations", "birth_date", "images"]
    list_display = ("locations", "birth_date")
    search_fields = ["profile__user__username"]
    list_filter = ["locations", "birth_date"]


class PlayerAdmin(admin.ModelAdmin):
    fieldsets = (
        (
            "PlayerDetails",
            {
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "is_online",
                )
            },
        ),
        ("PersonalizedData", {"fields": ("profile", "followers")}),
    )
    list_display = ("username", "profile", "email", "is_online", "created_at")
    list_filter = ["is_online", "created_at"]
    search_fields = ["username", "email"]
    ordering = ["date_joined"]


class TweetAdmin(admin.ModelAdmin):
    fields = ["context", "file", "user", "question", "people_you_follow"]
    list_display = ("user", "created_at", "updated_at", "question", "people_you_follow")
    search_fields = ["user__username"]
    list_filter = ["created_at", "updated_at", "people_you_follow"]


class VoteAdmin(admin.ModelAdmin):
    fields = ["user", "choice"]
    list_display = ("user", "choice")


class LikesAdmin(admin.ModelAdmin):
    fields = ["user", "tweet", "reply"]
    list_display = ("user", "tweet", "reply")


admin.site.register(Tweet, TweetAdmin)
admin.site.register(Reply, MPTTModelAdmin)
admin.site.register(get_user_model(), PlayerAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(ProfileImage, ProfileImageAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(Likes, LikesAdmin)
admin.site.register(Question)
admin.site.register(Choice)
