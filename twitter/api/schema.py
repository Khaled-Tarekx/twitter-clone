import strawberry
from accounts.graphql.schema import Query as AccountQuery
from accounts.graphql.schema import Mutation as AccountMutation


@strawberry.type
class Query(AccountQuery):
    pass


@strawberry.type
class Mutation(AccountMutation):
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)
