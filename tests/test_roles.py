"""Casos de la Unidad II Actividad 4, autorización e integridad de la base."""
from concurrent.futures import ThreadPoolExecutor
import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app import models as m
from app.factory import create_app
from app.role_catalog import DEFAULTS, PERMISSIONS
from test_graphql import setup, company, credentials, login, ADMIN, USER
from test_finance import ACCOUNT, CONCEPT, ASSIGN, TX

ROLES = 'query($c:ID!){roles(companyId:$c){id code} permissions(companyId:$c){id code}}'
LIST = 'query($r:ID!){rolePermissions(roleId:$r){id isActive permission{code}}}'
GRANT = 'mutation($r:ID!,$p:ID!,$actor:ID){assignPermissionToRole(input:{roleId:$r,permissionId:$p},actorCompanyUserId:$actor){id isActive role{code} permission{code}}}'
REVOKE = GRANT.replace('assignPermissionToRole', 'removePermissionFromRole')
SET_ROLE = 'mutation($u:ID!,$r:ID!,$actor:ID){assignRole(input:{companyUserId:$u,roleId:$r},actorCompanyUserId:$actor){id isActive role{code}}}'


@pytest.fixture
def team(api):
    cid, ana, auth = setup(api)
    result = api.call(ROLES, {'c': cid}, auth)
    roles = {x['code']: x['id'] for x in result['roles']}
    permissions = {x['code']: x['id'] for x in result['permissions']}
    people = {'Ana': {'member': ana, 'auth': auth}}
    for person, role in [('Luis', 'CONTADOR'), ('María', 'CAPTURISTA'), ('José', 'CAPTURISTA'), ('Pedro', 'CONSULTA')]:
        mail = {'María': 'maria', 'José': 'jose'}.get(person, person.lower()) + '@example.com'
        member = api.call(USER, {'input': {**credentials(cid, mail), 'name': person}}, auth)['createCompanyUser']
        api.call(SET_ROLE, {'u': member['id'], 'r': roles[role], 'actor': ana['id']}, auth)
        people[person] = {'member': member, 'auth': login(api, mail)}
    return cid, roles, permissions, people


def count(api, model):
    with api.app.state.sessions() as db:
        return db.scalar(select(func.count()).select_from(model))


def codes(api, role, auth):
    return {x['permission']['code'] for x in api.call(LIST, {'r': role}, auth)['rolePermissions']}


def account(api, team, person, label, code=None):
    return api.call(ACCOUNT, {'input': {'companyId': team[0], 'name': label, 'accountType': 'CASH'}},
                    team[3][person]['auth'], code)


def test_initial_matrix_and_admin_membership(api, team):
    cid, roles, permissions, people = team
    assert set(roles) == set(DEFAULTS) and set(permissions) == set(PERMISSIONS)
    for role, expected in DEFAULTS.items():
        assert codes(api, roles[role], people['Ana']['auth']) == expected
    assert people['Ana']['member']['isAdmin'] is True
    with api.app.state.sessions() as db:
        for person, role in [('Ana', 'ADMINISTRADOR'), ('Luis', 'CONTADOR'), ('María', 'CAPTURISTA'), ('José', 'CAPTURISTA'), ('Pedro', 'CONSULTA')]:
            links = list(db.scalars(select(m.CompanyUserRole).where(
                m.CompanyUserRole.company_user_id == int(people[person]['member']['id']), m.CompanyUserRole.is_active.is_(True))))
            assert len(links) == 1 and links[0].role.code == role


def test_role_change_applies_to_two_people_and_soft_revoke(api, team):
    _, roles, permissions, people = team
    auth = people['Ana']['auth']
    args = {'r': roles['CAPTURISTA'], 'p': permissions['accounts.write'], 'actor': people['Ana']['member']['id']}
    before = count(api, m.Account)
    for p in ('María', 'José'):
        account(api, team, p, p + ' antes', 'FORBIDDEN')
    assert count(api, m.Account) == before
    link = api.call(GRANT, args, auth)['assignPermissionToRole']
    api.call(GRANT, args, auth, 'CONFLICT')
    for p in ('María', 'José'):
        account(api, team, p, p + ' permitido')
    assert count(api, m.Account) == before + 2
    removed = api.call(REVOKE, args, auth)['removePermissionFromRole']
    assert removed['id'] == link['id'] and not removed['isActive']
    for p in ('María', 'José'):
        account(api, team, p, p + ' después', 'FORBIDDEN')
    assert count(api, m.Account) == before + 2
    with api.app.state.sessions() as db:
        assert db.get(m.RolePermission, int(link['id'])).is_active is False
    reactivated = api.call(GRANT, args, auth)['assignPermissionToRole']
    assert reactivated['id'] == link['id']
    api.call(REVOKE, args, auth)


def test_pedro_changes_role_without_changing_other_lists(api, team):
    cid, roles, _, people = team
    auth = people['Ana']['auth']
    original = {r: codes(api, roles[r], auth) for r in ('CONTADOR', 'CONSULTA')}
    a = account(api, team, 'Ana', 'Caja')['createAccount']['id']
    c = api.call(CONCEPT, {'input': {'companyId': cid, 'conceptType': 'INCOME', 'name': 'Ventas'}}, auth)['createConcept']['id']
    api.call(ASSIGN, {'input': {'accountId': a, 'conceptId': c}}, auth)
    movement = {'input': {'accountId': a, 'conceptId': c, 'transactionType': 'INCOME', 'amount': '125.50'}}
    before = count(api, m.Transaction)
    api.call(TX, movement, people['Pedro']['auth'], 'FORBIDDEN')
    assert count(api, m.Transaction) == before
    api.call(SET_ROLE, {'u': people['Pedro']['member']['id'], 'r': roles['CAPTURISTA']}, auth)
    result = api.call(TX, movement, people['Pedro']['auth'])['createTransaction']
    assert result['capturedBy'] == people['Pedro']['member']['userId']
    assert count(api, m.Transaction) == before + 1
    for r in original:
        assert codes(api, roles[r], auth) == original[r]
    account(api, team, 'Luis', 'Cuenta del contador')
    with api.app.state.sessions() as db:
        links = list(db.scalars(select(m.CompanyUserRole).where(
            m.CompanyUserRole.company_user_id == int(people['Pedro']['member']['id']))))
        assert sum(x.is_active for x in links) == 1
        assert next(x for x in links if x.role.code == 'CONSULTA').is_active is False


def test_only_roles_write_changes_configuration(api, team):
    _, roles, permissions, people = team
    args = {'r': roles['CONSULTA'], 'p': permissions['concepts.write']}
    before = count(api, m.RolePermission)
    api.call(GRANT, args, people['José']['auth'], 'FORBIDDEN')
    assert count(api, m.RolePermission) == before
    result = api.call(GRANT, args, people['Ana']['auth'])['assignPermissionToRole']
    assert result['isActive']
    api.call(REVOKE, args, people['Ana']['auth'])
    assert codes(api, roles['CONSULTA'], people['Ana']['auth']) == DEFAULTS['CONSULTA']


def test_actor_cannot_impersonate_admin_or_bypass_jwt(api, team):
    cid, roles, permissions, people = team
    args = {'r': roles['CONSULTA'], 'p': permissions['concepts.write'], 'actor': people['Ana']['member']['id']}
    api.call(GRANT, args, people['José']['auth'], 'FORBIDDEN')
    api.call(GRANT, args, code='UNAUTHENTICATED')
    q = 'mutation($c:ID!,$a:ID!){createAccount(input:{companyId:$c,name:"Suplantada",accountType:CASH},actorCompanyUserId:$a){id}}'
    api.call(q, {'c': cid, 'a': people['Ana']['member']['id']}, people['María']['auth'], 'FORBIDDEN')
    api.call(q, {'c': cid, 'a': people['José']['member']['id']}, people['Ana']['auth'], 'FORBIDDEN')
    assert count(api, m.Account) == 0


def test_roles_cannot_cross_companies(api, team):
    cid, roles, permissions, people = team
    other = company(api, 'Otra empresa')
    member = api.call(ADMIN, {'input': credentials(other, 'another@example.com')}, api.bootstrap)['createCompanyAdmin']
    other_auth = login(api, 'another@example.com')
    other_roles = api.call(ROLES, {'c': other}, other_auth)['roles']
    api.call(LIST, {'r': roles['CONTADOR']}, other_auth, 'FORBIDDEN')
    api.call(GRANT, {'r': roles['CONSULTA'], 'p': permissions['accounts.write']}, other_auth, 'FORBIDDEN')
    api.call(SET_ROLE, {'u': member['id'], 'r': roles['CAPTURISTA']}, people['Ana']['auth'], 'FORBIDDEN')
    assert not ({r['id'] for r in other_roles} & set(roles.values()))
    assert codes(api, roles['CONSULTA'], people['Ana']['auth']) == DEFAULTS['CONSULTA']


def test_actor_selects_one_of_users_own_companies(api, team):
    from app.role_catalog import initial_role
    _, _, _, people = team
    other = company(api, 'Empresa compartida')
    api.call(ADMIN, {'input': credentials(other, 'shared-admin@example.com')}, api.bootstrap)
    with api.app.state.sessions.begin() as db:
        member = m.CompanyUser(company_id=int(other), user_id=int(people['Ana']['member']['userId']))
        db.add(member)
        db.flush()
        initial_role(db, member)
        shared_id = str(member.id)
    query = 'query($a:ID!){transactions(actorCompanyUserId:$a){id}}'
    for actor in (people['Ana']['member']['id'], shared_id):
        assert api.call(query, {'a': actor}, people['Ana']['auth'])['transactions'] == []
    api.call(query, {'a': shared_id}, people['Pedro']['auth'], 'FORBIDDEN')


def test_read_and_write_are_independent_and_no_admin_bypass(api, team):
    cid, roles, permissions, people = team
    auth = people['Ana']['auth']
    for person in ('María', 'José', 'Pedro'):
        api.call('query($c:ID!){accounts(companyId:$c){id}}', {'c': cid}, people[person]['auth'])
        account(api, team, person, 'Denegada ' + person, 'FORBIDDEN')
    # Aun isAdmin=true obedece role_permissions; no se usa como bypass.
    args = {'r': roles['ADMINISTRADOR'], 'p': permissions['accounts.write']}
    api.call(REVOKE, args, auth)
    account(api, team, 'Ana', 'Sin bypass', 'FORBIDDEN')
    api.call(GRANT, args, auth)
    # Retirar lectura no impide un permiso de escritura explícitamente concedido.
    args = {'r': roles['CONTADOR'], 'p': permissions['accounts.read']}
    api.call(REVOKE, args, auth)
    api.call('query($c:ID!){accounts(companyId:$c){id}}', {'c': cid}, people['Luis']['auth'], 'FORBIDDEN')
    account(api, team, 'Luis', 'Escritura separada')
    api.call(GRANT, args, auth)


def test_restart_does_not_duplicate_or_restore_revoked_permissions(api, team):
    _, roles, permissions, people = team
    args = {'r': roles['CAPTURISTA'], 'p': permissions['accounts.write']}
    link = api.call(GRANT, args, people['Ana']['auth'])['assignPermissionToRole']
    api.call(REVOKE, args, people['Ana']['auth'])
    before = [count(api, model) for model in (m.Role, m.Permission, m.RolePermission, m.CompanyUserRole)]
    restarted = create_app(api.settings)
    restarted.state.engine.dispose()
    assert before == [count(api, model) for model in (m.Role, m.Permission, m.RolePermission, m.CompanyUserRole)]
    with api.app.state.sessions() as db:
        assert db.get(m.RolePermission, int(link['id'])).is_active is False
    assert codes(api, roles['CAPTURISTA'], people['Ana']['auth']) == DEFAULTS['CAPTURISTA']


def test_one_active_role_even_concurrent_and_at_database_level(api, team):
    _, roles, _, people = team
    target = people['Pedro']['member']['id']
    def assign(role):
        return api.client.post('/graphql', json={'query': SET_ROLE, 'variables': {'u': target, 'r': roles[role]}},
                               headers=people['Ana']['auth']).json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(assign, ['CONTADOR', 'CAPTURISTA']))
    assert all('errors' not in result for result in results), results
    with api.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(m.CompanyUserRole).where(
            m.CompanyUserRole.company_user_id == int(target), m.CompanyUserRole.is_active.is_(True))) == 1
    with pytest.raises(IntegrityError), api.app.state.sessions.begin() as db:
        link = db.scalar(select(m.CompanyUserRole).where(
            m.CompanyUserRole.company_user_id == int(target), m.CompanyUserRole.is_active.is_(False)))
        link.is_active = True
        db.flush()


def test_roles_seed_repeatable_preserves_changes(api):
    from app.seed_roles import seed, PEOPLE
    passwords = {p: 'Testing-roles-only-2026!' for p in PEOPLE}
    first = seed(api.settings, passwords)
    assert seed(api.settings, passwords) == first
    assert count(api, m.User) == 5 and count(api, m.Permission) == 10 and count(api, m.Role) == 4


@pytest.mark.parametrize('person,role', [('Ana', 'ADMINISTRADOR'), ('Luis', 'CONTADOR'),
                                      ('María', 'CAPTURISTA'), ('Pedro', 'CONSULTA')])
def test_each_permission_protects_its_operation(api, team, person, role):
    cid, roles, permissions, people = team
    admin = people['Ana']['auth']
    a = account(api, team, 'Ana', 'Caja para matriz')['createAccount']['id']
    c = api.call(CONCEPT, {'input': {'companyId': cid, 'conceptType': 'INCOME', 'name': 'Matriz'}}, admin)['createConcept']['id']
    api.call(ASSIGN, {'input': {'accountId': a, 'conceptId': c}}, admin)
    cases = [
        ('company.users.read', 'query($c:ID!){companyUsers(companyId:$c){id}}', {'c': cid}),
        ('company.users.write', USER, {'input': credentials(cid, 'invited@example.com')}),
        ('accounts.read', 'query($c:ID!){accounts(companyId:$c){id}}', {'c': cid}),
        ('accounts.write', ACCOUNT, {'input': {'companyId': cid, 'name': 'Cuenta matriz', 'accountType': 'CASH'}}),
        ('concepts.read', 'query($c:ID!){concepts(companyId:$c){id}}', {'c': cid}),
        ('concepts.write', CONCEPT, {'input': {'companyId': cid, 'name': 'Concepto matriz', 'conceptType': 'EXPENSE'}}),
        ('transactions.read', 'query($a:ID!){transactions(accountId:$a){id}}', {'a': a}),
        ('transactions.write', TX, {'input': {'accountId': a, 'conceptId': c, 'transactionType': 'INCOME', 'amount': '10'}}),
        ('roles.read', ROLES, {'c': cid}),
        ('roles.write', SET_ROLE, {'u': people['Pedro']['member']['id'], 'r': roles['CONSULTA']}),
    ]
    models = [m.User, m.CompanyUser, m.Account, m.Concept, m.Transaction, m.RolePermission, m.CompanyUserRole]
    for permission, query, variables in cases:
        allowed = permission in DEFAULTS[role]
        before = [count(api, model) for model in models]
        api.call(query, variables, people[person]['auth'], None if allowed else 'FORBIDDEN')
        if not allowed:
            assert before == [count(api, model) for model in models], permission
