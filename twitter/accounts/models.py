from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from mptt.models import MPTTModel, TreeForeignKey
from django.utils import timezone
import datetime
from django.urls import reverse


class ProfileImage(models.Model):
    background_picture = models.ImageField(default="image 2.jpg")
    picture = models.ImageField(default="image 2.jpg")


class Profile(models.Model):
    bio = models.CharField(max_length=160)
    locations = models.CharField(max_length=30)
    website = models.CharField(max_length=100)
    birth_date = models.DateField()
    images = models.ForeignKey(
        ProfileImage, related_name="profile", on_delete=models.CASCADE
    )

    # def get_absolute_url(self):
    #     return reverse('profile-detail', kwargs={'pk': self.pk})


class Question(models.Model):
    text = models.CharField(max_length=200)
    pub_date = models.DateTimeField("date published", default=timezone.now)

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Tweet(models.Model):
    context = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    file = models.FileField(default="default.txt")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tweets"
    )
    people_you_follow = models.BooleanField(default=False)
    question = models.OneToOneField(
        Question, on_delete=models.CASCADE, related_name="tweet", null=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}"

    def user_can_like(self, user):
        user_likes = user.likes.all()
        qs = user_likes.filter(tweet=self)
        if qs.exists():
            return False
        return True

    @property
    def get_likes_count(self):
        return self.likes.count()

    def get_absolute_url(self):
        return reverse("accounts:tweet", kwargs={"pk": self.pk})


class Choice(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="choices", null=True
    )
    text = models.CharField(max_length=25)

    def __str__(self):
        return self.text

    @property
    def get_vote_count(self):
        return self.votes.count()

    def user_can_vote(self, user):
        user_votes = user.votes.all()
        qs = user_votes.filter(choice=self)
        if qs.exists():
            return False
        return True


class Vote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes"
    )
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} voted for {self.choice.text[:15]}"


class Likes(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes"
    )
    tweet = models.ForeignKey(
        Tweet, on_delete=models.CASCADE, null=True, related_name="likes"
    )
    reply = models.ForeignKey(
        "Reply", on_delete=models.CASCADE, null=True, related_name="likes"
    )

    def __str__(self):
        return f"{self.user} liked"


class User(AbstractUser):
    is_online = models.BooleanField(default=False)
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name="user", null=True
    )
    followers = models.ManyToManyField(
        "User", symmetrical=False, related_name="following"
    )
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.username}"


class Reply(MPTTModel):
    context = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, related_name="children", null=True
    )
    tweet = models.ForeignKey(
        Tweet, on_delete=models.CASCADE, related_name="replies", null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
    )
    file = models.FileField(upload_to="media/")

    class MPTTMeta:
        order_insertion_by = ["-created_at"]

    def user_can_like(self, user):
        user_likes = user.likes.all()
        qs = user_likes.filter(reply=self)
        if qs.exists():
            return False
        return True

    @property
    def get_likes_count(self):
        return self.likes.count()


class NewsFeed(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="news_feed",
    )
    created_at = models.DateTimeField(default=timezone.now)
    description = models.CharField(max_length=250)
    is_read = models.BooleanField(default=False)
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_news_feed",
        null=True,
    )
