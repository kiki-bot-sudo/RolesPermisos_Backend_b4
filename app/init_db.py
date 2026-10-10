from .config import Settings
from .db import Base, database
from . import models

if __name__ == '__main__':
    engine, _ = database(Settings.from_env().database_url)
    Base.metadata.create_all(engine)
    engine.dispose()
    print('Base de datos inicializada.')
