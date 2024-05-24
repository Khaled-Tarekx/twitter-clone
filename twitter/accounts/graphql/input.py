import typing
import strawberry
from django.utils import timezone
from strawberry.file_uploads import Upload


@strawberry.input
class ProfileImageInput:
    picture: str
    background_picture: str


@strawberry.input
class ProfileInput:
    images: ProfileImageInput
    bio: str
    locations: str
    website: str
    birth_date: str


@strawberry.input
class RegisterUserInput:
    username: str
    email: str
    password: str
    profile: ProfileInput


@strawberry.input
class RefreshTokenInput:
    token: str
    csrf_token: str


@strawberry.input
class ReplyInput:
    context: str
    file: typing.Optional[Upload] = "9.jpg"
    created_at: str = timezone.now()


@strawberry.input
class QuestionInput:
    text: typing.Optional[str]
    pub_date: str = timezone.now()


@strawberry.input
class ChoiceInput:
    choice_1: typing.Optional[str]
    choice_2: typing.Optional[str]


@strawberry.input
class TweetInput:
    context: str
    question: typing.Optional[QuestionInput]
    choices: typing.Optional[ChoiceInput]
    created_at: str = timezone.now()
    people_you_follow: bool = False
    file: typing.Optional[Upload] = "9.jpg"


@strawberry.input
class NewsFeedInput:
    from_user: strawberry.ID
    description: str
    to_user: strawberry.ID
    created_at: str = timezone.now()
