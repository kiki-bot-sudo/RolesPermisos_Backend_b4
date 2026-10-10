from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from .config import Settings
from .db import Base, database
from .schema import schema


def create_app(settings: Settings):
    app = FastAPI(title='Actividades 3 y 4: Empresas y finanzas', debug=False)
    engine, sessions = database(settings.database_url)
    Base.metadata.create_all(engine)
    app.state.engine, app.state.sessions, app.state.settings = engine, sessions, settings
    app.include_router(GraphQLRouter(schema, graphql_ide='graphiql'), prefix='/graphql')
    return app
