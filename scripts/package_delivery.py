"""Empaqueta solo archivos de entrega y verifica integridad y exclusión de secretos."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'entrega'
PREFIX = 'Actividad4_Finanzas'


def main():
    files = [ROOT / name for name in (
        'ENTREGA.md', 'README.md', 'requirements.txt', 'schema.graphql',
        '.env.example', '.gitignore')]
    for directory in ('app', 'tests', 'scripts', 'docs'):
        files.extend(path for path in (ROOT / directory).rglob('*')
                     if path.is_file() and '__pycache__' not in path.parts
                     and path.suffix in {'.py', '.md', '.graphql', '.json', '.txt', '.xml'})
    files = sorted(set(files))
    # Se comparan los secretos locales sin imprimirlos ni incorporarlos al manifiesto.
    secrets = []
    configuration = ROOT / '.env'
    if configuration.exists():
        for line in configuration.read_text(encoding='utf-8-sig').splitlines():
            key, _, value = line.partition('=')
            if key.strip() in {'JWT_SECRET', 'BOOTSTRAP_KEY'} and value.strip():
                secrets.append(value.strip().strip('\"\'').encode())
    credentials = ROOT / '.demo-credentials.json'
    if credentials.exists():
        secrets.append(json.loads(credentials.read_text(encoding='utf-8'))['password'].encode())

    payloads = {}
    for path in files:
        data = path.read_bytes()
        if any(secret in data for secret in secrets):
            raise RuntimeError(f'Secreto local detectado en {path.relative_to(ROOT)}; no se empaquetó.')
        payloads[f'{PREFIX}/{path.relative_to(ROOT).as_posix()}'] = data
    OUTPUT.mkdir(exist_ok=True)
    archive = OUTPUT / f'{PREFIX}.zip'
    with ZipFile(archive, 'w', ZIP_DEFLATED) as zipped:
        for name, data in payloads.items():
            zipped.writestr(name, data)
    with ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert set(zipped.namelist()) == set(payloads)
        for name, expected in payloads.items():
            assert zipped.read(name) == expected
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (OUTPUT / f'{PREFIX}.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='utf-8')
    print(f'ZIP verificado: {archive}')
    print(f'Archivos: {len(files)}. Tamaño: {archive.stat().st_size} bytes.')
    print('Sin secretos locales, bases de datos, entornos virtuales ni cachés.')


if __name__ == '__main__':
    main()
