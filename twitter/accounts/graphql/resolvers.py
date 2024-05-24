import typing
from django.utils import timezone
from .types import Tweet
from .. import models
import strawberry


def users():
    return models.User.objects.all()


def user(id: strawberry.ID):
    return models.User.objects.get(id=id)


def profiles():
    return models.Profile.objects.all()


def profile(id: strawberry.ID):
    return models.Profile.objects.get(id=id)


def tweets():
    return models.Tweet.objects.filter(created_at__lte=timezone.now())


def tweet(id: strawberry.ID):
    return models.Tweet.objects.get(id=id)


def replies():
    return models.Reply.objects.filter(created_at__lte=timezone.now())


def reply(id: strawberry.ID):
    return models.Reply.objects.get(id=id)


def questions():
    return models.Question.objects.all()


def question(id: strawberry.ID):
    return models.Question.objects.get(id=id)


def choices():
    return models.Choice.objects.all()


def choice(id: strawberry.ID):
    return models.Choice.objects.get(id=id)


def newsfeeds():
    return models.NewsFeed.objects.all()


def newsfeed(id: strawberry.ID):
    return models.NewsFeed.objects.get(id=id)


def home(id: strawberry.ID) -> typing.List[Tweet]:
    by_user = models.User.objects.get(id=id)
    user_following = by_user.following.all()
    following_tweets = models.Tweet.objects.filter(
        user__following__id__in=user_following
    )
    user_tweets = models.Tweet.objects.filter(user=by_user)
    tweet_list = (following_tweets | user_tweets).distinct()
    return tweet_list
