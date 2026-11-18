"""Seeder for Permissions and Role-Permission mappings."""

from sqlalchemy.orm import Session
from app.modules.users.models import Permission, Role, RolePermission
from seed.base import SeedResult, load_json


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="permissions")
    data = load_json("permissions.json")
    for row in data:
        code = row["code"]
        existing = session.query(Permission).filter(Permission.code == code).first()
        if existing:
            changed = False
            if existing.description != row.get("description"):
                existing.description = row.get("description")
                changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            perm = Permission(
                code=code,
                module=row["module"],
                description=row.get("description"),
            )
            session.add(perm)
            result.created += 1
    session.flush()

    # Map all permissions to ADMIN and ERP ADMIN roles
    all_perms = session.query(Permission).all()
    admin_roles = session.query(Role).filter(Role.code.in_(["ADMIN", "ERP ADMIN"])).all()
    for role in admin_roles:
        existing_perm_ids = {
            rp.permission_id
            for rp in session.query(RolePermission).filter(RolePermission.role_id == role.id).all()
        }
        for p in all_perms:
            if p.id not in existing_perm_ids:
                session.add(RolePermission(role_id=role.id, permission_id=p.id))

    session.flush()
    return result
