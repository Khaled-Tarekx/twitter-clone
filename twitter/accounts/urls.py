from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from .rest.views import (
    ListVoteView,
    TweetViewSet,
    TwilioEmails2View,
    TwilioEmails3View,
    TwilioEmailsView,
    TwilioMessagesView,
    UnVoteView,
    UserUnLikeReplyView,
    UserUnLikeTweetView,
    UserViewSet,
    ProfileViewSet,
    NewsFeedViewSet,
    ReplyViewSet,
    ChoiceViewSet,
    QuestionViewSet,
    UserFollowView,
    UserUnFollowView,
    MyObtainTokenPairView,
    ChangePasswordsView,
    UserLikeTweetView,
    UserLikeReplyView,
    VoteView,
    LikesView,
    DeActivateAccountView,
    ActivateAccountView,
    ReTweetReplyView,
    ReTweetView,
    exchange_token,
)

router = DefaultRouter()

router.register(r"tweets", TweetViewSet, basename="tweet")
router.register(r"users", UserViewSet, basename="user")
router.register(r"profiles", ProfileViewSet, basename="profile")
router.register(r"newsfeeds", NewsFeedViewSet, basename="newsfeed")
router.register(r"replies", ReplyViewSet, basename="reply")
router.register(r"choices", ChoiceViewSet, basename="choice")
router.register(r"questions", QuestionViewSet, basename="question")


urlpatterns = [
    path("", include(router.urls)),
    path("follow-user/<int:pk>/", view=UserFollowView.as_view()),
    path("unfollow-user/<int:pk>/", view=UserUnFollowView.as_view()),
    path("change-password/<int:pk>/", view=ChangePasswordsView.as_view()),
    path("retweet/<int:pk>/", view=ReTweetView.as_view()),
    path("retweet-reply/<int:pk>/", view=ReTweetReplyView.as_view()),
    path("activate-account/", view=ActivateAccountView.as_view()),
    path("deactivate-account/", view=DeActivateAccountView.as_view()),
    path("tweets/like/<int:pk>/", view=UserLikeTweetView.as_view()),
    path("replies/like/<int:pk>/", view=UserLikeReplyView.as_view()),
    path("tweets/unlike/<int:tweet_id>/", view=UserUnLikeTweetView.as_view()),
    path("replies/unlike/<int:reply_id>/", view=UserUnLikeReplyView.as_view()),
    path("votes/", view=ListVoteView.as_view()),
    path("likes/", view=LikesView.as_view()),
    path("choices/vote/<int:choice_id>/", view=VoteView.as_view()),
    path("choices/unvote/<int:choice_id>/", view=UnVoteView.as_view()),
    path("twilio/message/", view=TwilioMessagesView.as_view(), name="send_message"),
    path("twilio/email/", view=TwilioEmailsView.as_view(), name="send_email"),
    path("twilio/email/v2/", view=TwilioEmails2View.as_view(), name="send_email_v2"),
    path("twilio/email/v3/", view=TwilioEmails3View.as_view(), name="send_email_v3"),
    path("api/token/", view=MyObtainTokenPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", view=TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", view=TokenVerifyView.as_view(), name="token_verify"),
    path("api/exchange-token/", view=exchange_token, name="exchange_token"),
]
