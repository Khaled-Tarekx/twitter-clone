from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Tweet, Reply, NewsFeed
from .graphql.schema import get_user_by_id


@receiver(post_save, sender=Tweet)
def create_newsfeed_for_tweet(sender, instance, created, **kwargs):
    if created:
        from_user_id = instance.user.id
        data = instance.context
        text = data[:30]
        from_user = get_user_by_id(id=from_user_id)
        description = f"{from_user} tweeted {text}..."
        NewsFeed.objects.create(from_user=from_user, description=description)


@receiver(post_save, sender=Reply)
def create_newsfeed_for_reply(sender, instance, created, **kwargs):
    if created:
        from_user_id = instance.user.id
        data = instance.context
        text = data[:30]
        from_user = get_user_by_id(id=from_user_id)
        description = f"{from_user} replied with {text}..."
        if instance.parent is not None:
            to_user_id = instance.parent.user.id
            to_user = get_user_by_id(id=to_user_id)
            description = f"{from_user} replied with {text} to {to_user}..."
            NewsFeed.objects.create(
                from_user=from_user, description=description, to_user=to_user
            )
        else:
            NewsFeed.objects.create(from_user=from_user, description=description)


# @receiver(post_save, sender=Question)
# def create_newsfeed_for_question(sender, instance, created, **kwargs):
#     if created:
#         from_user_id = instance.tweet.user.id
#         from_user = get_user_by_id(id=from_user_id)
#         data = instance.text
#         text = data[:30]
#         description = f'{from_user} created poll question > {text}'
#         NewsFeed.objects.create(from_user=from_user, description=description)
