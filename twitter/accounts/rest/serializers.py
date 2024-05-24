import os
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from ..graphql.schema import get_like_by_reply, get_tweet_by_id, get_user_by_id
from ..models import (
    User,
    Tweet,
    Reply,
    Question,
    Choice,
    Profile,
    ProfileImage,
    Likes,
    Vote,
    NewsFeed,
)
import logging
from twilio.rest import Client
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
from django.core.mail import send_mail

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super(MyTokenObtainPairSerializer, cls).get_token(user)
        token["username"] = user.username
        return token


class ProfileImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileImage
        fields = ["id", "background_picture", "picture"]


class ProfileSerializer(serializers.ModelSerializer):
    images = ProfileImageSerializer()

    class Meta:
        model = Profile
        fields = ["id", "bio", "locations", "website", "birth_date", "images"]

    def create(self, validated_data):
        images_data = validated_data.pop("images")
        images = ProfileImage.objects.create(**images_data)
        return Profile.objects.create(**validated_data, images=images)


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    followers = serializers.SlugRelatedField(
        read_only=True,
        many=True,
        slug_field="username",
    )
    following = serializers.SlugRelatedField(
        read_only=True,
        many=True,
        slug_field="username",
    )

    class Meta:
        model = User
        fields = [
            "id",
            "is_online",
            "profile",
            "password",
            "username",
            "followers",
            "following",
            "email",
            "is_active",
            "created_at",
            "updated_at",
        ]

        extra_kwargs = {
            "password": {"write_only": True},
            "followers": {"read_only": True},
            "is_online": {"read_only": True},
            "following": {"read_only": True},
        }

    def create(self, validated_data):
        profile_data = validated_data.pop("profile")
        images_data = profile_data.pop("images")
        images = ProfileImage.objects.create(**images_data)
        profile = Profile.objects.create(**profile_data, images=images)
        return User.objects.create(**validated_data, profile=profile)


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "text", "pub_date"]

        extra_kwargs = {"text": {"required": False}}


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text"]


class ChoiceQSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())

    class Meta:
        model = Choice
        fields = ["id", "question", "text"]

    def create(self, validated_data):
        question = validated_data.pop("question")
        return Choice.objects.create(**validated_data, question=question)


class ChoiceOutSerializer(serializers.ModelSerializer):
    question = serializers.SlugRelatedField(read_only=True, slug_field="text")

    class Meta:
        model = Choice
        fields = ["id", "text", "question"]


# class LikeTweetSerializer(serializers.ModelSerializer):
#     tweet = serializers.PrimaryKeyRelatedField(
#         queryset=Tweet.objects.all()
#     )

#     class Meta:
#         model = Likes
#         fields = ["id", "user", "tweet"]

#     def create(self, validated_data):
#         user = self.context['request'].user
#         tweet = validated_data['tweet']
#         if tweet.user_can_like(user) is True:
#             return Likes.objects.create(user=user, tweet=tweet)
#         raise ValidationError("user already liked that tweet")


class LikeTweetOutSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field="username")
    tweet = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Likes
        fields = ["id", "user", "tweet"]


class LikeReplyOutSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field="username")
    reply = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Likes
        fields = ["id", "user", "reply"]


class TweetSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    question = QuestionSerializer(required=False)
    choices = ChoiceSerializer(required=False, many=True)

    class Meta:
        model = Tweet
        fields = [
            "id",
            "context",
            "created_at",
            "updated_at",
            "choices",
            "file",
            "user",
            "people_you_follow",
            "question",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["likes"] = instance.get_likes_count
        return representation

    def create(self, validated_data):
        user = validated_data.pop("user")
        try:
            question_data = validated_data.pop("question")
            question = Question.objects.create(**question_data)
            choice_data = validated_data.pop("choices")
        except KeyError:
            return Tweet.objects.create(**validated_data, user=user)
        for data in choice_data:
            Choice.objects.create(**data, question=question)
        return Tweet.objects.create(**validated_data, user=user, question=question)


class TweetOutSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    question = QuestionSerializer(read_only=True)
    choice = ChoiceOutSerializer(read_only=True)
    likes = serializers.SlugRelatedField(many=True, read_only=True, slug_field="user")

    class Meta:
        model = Tweet
        fields = [
            "id",
            "context",
            "created_at",
            "updated_at",
            "choice",
            "file",
            "user",
            "likes",
            "people_you_follow",
            "question",
        ]


class ReplySerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Reply.objects.all(), required=False
    )
    tweet = serializers.PrimaryKeyRelatedField(queryset=Tweet.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Reply
        fields = [
            "id",
            "context",
            "created_at",
            "updated_at",
            "parent",
            "tweet",
            "user",
            "file",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["likes"] = instance.get_likes_count
        return representation

    def create(self, validated_data):
        tweet = validated_data.get("tweet")
        user = validated_data.get("user")
        tweet = get_tweet_by_id(id=tweet.id)
        reply_owner = get_user_by_id(id=user.id)
        if (
            tweet.people_you_follow is True
            and reply_owner not in tweet.user.following.all()
        ):
            raise ValidationError(
                "this tweet is for people who are followed by the owner"
            )
        return Reply.objects.create(**validated_data)


class ReplyOutSerializer(serializers.ModelSerializer):
    parent = serializers.SlugRelatedField(read_only=True, slug_field="context")
    tweet = serializers.SlugRelatedField(read_only=True, slug_field="context")
    user = serializers.SlugRelatedField(read_only=True, slug_field="username")
    likes = serializers.SlugRelatedField(many=True, read_only=True, slug_field="user")

    class Meta:
        model = Reply
        fields = [
            "id",
            "context",
            "created_at",
            "updated_at",
            "parent",
            "likes",
            "tweet",
            "user",
            "file",
        ]


class NewsFeedSerializer(serializers.ModelSerializer):
    from_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    to_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False
    )

    class Meta:
        model = NewsFeed
        fields = ["id", "from_user", "created_at", "description", "to_user"]


class NewsFeedOutSerializer(serializers.ModelSerializer):
    from_user = serializers.SlugRelatedField(read_only=True, slug_field="username")
    to_user = serializers.SlugRelatedField(
        read_only=True, slug_field="username", required=False
    )

    class Meta:
        model = NewsFeed
        fields = ["id", "from_user", "created_at", "description", "is_read", "to_user"]


class VoteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), required=False
    )
    choice = serializers.PrimaryKeyRelatedField(queryset=Choice.objects.all())

    class Meta:
        model = Vote
        fields = ["id", "user", "choice"]

    def create(self, validated_data):
        user = self.context["request"].user
        choice = validated_data["choice"]
        if choice.user_can_vote(user) is True:
            return Vote.objects.create(user=user, choice=choice)
        raise ValidationError("you already voted for that choice")


class UnVoteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    choice = serializers.PrimaryKeyRelatedField(queryset=Choice.objects.all())

    class Meta:
        model = Vote
        fields = ["id", "user", "choice"]


class VoteOutSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(read_only=True, slug_field="username")
    choice = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Vote
        fields = ["id", "user", "choice"]


class UserFollowSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def create(self, validated_data):
        user = self.context["request"].user
        user_to_follow = validated_data.get("id")
        if user.following.filter(id=user_to_follow.id).exists():
            raise ValidationError(
                f"message: you already have {user_to_follow.username} followed"
            )
        user.following.add(user_to_follow)
        return validated_data


class UserUnFollowSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def create(self, validated_data):
        user = self.context["request"].user
        user_to_unfollow = validated_data.get("id")
        if user.following.filter(id=user_to_unfollow.id).exists():
            user.following.remove(user_to_unfollow)
            return validated_data
        raise ValidationError(
            f"message: you already have {user_to_unfollow.username} unfollowed"
        )


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("old_password", "password", "password2")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                {"old_password": "Old password is not correct"}
            )
        return value

    def update(self, instance, validated_data):
        user = self.context["request"].user
        if user.pk != instance.pk:
            raise serializers.ValidationError(
                {"authorize": "You dont have permission for this user."}
            )
        instance.set_password(validated_data["password"])
        instance.save()
        return instance


class ReTweetSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Tweet.objects.all())

    def create(self, validated_data):
        user = self.context["request"].user
        try:
            tweet = validated_data["id"]
        except:
            ValidationError("couldnt find a tweet with that id")
        return Tweet.objects.create(
            context=tweet.context,
            file=tweet.file,
            user=user,
            created_at=tweet.created_at,
        )


class ReTweetReplySerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Reply.objects.all())

    def create(self, validated_data):
        user = self.context["request"].user
        try:
            reply = validated_data["id"]
        except:
            ValidationError("couldnt find a reply with that id")
        return Tweet.objects.create(
            context=reply.context,
            file=reply.file,
            user=user,
            created_at=reply.created_at,
        )


class DeActivateAccountSerializer(serializers.Serializer):
    def create(self, validated_data):
        user = self.context["request"].user
        if not user.is_active:
            raise ValidationError({"message": "user already deactivated"})
        user.is_active = False
        user.save()
        return user


class ActivateAccountSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def create(self, validated_data):
        user = validated_data["id"]
        if user.is_active:
            raise ValidationError({"message": "user already activated"})
        user.is_active = True
        user.save()
        return user


class ReTweetOutSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    question = QuestionSerializer(read_only=True)
    choice = ChoiceOutSerializer(read_only=True)

    class Meta:
        model = Tweet
        fields = [
            "id",
            "context",
            "created_at",
            "updated_at",
            "choice",
            "file",
            "user",
            "people_you_follow",
            "question",
        ]


class DisLikeReplySerializer(serializers.ModelSerializer):
    reply = serializers.PrimaryKeyRelatedField(queryset=Reply.objects.all())

    class Meta:
        model = Likes
        fields = ["id", "user", "reply"]

    def create(self, validated_data):
        user = self.context["request"].user
        reply = validated_data["reply"]
        if reply.user_can_like(user) is True:
            raise ValidationError("user already disliked that reply")
        like = get_like_by_reply(user=user, reply=reply)
        return like.delete()


class LikeSerializer(serializers.ModelSerializer):
    reply = serializers.PrimaryKeyRelatedField(
        queryset=Reply.objects.all(), required=False
    )
    tweet = serializers.PrimaryKeyRelatedField(
        queryset=Tweet.objects.all(), required=False
    )

    class Meta:
        model = Likes
        fields = ["id", "user", "reply", "tweet"]

        extra_kwargs = {"user": {"required": False}}

    def create(self, validated_data):
        user = self.context["request"].user
        try:
            reply = validated_data.get("reply")
            tweet = validated_data.get("tweet")
            if reply and reply.user_can_like(user) is True:
                return Likes.objects.create(user=user, reply=reply)
        except:
            raise ValidationError("user already liked that reply")
        if tweet and tweet.user_can_like(user) is True:
            return Likes.objects.create(user=user, tweet=tweet)
        raise ValidationError("user already liked that tweet")


class UnLikeSerializer(serializers.ModelSerializer):
    tweet = serializers.PrimaryKeyRelatedField(
        queryset=Tweet.objects.all(), required=False
    )
    reply = serializers.PrimaryKeyRelatedField(
        queryset=Reply.objects.all(), required=False
    )

    class Meta:
        model = Likes
        fields = ["id", "user", "tweet", "reply"]

    # def create(self, validated_data):
    #     user = self.context['request'].user
    #     try:
    #         tweet = validated_data.get('tweet')
    #         reply = validated_data.get('reply')
    #         if tweet and tweet.user_can_like(user) is True:
    #             raise ValidationError("user already disliked or didnt like this tweet")
    #         like = Likes.objects.get(tweet__id=tweet.id)
    #         like.delete()
    #         return like
    #     except:
    #         pass
    #     if reply and reply.user_can_like(user) is True:
    #         raise ValidationError("user already disliked or didnt like this reply")
    #     try:
    #         like = Likes.objects.get(reply_id=reply.id)
    #         like.delete()
    #         return like
    #     except:
    #         pass


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


client = Client(settings.ACCOUNTSID, settings.AUTHTOKEN)


class TwilioMessageSerializer(serializers.Serializer):
    body = serializers.CharField()
    to = serializers.CharField()

    def create(self, validated_data):
        phone_number = settings.TWILIOPHONENUMBER
        try:
            client.messages.create(
            body=validated_data.get("body"),
            messaging_service_sid=os.getenv("messaging_service_sid"),
            from_=phone_number,
            to=validated_data.get("to"),
        )
        except Exception as e:
            raise ValidationError(e)


class TwilioEmailSerializer(serializers.Serializer):
    content = serializers.CharField()
    to_emails = serializers.ListSerializer(child=serializers.EmailField())
    from_email = serializers.EmailField()
    subject = serializers.CharField()
    mime_type = serializers.CharField()
    def create(self, validated_data):
        try:
            sg = SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
            from_email = Email(email=validated_data["from_email"]),
            to_emails = To(validated_data["to_emails"]),
            subject = Subject(validated_data["subject"]),
            content = Content(validated_data["mime_type"], validated_data["content"])

            mail = Mail(from_email, to_emails, subject, content)
            mail_json = mail.get()
            return sg.client.mail.send.post(request_body=mail_json)
        except Exception as e:
            raise ValidationError(e)
        
        
class TwilioEmail2Serializer(serializers.Serializer):
    content = serializers.CharField()
    to_emails = serializers.ListSerializer(child=serializers.EmailField())
    subject = serializers.CharField()
    mime_type = serializers.CharField()
    def create(self, validated_data):
        try:
            message = Mail()
            message.to = [
            To(
        email=validated_data["to_emails"],
        p=0
        )
    ]
            message.from_email = From(
            email=settings.FROM_EMAIL_SENDGRID,
            name="KhaledTarek",
            p=1,
        )
            message.subject = Subject(validated_data["subject"])

            message.content = [
        Content(
            mime_type=validated_data["mime_type"],
            content=validated_data["content"]
        )
    ]
            sendgrid_client = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
            return sendgrid_client.send(message)
        except Exception as e:
            raise ValidationError(e)

class TwilioEmail3Serializer(serializers.Serializer): # working but api doesnt cus sender isnt verifed
    message = serializers.CharField()
    to_emails = serializers.ListSerializer(child=serializers.EmailField())
    subject = serializers.CharField()
    def create(self, validated_data):
        try:
            return send_mail(subject=validated_data['subject'], message=validated_data['message'],
                            from_email=settings.FROM_EMAIL_SENDGRID, recipient_list=validated_data["to_emails"], fail_silently=False)
        except Exception as e:
            raise ValidationError(e)