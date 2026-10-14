"""Empresa de Unidad II, Actividad 4. Repetir conserva permisos y puestos modificados."""
import json
import secrets
from pathlib import Path
from sqlalchemy import select
from . import models as m
from .config import Settings
from .db import database, serialize_write
from .role_catalog import initialize
from .finance_service import FinanceService

PEOPLE = {'Ana': 'ADMINISTRADOR', 'Luis': 'CONTADOR', 'María': 'CAPTURISTA',
          'José': 'CAPTURISTA', 'Pedro': 'CONSULTA'}
EMAILS = dict(zip(PEOPLE, ['ana.roles@example.com', 'luis.roles@example.com', 'maria.roles@example.com',
                          'jose.roles@example.com', 'pedro.roles@example.com']))
TAX_ID = 'DEMO-UNIDAD2-ACTIVIDAD4'


def seed(settings, passwords):
    engine, sessions = database(settings.database_url)
    initialize(engine, sessions)
    try:
        with sessions.begin() as db:
            serialize_write(db)
            svc = FinanceService(db, settings, {'x-bootstrap-key': settings.bootstrap_key})
            company = db.scalar(select(m.Company).where(m.Company.tax_id == TAX_ID))
            if company is None:
                company = svc.create_company({'name': 'Sistema General de Ingresos - Roles U2 A4', 'tax_id': TAX_ID})
                svc.create_member({'company_id': company.id, 'name': 'Ana', 'email': EMAILS['Ana'],
                                   'password': passwords['Ana']}, True)
            token, _ = svc.login({'email': EMAILS['Ana'], 'password': passwords['Ana']})
            svc.headers = {'authorization': 'Bearer ' + token}
            roles = {r.code: r for r in db.scalars(select(m.Role).where(m.Role.company_id == company.id))}
            members = {}
            for person, code in PEOPLE.items():
                member = db.scalar(select(m.CompanyUser).join(m.User).where(
                    m.CompanyUser.company_id == company.id, m.User.email == EMAILS[person]))
                if member is None:
                    member = svc.create_member({'company_id': company.id, 'name': person, 'email': EMAILS[person],
                                                'password': passwords[person]}, False)
                    svc.assign_role(member.id, roles[code].id)
                members[person] = {'companyUserId': str(member.id), 'userId': str(member.user_id), 'email': EMAILS[person]}
            account = db.scalar(select(m.Account).where(m.Account.company_id == company.id, m.Account.name_key == 'caja roles'))
            if account is None:
                account = svc.create_catalog(m.Account, {'company_id': company.id, 'account_type': 'CASH', 'name': 'Caja roles'})
            concept = db.scalar(select(m.Concept).where(m.Concept.company_id == company.id, m.Concept.name_key == 'ventas roles'))
            if concept is None:
                concept = svc.create_catalog(m.Concept, {'company_id': company.id, 'concept_type': 'INCOME', 'name': 'Ventas roles'})
            if svc.relation(account.id, concept.id) is None:
                svc.assign(account.id, concept.id)
            return {'companyId': str(company.id), 'accountId': str(account.id), 'conceptId': str(concept.id),
                    'members': members, 'roles': {k: str(v.id) for k, v in roles.items()}}
    finally:
        engine.dispose()


def credentials():
    path = Path('.roles-credentials.json')
    if not path.exists():
        path.write_text(json.dumps({p: {'email': EMAILS[p], 'password': secrets.token_urlsafe(24)}
                                    for p in PEOPLE}, ensure_ascii=False, indent=2), encoding='utf-8')
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    data = credentials()
    result = seed(Settings.from_env(), {p: c['password'] for p, c in data.items()})
    Path('.roles-demo.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print('Credenciales privadas: .roles-credentials.json. Identificadores: .roles-demo.json.')


if __name__ == '__main__':
    main()
