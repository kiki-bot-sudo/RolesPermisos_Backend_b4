"""Ejecuta las pruebas de roles en una base MySQL desechable, separada de ingresos."""
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


def main():
    env = dotenv_values('.env.docker')
    name = 'test_roles_' + uuid4().hex[:12]
    # El usuario raíz solo se usa para crear/eliminar esta base aislada.
    root_url = URL.create('mysql+pymysql', username='root', password=env['MYSQL_ROOT_PASSWORD'],
                          host='127.0.0.1', port=3307)
    engine = create_engine(root_url)
    output = Path('docs/evidencias/roles')
    output.mkdir(parents=True, exist_ok=True)
    try:
        with engine.begin() as db:
            db.execute(text(f'CREATE DATABASE `{name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_bin'))
            db.execute(text(f"GRANT ALL PRIVILEGES ON `{name}`.* TO '{env['MYSQL_USER']}'@'%'") )
        url = URL.create('mysql+pymysql', username=env['MYSQL_USER'], password=env['MYSQL_PASSWORD'],
                         host='127.0.0.1', port=3307, database=name, query={'charset': 'utf8mb4'})
        process_env = {**os.environ, 'MYSQL_TEST_DATABASE_URL': url.render_as_string(hide_password=False)}
        result = subprocess.run([sys.executable, '-m', 'pytest', 'tests/test_roles.py', '-v', '--tb=short',
                                 '--junitxml=docs/evidencias/roles/mysql-junit.xml'],
                                env=process_env, capture_output=True, text=True, encoding='utf-8', errors='replace')
        output.joinpath('mysql-pytest.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        print(result.stdout)
        return result.returncode
    finally:
        assert name.startswith('test_roles_') and len(name) == 23
        with engine.begin() as db:
            db.execute(text(f'DROP DATABASE IF EXISTS `{name}`'))
        engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
