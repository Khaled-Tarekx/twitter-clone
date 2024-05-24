import logging
import typing
from strawberry.schema.types.base_scalars import Date
import strawberry
from strawberry.scalars import JSON


@strawberry.type
class Image:
    url: str
    path: str


@strawberry.type
class ProfileImage:
    id: strawberry.ID
    picture: Image
    background_picture: Image


@strawberry.type
class Profile:
    id: strawberry.ID
    images: ProfileImage
    bio: str
    locations: str
    website: str
    birth_date: str


@strawberry.type
class Likes:
    id: typing.Optional[strawberry.ID]
    user: "User"
    tweet: typing.Optional["Tweet"]
    reply: typing.Optional["Reply"]


@strawberry.type
class Vote:
    id: typing.Optional[strawberry.ID]
    user: "User"
    choice: "Choice"


@strawberry.type
class Choice:
    id: strawberry.ID
    text: str

    @strawberry.field
    def votes(self) -> int:
        return self.get_vote_count


@strawberry.type
class Question:
    id: strawberry.ID
    text: str
    pub_date: str

    @strawberry.field
    def _choices(self) -> typing.List[Choice]:
        return self.choices.all()


@strawberry.type
class Followers:
    id: strawberry.ID
    username: str
    email: str
    is_active: bool


@strawberry.type
class ReplyOfReply:
    id: strawberry.ID
    context: str
    updated_at: str
    created_at: str

    @strawberry.field
    def owner(self) -> str:
        return self.user

    @strawberry.field
    def file(self) -> typing.Optional[str]:
        return self.file.path

    @strawberry.field
    def likes(self) -> int:
        return self.get_likes_count


@strawberry.type
class Reply:
    id: strawberry.ID
    context: str
    updated_at: Date
    created_at: str

    @strawberry.field
    def reply_of_reply(self) -> typing.List[ReplyOfReply]:
        return self.get_descendants(include_self=False)

    @strawberry.field
    def owner(self) -> str:
        return self.user

    @strawberry.field
    def likes(self) -> int:
        return self.get_likes_count

    @strawberry.field
    def file(self) -> typing.Optional[str]:
        return self.file.path


@strawberry.type
class Tweet:
    id: strawberry.ID
    context: str
    updated_at: Date
    created_at: str
    people_you_follow: bool

    @strawberry.field
    def reply_count(self) -> int:
        return self.replies.count()

    @strawberry.field
    def replies(self) -> typing.List[Reply]:
        return self.replies.all()

    @strawberry.field
    def owner(self) -> str:
        return self.user.username

    @strawberry.field
    def file(self) -> typing.Optional[str]:
        return self.file.path

    @strawberry.field
    def _question(self) -> typing.Optional[Question]:
        return self.question

    @strawberry.field
    def likes(self) -> int:
        return self.get_likes_count


@strawberry.type
class User:
    id: typing.Optional[strawberry.ID]
    username: str
    email: str
    profile: Profile
    is_active: bool

    @strawberry.field
    def followers_count(self) -> int:
        return self.followers.count()

    @strawberry.field
    def following_count(self) -> int:
        return self.following.count()

    @strawberry.field
    def followers(self) -> typing.List[Followers]:
        return self.followers.all()

    @strawberry.field
    def following(self) -> typing.List[Followers]:
        return self.following.all()

    @strawberry.field
    def tweet_count(self) -> int:
        return self.tweets.count()

    @strawberry.field
    def all_tweets(self) -> typing.List[Tweet]:
        return self.tweets.all()

    @strawberry.field
    def home_tweets(self) -> typing.List[Tweet]:
        return self.tweets.filter(user__following=self.id)


@strawberry.type
class Token:
    token: str
    refresh_token: str
    csrf_token: str
    user: User


@strawberry.type
class RefreshToken:
    token: str
    user: User


@strawberry.type
class VerifyToken:
    user: User
    payload: JSON
    is_valid: bool = False


@strawberry.type
class NewsFeed:
    id: strawberry.ID
    from_user: User
    description: str
    created_at: str
    to_user: typing.Optional[User]
