"""Genera configuración independiente para MySQL/Docker sin alterar el .env local."""
import secrets
from pathlib import Path


if __name__ == '__main__':
    target = Path('.env.docker')
    with target.open('x', encoding='utf-8') as file:
        file.write('MYSQL_DATABASE=ingresos\nMYSQL_USER=ingresos\n'
                   f'MYSQL_PASSWORD={secrets.token_urlsafe(32)}\n'
                   f'MYSQL_ROOT_PASSWORD={secrets.token_urlsafe(32)}\n'
                   f'JWT_SECRET={secrets.token_urlsafe(48)}\n'
                   f'BOOTSTRAP_KEY={secrets.token_urlsafe(48)}\n')
    print('.env.docker creado; no compartir ni versionar.')
