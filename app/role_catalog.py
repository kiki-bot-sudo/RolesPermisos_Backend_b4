"""Configuración inicial. Solo completa catálogos nuevos; nunca restaura permisos quitados."""
from sqlalchemy import select
from . import models as m
from .db import Base, serialize_write

PERMISSIONS = {
    'company.users.read': 'Ver usuarios de la empresa',
    'company.users.write': 'Invitar y desactivar usuarios',
    'accounts.read': 'Ver cuentas', 'accounts.write': 'Crear cuentas',
    'concepts.read': 'Ver conceptos', 'concepts.write': 'Crear y asignar conceptos',
    'transactions.read': 'Ver movimientos', 'transactions.write': 'Registrar y eliminar movimientos',
    'roles.read': 'Ver roles y permisos', 'roles.write': 'Configurar y asignar roles',
}
DEFAULTS = {
    'ADMINISTRADOR': set(PERMISSIONS),
    'CONTADOR': {'company.users.read', 'accounts.read', 'accounts.write', 'concepts.read',
                 'concepts.write', 'transactions.read', 'transactions.write', 'roles.read'},
    'CAPTURISTA': {'accounts.read', 'concepts.read', 'transactions.read', 'transactions.write'},
    'CONSULTA': {'company.users.read', 'accounts.read', 'concepts.read', 'transactions.read'},
}


def ensure_catalog(db, company_id=None):
    permissions = {p.code: p for p in db.scalars(select(m.Permission))}
    for code, label in PERMISSIONS.items():
        if code not in permissions:
            permissions[code] = m.Permission(code=code, name=label)
            db.add(permissions[code])
    db.flush()
    if company_id is None:
        return
    roles = {r.code: r for r in db.scalars(select(m.Role).where(m.Role.company_id == company_id))}
    for code, codes in DEFAULTS.items():
        if code in roles:
            continue
        role = m.Role(company_id=company_id, code=code, name=code.title())
        db.add(role)
        db.flush()
        for permission_code in sorted(codes):
            db.add(m.RolePermission(role_id=role.id, permission_id=permissions[permission_code].id))
    db.flush()


def initial_role(db, member):
    ensure_catalog(db, member.company_id)
    if db.scalar(select(m.CompanyUserRole.id).where(m.CompanyUserRole.company_user_id == member.id)):
        return
    code = 'ADMINISTRADOR' if member.is_admin else 'CAPTURISTA'
    role = db.scalar(select(m.Role).where(m.Role.company_id == member.company_id, m.Role.code == code))
    db.add(m.CompanyUserRole(company_user_id=member.id, role_id=role.id))
    db.flush()


def initialize(engine, sessions):
    # Una conexión mantiene el candado también durante create_all en MySQL.
    from sqlalchemy import text
    with engine.connect() as connection:
        mysql = engine.dialect.name == 'mysql'
        if mysql:
            if connection.scalar(text("SELECT GET_LOCK('ingresos_role_catalog', 30)")) != 1:
                raise RuntimeError('No se pudo bloquear la inicialización de roles.')
            connection.commit()
        try:
            Base.metadata.create_all(connection)
            if mysql:
                from sqlalchemy import inspect
                indexes = {index['name'] for index in inspect(connection).get_indexes('company_users')}
                for index in m.CompanyUser.__table__.indexes:
                    if index.name == 'uq_company_admin_mysql' and index.name not in indexes:
                        index.create(connection)
            connection.commit()
            with sessions(bind=connection) as db, db.begin():
                serialize_write(db)
                ensure_catalog(db)
                for company in db.scalars(select(m.Company).order_by(m.Company.id)):
                    ensure_catalog(db, company.id)
                for member in db.scalars(select(m.CompanyUser).order_by(m.CompanyUser.id)):
                    initial_role(db, member)
        finally:
            if mysql:
                connection.execute(text("SELECT RELEASE_LOCK('ingresos_role_catalog')"))
                connection.commit()
