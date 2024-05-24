import string
import typing
from datetime import timedelta, datetime, timezone
import jwt
import strawberry
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email, URLValidator
from django.utils.crypto import get_random_string
from . import resolvers

from .input import (
    RegisterUserInput,
    RefreshTokenInput,
    TweetInput,
    ReplyInput,
    NewsFeedInput,
)
from .types import (
    User,
    Token,
    RefreshToken,
    Profile,
    VerifyToken,
    Tweet,
    Reply,
    ReplyOfReply,
    Choice,
    Question,
    NewsFeed,
    Vote,
    Likes,
)
from .. import models

CSRF_ALLOWED_CHARS = string.ascii_letters + string.digits
CSRF_SECRET_LENGTH = 32


def get_payload_from_token(token):
    try:
        payload = jwt.decode(token, key=settings.SECRET_KEY, algorithms="HS256")
    except jwt.ExpiredSignatureError:
        raise ValidationError("Signature has expired")
    except jwt.DecodeError:
        raise ValidationError("Error decoding signature")
    except jwt.InvalidTokenError:
        raise ValidationError("Invalid token")
    return payload


def create_csrf_token():
    return get_random_string(CSRF_SECRET_LENGTH, allowed_chars=CSRF_ALLOWED_CHARS)


def is_valid_url(url):
    validate_url = URLValidator()
    validate_url(url)
    return True


def user_with_username_exists(username):
    return models.User.objects.filter(username=username).exists()


def user_with_email_exists(email):
    return models.User.objects.filter(email=email).exists()


def is_valid_email(email):
    validate_email(email)
    return True


def validate_user_input(user: RegisterUserInput):
    if not is_valid_email(user.email):
        raise ValidationError({"message": "Invalid email"})
    if user_with_email_exists(user.email):
        raise ValidationError({"message": "Email already in use"})

    if user_with_username_exists(user.username):
        raise ValidationError({"message": "Username is in use"})

    if not is_valid_url(user.profile.website):
        raise ValidationError({"message": "Invalid url"})
    return True


def exp_date():
    return datetime.now(tz=timezone.utc) + timedelta(minutes=10)


def refresh_exp_date():
    return datetime.now(tz=timezone.utc) + timedelta(weeks=16)


def get_user(email, password):
    try:
        return models.User.objects.get(email=email, password=password)
    except ObjectDoesNotExist:
        raise ValidationError("no user exists with that email or password")


def get_user_by_id(id):
    try:
        return models.User.objects.get(id=id)
    except ObjectDoesNotExist:
        raise ValidationError("user doesnt exist")


def get_user_by_email(email):
    try:
        return models.User.objects.get(email=email)
    except ObjectDoesNotExist:
        raise ValidationError("user doesnt exist")


def get_tweet_by_id(id):
    try:
        return models.Tweet.objects.get(id=id)
    except ObjectDoesNotExist:
        raise ValidationError("tweet doesnt exist")


def get_reply_by_id(id):
    try:
        return models.Reply.objects.get(id=id)
    except ObjectDoesNotExist:
        raise ValidationError("reply doesnt exist")


def get_question_by_id(id):
    try:
        return models.Question.objects.get(id=id)
    except ObjectDoesNotExist:
        raise ValidationError("question doesnt exist")


def get_choice_by_id(id):
    try:
        return models.Choice.objects.get(id=id)
    except ObjectDoesNotExist:
        raise ValidationError("Choice doesnt exist")


def get_newsfeed_by_id(id):
    try:
        return models.NewsFeed.objects.get(id=id)
    except ObjectDoesNotExist:
        raise ValidationError("newsfeed doesnt exist")


def get_vote_by_choice(user, choice):
    try:
        return models.Vote.objects.get(user=user, choice=choice)
    except ObjectDoesNotExist:
        raise ValidationError("choice vote doesnt exist")


def get_like_by_tweet(user, tweet):
    try:
        return models.Likes.objects.get(user=user, tweet=tweet)
    except ObjectDoesNotExist:
        raise ValidationError("tweet like doesnt exist")


def get_like_by_reply(user, reply):
    try:
        return models.Likes.objects.get(user=user, reply=reply)
    except ObjectDoesNotExist:
        raise ValidationError("reply like doesnt exist")


def get_headers():
    return {"alg": "HS256", "typ": "JWT"}


def get_payload(user):
    return {"email": user.email, "iat": datetime.now(), "exp": exp_date()}


def get_refresh_payload(user):
    return {"email": user.email, "iat": datetime.now(), "exp": refresh_exp_date()}


@strawberry.type
class Query:
    users: typing.List[User] = strawberry.field(resolver=resolvers.users)
    user: User = strawberry.field(resolver=resolvers.user)
    profiles: typing.List[Profile] = strawberry.field(resolver=resolvers.profiles)
    profile: Profile = strawberry.field(resolver=resolvers.profile)
    tweets: typing.List[Tweet] = strawberry.field(resolver=resolvers.tweets)
    tweet: Tweet = strawberry.field(resolver=resolvers.tweet)
    replies: typing.List[Reply] = strawberry.field(resolver=resolvers.replies)
    reply: Reply = strawberry.field(resolver=resolvers.reply)
    questions: typing.List[Question] = strawberry.field(resolver=resolvers.questions)
    question: Question = strawberry.field(resolver=resolvers.question)
    choices: typing.List[Choice] = strawberry.field(resolver=resolvers.choices)
    choice: Choice = strawberry.field(resolver=resolvers.choice)
    newsfeeds: typing.List[NewsFeed] = strawberry.field(resolver=resolvers.newsfeeds)
    newsfeed: NewsFeed = strawberry.field(resolver=resolvers.newsfeed)
    home: Tweet = strawberry.field(resolver=resolvers.home)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def register_user(self, user: RegisterUserInput) -> User:
        if not validate_user_input(user):
            raise ValidationError("user info is not supplied correctly")
        profile_images = models.ProfileImage.objects.create(
            background_picture=user.profile.images.background_picture,
            picture=user.profile.images.picture,
        )
        profile = models.Profile.objects.create(
            website=user.profile.website,
            bio=user.profile.bio,
            locations=user.profile.locations,
            birth_date=user.profile.birth_date,
            images=profile_images,
        )
        return models.User.objects.create_user(
            username=user.username,
            email=user.email,
            password=user.password,
            profile=profile,
        )

    @strawberry.mutation
    def update_user(self, id: strawberry.ID, user: RegisterUserInput) -> User:
        validate_user_input(user)

        profile_qs = models.Profile.objects.filter(id=id)
        profile_qs.update(
            website=user.profile.website,
            bio=user.profile.bio,
            locations=user.profile.locations,
            birth_date=user.profile.birth_date,
        )
        profile = profile_qs.first()
        profile.images.background_picture = user.profile.images.background_picture
        profile.images.picture = user.profile.images.picture
        profile.images.save()
        user_qs = models.User.objects.filter(profile=profile)
        user_qs.update(
            username=user.username,
            email=user.email,
            password=user.password,
            profile=profile,
        )
        return user_qs.first()

    @strawberry.mutation
    def delete_user(self, id: strawberry.ID) -> User:
        try:
            user = get_user_by_id(id=id)
            user.delete()
            return user
        except ObjectDoesNotExist:
            raise ValidationError("user didnt exist in the first place")

    @strawberry.mutation
    def create_jwt(self, email: str, password: str) -> Token:
        user = get_user(email, password)
        token = jwt.encode(
            get_payload(user), key=settings.SECRET_KEY, algorithm="HS256"
        )
        refresh_token = jwt.encode(
            get_refresh_payload(user), key=settings.SECRET_KEY, algorithm="HS256"
        )
        return Token(
            token=token,
            refresh_token=refresh_token,
            csrf_token=create_csrf_token(),
            user=user,
        )

    @strawberry.mutation
    def refresh_jwt(self, token_input: RefreshTokenInput) -> RefreshToken:
        payload = get_payload_from_token(token_input.token)
        email = payload.get("email")
        user = get_user_by_email(email=email)
        token = jwt.encode(
            get_payload(user),
            settings.SECRET_KEY,
            algorithm="HS256",
            headers=get_headers(),
        )
        return RefreshToken(user=user, token=token)

    @strawberry.mutation
    def verify_token(self, token: str) -> VerifyToken:
        payload = jwt.decode(token, key=settings.SECRET_KEY, algorithms="HS256")
        email = payload.get("email")
        user = get_user_by_email(email=email)
        return VerifyToken(is_valid=True, user=user, payload=payload)

    @strawberry.mutation
    def change_password(self, id: strawberry.ID, password: str) -> User:
        try:
            user_qs = models.User.objects.filter(id=id)
        except ObjectDoesNotExist:
            raise ValidationError({"message": "user doesnt exist"})
        user_qs.update(password=password)
        return user_qs.first()

    @strawberry.mutation
    def deactivate_account(self, id: strawberry.ID) -> User:
        user = get_user_by_id(id)
        if not user.is_active:
            raise ValidationError({"message": "user already deactivated"})
        user.is_active = False
        user.save()
        return user

    @strawberry.mutation
    def activate_account(self, id: strawberry.ID) -> User:
        user = get_user_by_id(id)
        if user.is_active:
            raise ValidationError({"message": "user already activated"})
        user.is_active = True
        user.save()
        return user

    @strawberry.mutation
    def follow_user(self, user_id: strawberry.ID, target_id: strawberry.ID) -> User:
        user_to_follow = get_user_by_id(id=target_id)
        user = get_user_by_id(id=user_id)
        if user.following.filter(id=target_id).exists():
            raise ValidationError(f"you already follow {user_to_follow.username}")
        user.following.add(user_to_follow)
        return user

    @strawberry.mutation
    def unfollow_user(self, user_id: strawberry.ID, target_id: strawberry.ID) -> User:
        user_to_unfollow = get_user_by_id(id=target_id)
        user = get_user_by_id(id=user_id)
        if user.following.filter(id=target_id).exists():
            user.following.remove(user_to_unfollow)
            return user
        raise ValidationError(
            f"message: you already have {user_to_unfollow.username} unfollowed"
        )

    @strawberry.mutation
    def create_tweet(self, user_id: strawberry.ID, tweet_input: TweetInput) -> Tweet:
        user = get_user_by_id(id=user_id)
        question = models.Question.objects.create(
            text=tweet_input.question.text, pub_date=tweet_input.question.pub_date
        )
        models.Choice.objects.create(
            text=tweet_input.choices.choice_1, question=question
        )
        models.Choice.objects.create(
            text=tweet_input.choices.choice_2, question=question
        )
        return models.Tweet.objects.create(
            context=tweet_input.context,
            file=tweet_input.file,
            question=question,
            people_you_follow=tweet_input.people_you_follow,
            created_at=tweet_input.created_at,
            user=user,
        )

    @strawberry.mutation
    def update_tweet(self, tweet_id: strawberry.ID, tweet_input: TweetInput) -> Tweet:
        tweet_qs = models.Tweet.objects.filter(id=tweet_id)
        tweet_qs.update(
            context=tweet_input.context,
            file=tweet_input.file,
            created_at=tweet_input.created_at,
            people_you_follow=tweet_input.people_you_follow,
        )
        return tweet_qs.first()

    @strawberry.mutation
    def reply_to_tweet(
        self, id: strawberry.ID, user_id: strawberry.ID, reply_input: ReplyInput
    ) -> Reply:
        tweet = get_tweet_by_id(id=id)
        owner = get_user_by_id(id=user_id)
        if tweet.people_you_follow is True and owner not in tweet.user.following.all():
            raise ValidationError(
                "this tweet is for people who are followed by the owner"
            )
        return models.Reply.objects.create(
            context=reply_input.context,
            file=reply_input.file,
            created_at=reply_input.created_at,
            user=owner,
            tweet=tweet,
        )

    @strawberry.mutation
    def update_reply_to_tweet(
        self, reply_id: strawberry.ID, reply_input: ReplyInput
    ) -> Reply:
        reply_qs = models.Reply.objects.filter(id=reply_id)
        reply_qs.update(
            context=reply_input.context,
            file=reply_input.file,
            created_at=reply_input.created_at,
        )
        return reply_qs.first()

    @strawberry.mutation
    def retweet(self, user_id: strawberry.ID, tweet_id: strawberry.ID) -> Tweet:
        tweet = get_tweet_by_id(id=tweet_id)
        user = get_user_by_id(id=user_id)
        return models.Tweet.objects.create(
            context=tweet.context,
            file=tweet.file,
            user=user,
            created_at=tweet.created_at,
        )

    @strawberry.mutation
    def retweet_reply(self, id: strawberry.ID, user_id: strawberry.ID) -> Reply:
        reply = get_reply_by_id(id=id)
        user = get_user_by_id(id=user_id)
        return models.Tweet.objects.create(
            context=reply.context,
            file=reply.file,
            user=user,
            created_at=reply.created_at,
        )

    @strawberry.mutation
    def reply_to_reply(
        self, user_id: strawberry.ID, reply_id: strawberry.ID, reply_input: ReplyInput
    ) -> ReplyOfReply:
        reply = get_reply_by_id(id=reply_id)
        owner = get_user_by_id(id=user_id)
        return models.Reply.objects.create(
            context=reply_input.context,
            file=reply_input.file,
            user=owner,
            parent=reply,
            created_at=reply_input.created_at,
        )

    @strawberry.mutation
    def vote_choice(self, id: strawberry.ID, user_id: strawberry.ID) -> Vote:
        choice = get_choice_by_id(id=id)
        user = get_user_by_id(id=user_id)
        if choice.user_can_vote(user) is True:
            return models.Vote.objects.create(user=user, choice=choice)
        raise ValidationError("user already voted for  that choice")

    @strawberry.mutation
    def unvote_choice(self, id: strawberry.ID, user_id: strawberry.ID) -> Vote:
        choice = get_choice_by_id(id=id)
        user = get_user_by_id(id=user_id)
        if choice.user_can_vote(user) is True:
            raise ValidationError("user already unvoted that choice")
        vote = get_vote_by_choice(user=user, choice=choice)
        vote.delete()
        return vote

    @strawberry.mutation
    def like_tweet(self, id: strawberry.ID, user_id: strawberry.ID) -> Likes:
        tweet = get_tweet_by_id(id=id)
        user = get_user_by_id(id=user_id)
        if tweet.user_can_like(user) is True:
            return models.Likes.objects.create(user=user, tweet=tweet)
        raise ValidationError("user already liked that tweet")

    @strawberry.mutation
    def like_reply(self, id: strawberry.ID, user_id: strawberry.ID) -> Likes:
        reply = get_reply_by_id(id=id)
        user = get_user_by_id(id=user_id)
        if reply.user_can_like(user) is True:
            return models.Likes.objects.create(user=user, reply=reply)
        raise ValidationError("user already liked that tweet")

    @strawberry.mutation
    def dislike_tweet(self, id: strawberry.ID, user_id: strawberry.ID) -> Likes:
        tweet = get_tweet_by_id(id=id)
        user = get_user_by_id(id=user_id)
        if tweet.user_can_like(user) is True:
            raise ValidationError("user already disliked that tweet")
        like = get_like_by_tweet(user=user, tweet=tweet)
        like.delete()
        return like

    @strawberry.mutation
    def dislike_reply(self, id: strawberry.ID, user_id: strawberry.ID) -> Likes:
        reply = get_reply_by_id(id=id)
        user = get_user_by_id(id=user_id)
        if reply.user_can_like(user) is True:
            raise ValidationError("user already disliked that reply")
        like = get_like_by_reply(user=user, reply=reply)
        like.delete()
        return like

    @strawberry.mutation
    def create_newsfeed(self, news_feed_input: NewsFeedInput) -> NewsFeed:
        from_user = get_user_by_id(id=news_feed_input.from_user)
        to_user = get_user_by_id(id=news_feed_input.to_user)
        return models.NewsFeed.objects.create(
            from_user=from_user,
            to_user=to_user,
            created_at=news_feed_input.created_at,
            description=news_feed_input.description,
        )
