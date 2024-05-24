import logging
from rest_framework import status, generics
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    ActivateAccountSerializer,
    DeActivateAccountSerializer,
    LikeSerializer,
    ReTweetOutSerializer,
    ReTweetReplySerializer,
    ReTweetSerializer,
    SocialSerializer,
    TwilioEmail2Serializer,
    TwilioEmail3Serializer,
    TwilioEmailSerializer,
    TwilioMessageSerializer,
    UnLikeSerializer,
    UnVoteSerializer,
    UserSerializer,
    ProfileSerializer,
    TweetSerializer,
    TweetOutSerializer,
    ReplySerializer,
    ReplyOutSerializer,
    NewsFeedSerializer,
    NewsFeedOutSerializer,
    ChoiceOutSerializer,
    ChoiceQSerializer,
    QuestionSerializer,
    UserUnFollowSerializer,
    UserFollowSerializer,
    MyTokenObtainPairSerializer,
    ChangePasswordSerializer,
    LikeTweetOutSerializer,
    LikeReplyOutSerializer,
    VoteOutSerializer,
    VoteSerializer,
)
from django.conf import settings
from requests.exceptions import HTTPError
from social_django.utils import psa
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from ..models import (
    Profile,
    User,
    Tweet,
    Reply,
    NewsFeed,
    Choice,
    Question,
    Likes,
    Vote,
)


class MyObtainTokenPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class ProfileViewSet(ModelViewSet):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    authentication_classes = []


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()


class TweetViewSet(ModelViewSet):
    serializer_class = TweetSerializer
    queryset = Tweet.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = serializer.save()
        headers = self.get_success_headers(serializer.data)
        tweet_serializer = TweetOutSerializer(saved)
        return Response(
            tweet_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ReplyViewSet(ModelViewSet):
    serializer_class = ReplySerializer
    queryset = Reply.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = serializer.save()
        headers = self.get_success_headers(serializer.data)
        reply_serializer = ReplyOutSerializer(saved)
        return Response(
            reply_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class NewsFeedViewSet(ModelViewSet):
    serializer_class = NewsFeedSerializer
    queryset = NewsFeed.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = serializer.save()
        headers = self.get_success_headers(serializer.data)
        newsfeed_serializer = NewsFeedOutSerializer(saved)
        return Response(
            newsfeed_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ChoiceViewSet(ModelViewSet):
    serializer_class = ChoiceQSerializer
    queryset = Choice.objects.all()
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        saved = serializer.save()
        headers = self.get_success_headers(serializer.data)
        choice_serializer = ChoiceOutSerializer(saved)
        return Response(
            choice_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class QuestionViewSet(ModelViewSet):
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()
    permission_classes = (IsAuthenticated,)


class UserFollowView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserFollowSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        user = self.get_object()
        user_serializer = UserSerializer(user)
        return Response(
            user_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class UserUnFollowView(UserFollowView):
    queryset = User.objects.all()
    serializer_class = UserUnFollowSerializer
    permission_classes = (IsAuthenticated,)


class ChangePasswordsView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)


class UserLikeTweetView(CreateAPIView):
    queryset = Likes.objects.all()
    serializer_class = LikeSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        like = Likes.objects.get(tweet_id=serializer.data["tweet"])
        likes_serializer = LikeTweetOutSerializer(like)
        return Response(
            likes_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class UserLikeReplyView(CreateAPIView):
    queryset = Likes.objects.all()
    serializer_class = LikeSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        like = Likes.objects.get(reply=serializer.data["reply"])
        likes_serializer = LikeReplyOutSerializer(like)
        return Response(
            likes_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class UserUnLikeTweetView(DestroyAPIView):
    queryset = Likes.objects.all()
    serializer_class = UnLikeSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "tweet_id"


class LikesView(ListAPIView):
    queryset = Likes.objects.all()
    serializer_class = LikeSerializer
    permission_classes = (IsAuthenticated,)


class UserUnLikeReplyView(DestroyAPIView):
    serializer_class = UnLikeSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Likes.objects.all()
    lookup_field = "reply_id"


class ListVoteView(ListAPIView):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = (IsAuthenticated,)


class VoteView(CreateAPIView):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "choice_id"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        vote = Vote.objects.get(choice=serializer.data["choice"])
        vote_serializer = VoteOutSerializer(vote)
        return Response(
            vote_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class UnVoteView(DestroyAPIView):
    queryset = Vote.objects.all()
    serializer_class = UnVoteSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "choice_id"


class ActivateAccountView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = ActivateAccountSerializer


class DeActivateAccountView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = DeActivateAccountSerializer
    permission_classes = (IsAuthenticated,)


class ReTweetView(CreateAPIView):
    queryset = Tweet.objects.all()
    serializer_class = ReTweetSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        tweet = Tweet.objects.get(id=serializer.data["id"])
        tweet_serializer = ReTweetOutSerializer(tweet)
        return Response(
            tweet_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class ReTweetReplyView(CreateAPIView):
    queryset = Tweet.objects.all()
    serializer_class = ReTweetReplySerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        headers = self.get_success_headers(serializer.data)
        tweet = Tweet.objects.get(id=serializer.data["id"])
        retweet_reply_serializer = ReplyOutSerializer(tweet)
        return Response(
            retweet_reply_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class TwilioMessagesView(CreateAPIView):
    serializer_class = TwilioMessageSerializer
    permission_classes = (IsAuthenticated,)


class TwilioEmailsView(CreateAPIView):
    serializer_class = TwilioEmailSerializer
    permission_classes = (IsAuthenticated,)

class TwilioEmails2View(CreateAPIView):
    serializer_class = TwilioEmail2Serializer
    permission_classes = (IsAuthenticated,)
    
class TwilioEmails3View(CreateAPIView):
    serializer_class = TwilioEmail3Serializer
    permission_classes = (IsAuthenticated,)
    

@api_view(http_method_names=["POST"])
@permission_classes([AllowAny])
@psa()
def exchange_token(request, backend):
    serializer = SocialSerializer(data=request.data)
    if serializer.is_valid(raise_exception=True):
        try:
            nfe = settings.NON_FIELD_ERRORS_KEY
        except AttributeError:
            nfe = "non_field_errors"
        try:
            user = request.backend.do_auth(serializer.validated_data["access_token"])
        except HTTPError as e:
           
            return Response(
                {
                    "errors": {
                        "token": "Invalid token",
                        "detail": str(e),
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user:
            if user.is_active:
                token, _ = Token.objects.get_or_create(user=user)
                return Response({"token": token.key})
            else:
                return Response(
                    {"errors": {nfe: "This user account is inactive"}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"errors": {nfe: "Authentication Failed"}},
                status=status.HTTP_400_BAD_REQUEST,
            )
