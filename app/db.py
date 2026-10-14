from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def database(url):
    sqlite = url.startswith('sqlite:')
    options = {} if sqlite else {'isolation_level': 'READ COMMITTED'}
    engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': 30} if sqlite else {},
                           pool_pre_ping=True, **options)

    @event.listens_for(engine, 'connect')
    def configure(connection, _):
        if sqlite:
            connection.execute('PRAGMA foreign_keys=ON')

    return engine, sessionmaker(engine, expire_on_commit=False)


def serialize_write(session):
    if session.bind.dialect.name == 'sqlite':
        session.execute(text('BEGIN IMMEDIATE'))
