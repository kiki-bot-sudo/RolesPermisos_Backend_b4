"""Ejecuta las cuatro partes por HTTP y comprueba persistencia en MySQL o SQLite.

Uso: python scripts/demo_roles.py --docker (API 8008, MySQL 3307)
     python scripts/demo_roles.py (API 8000, .env local)
Los tokens y contraseñas nunca se guardan en las evidencias.
"""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from uuid import uuid4
from graphql import parse, print_ast
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from dotenv import dotenv_values
from sqlalchemy import select, func, text
from app import models as m
from app.config import Settings
from app.db import database
from app.seed_roles import seed, credentials
from app.role_catalog import DEFAULTS

SELECT_FINAL = '''SELECT r.code AS rol, p.code AS permiso, rp.is_active
FROM role_permissions rp
JOIN roles r ON r.id = rp.role_id
JOIN permissions p ON p.id = rp.permission_id
WHERE r.company_id = :company_id
ORDER BY r.code, p.code'''


def configuration(docker=False):
    if not docker:
        return Settings.from_env()
    env = dotenv_values('.env.docker')
    return Settings(f"mysql+pymysql://{env['MYSQL_USER']}:{env['MYSQL_PASSWORD']}@127.0.0.1:3307/{env['MYSQL_DATABASE']}?charset=utf8mb4",
                    env['JWT_SECRET'], env['BOOTSTRAP_KEY'])


def run(settings, url, capture_url=None):
    people = credentials()
    demo = seed(settings, {p: c['password'] for p, c in people.items()})
    demo_file = '.roles-demo.mysql.json' if settings.database_url.startswith('mysql') else '.roles-demo.json'
    Path(demo_file).write_text(json.dumps(demo, ensure_ascii=False, indent=2), encoding='utf-8')
    engine, sessions = database(settings.database_url)
    events, auth = [], {}
    client = httpx.Client(timeout=30)
    suffix = uuid4().hex[:8]

    def rows(model):
        with sessions() as db:
            return db.scalar(select(func.count()).select_from(model))

    def call(title, rule, person, query, variables, code=None):
        query = print_ast(parse(query))
        screenshot = None
        if capture_url:
            captured = client.post(capture_url, json={'url': url, 'query': query, 'variables': variables,
                'headers': auth[person], 'title': title, 'actor': person, 'rule': rule}, timeout=90)
            captured.raise_for_status()
            payload = captured.json()
            result, screenshot = payload['response'], payload['screenshot']
            status = payload['http']
        else:
            response = client.post(url, json={'query': query, 'variables': variables}, headers=auth[person])
            response.raise_for_status()
            result, status = response.json(), response.status_code
        if code:
            assert result.get('errors') and result['errors'][0]['extensions']['code'] == code, result
        else:
            assert 'errors' not in result, result
        events.append({'title': title, 'rule': rule, 'actor': person, 'query': query, 'variables': variables,
                       'expected': code or 'OK', 'http': status, 'response': result, 'screenshot': screenshot})
        return result.get('data')

    try:
        for person, data in people.items():
            response = client.post(url, json={'query': 'mutation($i:LoginInput!){login(input:$i){token}}',
                                              'variables': {'i': data}}).json()
            assert 'errors' not in response, 'No se pudo iniciar sesión como ' + person
            auth[person] = {'Authorization': 'Bearer ' + response['data']['login']['token']}
        cid, roles = demo['companyId'], demo['roles']
        # El guion es repetible: devuelve a Pedro al puesto inicial mediante la API.
        call('00 Preparar el puesto inicial de Pedro', 'La demostración comienza con Pedro como CONSULTA.', 'Ana',
             'mutation($u:ID!,$r:ID!){assignRole(input:{companyUserId:$u,roleId:$r}){id isActive role{code}}}',
             {'u': demo['members']['Pedro']['companyUserId'], 'r': roles['CONSULTA']})
        catalog = call('01 Catálogos', 'La empresa tiene cuatro roles y diez permisos.', 'Ana',
                       'query($c:ID!){roles(companyId:$c){id code} permissions(companyId:$c){id code}}', {'c': cid})
        assert len(catalog['roles']) == 4 and len(catalog['permissions']) == 10
        permissions = {p['code']: p['id'] for p in catalog['permissions']}
        qlist = 'query($r:ID!){rolePermissions(roleId:$r){id isActive permission{code}}}'
        def role_codes(role, title):
            data = call(title, 'Lista vigente del rol ' + role + '.', 'Ana', qlist, {'r': roles[role]})
            return {p['permission']['code'] for p in data['rolePermissions']}
        for role in DEFAULTS:
            assert role_codes(role, '02 Configuración inicial ' + role) == DEFAULTS[role]
        initial = {role: DEFAULTS[role].copy() for role in DEFAULTS}
        def create(person, stage, allowed):
            before = rows(m.Account)
            query = '''mutation($c:ID!,$n:String!,$actor:ID!){
  createAccount(input:{companyId:$c,name:$n,accountType:CASH},actorCompanyUserId:$actor){id name companyId}
}'''
            call(f'{stage} Cuenta de {person}',
                 'El permiso accounts.write se decide por el rol vigente; un rechazo no inserta filas.', person,
                 query, {'c': cid, 'n': f'{person} {stage} {suffix}', 'actor': demo['members'][person]['companyUserId']},
                 None if allowed else 'FORBIDDEN')
            assert rows(m.Account) == before + int(allowed)
            events[-1]['storage'] = {'accounts_before': before, 'accounts_after': rows(m.Account)}
        for person in ('María', 'José'):
            create(person, '03 Antes de conceder', False)
        grant = '''mutation($r:ID!,$p:ID!,$actor:ID!){
  assignPermissionToRole(input:{roleId:$r,permissionId:$p},actorCompanyUserId:$actor){id isActive role{code} permission{code}}
}'''
        revoke = grant.replace('assignPermissionToRole', 'removePermissionFromRole')
        args = {'r': roles['CAPTURISTA'], 'p': permissions['accounts.write'], 'actor': demo['members']['Ana']['companyUserId']}
        link = call('04 Ana concede accounts.write', 'Un cambio en CAPTURISTA beneficia a sus dos integrantes.',
                    'Ana', grant, args)['assignPermissionToRole']
        for person in ('María', 'José'):
            create(person, '05 Con permiso', True)
        call('06 Ana quita accounts.write', 'Quitar un permiso desactiva la pareja y conserva el ID.', 'Ana', revoke, args)
        with sessions() as db:
            saved = db.get(m.RolePermission, int(link['id']))
            assert saved is not None and not saved.is_active
            events[-1]['storage'] = {'role_permission_id': saved.id, 'is_active': saved.is_active, 'row_preserved': True}
        for person in ('María', 'José'):
            create(person, '07 Tras quitar permiso', False)
        movement = '''mutation($a:ID!,$c:ID!,$actor:ID!){
  createTransaction(input:{accountId:$a,conceptId:$c,transactionType:INCOME,amount:"125.50"},actorCompanyUserId:$actor){id amount capturedBy}
}'''
        txargs = {'a': demo['accountId'], 'c': demo['conceptId'], 'actor': demo['members']['Pedro']['companyUserId']}
        before = rows(m.Transaction)
        call('08 Pedro como CONSULTA', 'CONSULTA no tiene transactions.write; el rechazo no crea movimientos.',
             'Pedro', movement, txargs, 'FORBIDDEN')
        assert rows(m.Transaction) == before
        events[-1]['storage'] = {'transactions_before': before, 'transactions_after': rows(m.Transaction)}
        change = '''mutation($u:ID!,$r:ID!,$actor:ID!){
  assignRole(input:{companyUserId:$u,roleId:$r},actorCompanyUserId:$actor){id isActive role{code}}
}'''
        call('09 Ana cambia el puesto de Pedro', 'assignRole deja un solo rol activo y conserva el anterior inactivo.',
             'Ana', change, {'u': demo['members']['Pedro']['companyUserId'], 'r': roles['CAPTURISTA'],
                             'actor': demo['members']['Ana']['companyUserId']})
        call('10 Pedro como CAPTURISTA', 'El mismo token recibe los permisos del nuevo rol.', 'Pedro', movement, txargs)
        assert rows(m.Transaction) == before + 1
        call('11 Historial de Pedro', 'Pedro tiene CAPTURISTA activo y CONSULTA inactivo.', 'Ana',
             'query($u:ID!){companyUserRoles(companyUserId:$u,activeOnly:false){id isActive role{code}}}',
             {'u': demo['members']['Pedro']['companyUserId']})
        with sessions() as db:
            assert db.scalar(select(func.count()).select_from(m.CompanyUserRole).where(
                m.CompanyUserRole.company_user_id == int(txargs['actor']), m.CompanyUserRole.is_active.is_(True))) == 1
        assert role_codes('CONTADOR', '12 Contador sin cambios') == initial['CONTADOR']
        assert role_codes('CONSULTA', '13 Consulta sin cambios') == initial['CONSULTA']
        create('Luis', '14 Contador conserva escritura', True)
        args = {'r': roles['CONSULTA'], 'p': permissions['concepts.write'], 'actor': demo['members']['José']['companyUserId']}
        before = rows(m.RolePermission)
        call('15 José intenta configurar permisos', 'Sin roles.write no se cambia la lista ni se inserta la pareja.',
             'José', grant, args, 'FORBIDDEN')
        assert rows(m.RolePermission) == before
        events[-1]['storage'] = {'role_permissions_before': before, 'role_permissions_after': rows(m.RolePermission)}
        args['actor'] = demo['members']['Ana']['companyUserId']
        call('16 Ana agrega concepts.write a CONSULTA', 'Con roles.write la misma operación sí se permite.', 'Ana', grant, args)
        call('17 Ana restaura CONSULTA', 'La pareja queda inactiva y CONSULTA vuelve a ser de lectura.', 'Ana', revoke, args)
        for role in DEFAULTS:
            assert role_codes(role, '18 Matriz final ' + role) == initial[role]
        with sessions() as db:
            final = [dict(row) for row in db.execute(text(SELECT_FINAL), {'company_id': cid}).mappings()]
        report = {'activity': 'Unidad II - Actividad 4', 'executed_at': datetime.now(timezone.utc).isoformat(),
                  'database': engine.dialect.name, 'endpoint': url, 'companyId': cid, 'checks': len(events),
                  'status': 'PASS', 'events': events, 'final_select': SELECT_FINAL, 'final_rows': final}
        output = Path('docs/evidencias/roles')
        output.mkdir(parents=True, exist_ok=True)
        (output / 'demostracion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        (output / 'role_permissions-final.tsv').write_text(
            'rol\tpermiso\tis_active\n' + ''.join(f"{r['rol']}\t{r['permiso']}\t{int(r['is_active'])}\n" for r in final), encoding='utf-8')
        Path('docs/roles-select.sql').write_text(SELECT_FINAL.replace(':company_id', cid) + ';\n', encoding='utf-8')
        print(f"PASS: {len(events)} operaciones HTTP, almacenamiento comprobado en {engine.dialect.name}.")
        return report
    finally:
        client.close()
        engine.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--docker', action='store_true')
    parser.add_argument('--capture-url', help='Servicio local de capturas de GraphiQL')
    args = parser.parse_args()
    run(configuration(args.docker), 'http://127.0.0.1:8008/graphql' if args.docker else 'http://127.0.0.1:8000/graphql', args.capture_url)
