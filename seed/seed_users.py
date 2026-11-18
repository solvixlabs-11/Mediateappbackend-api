"""Seeder for Users and admin accounts."""

import os
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.modules.users.models import Role, User
from seed.base import SeedResult


def run(session: Session, dev: bool = False) -> SeedResult:
    result = SeedResult(name="users")

    # Find roles
    admin_role = session.query(Role).filter(Role.code.in_(["ADMIN", "ERP ADMIN"])).first()
    manager_role = session.query(Role).filter(Role.code == "MANAGER").first()
    mr_role = session.query(Role).filter(Role.code == "MR").first()

    default_admin_email = os.getenv("ADMIN_EMAIL", "admin@mediatehealthcare.com")
    default_admin_password = os.getenv("ADMIN_PASSWORD", "Admin@123")

    core_users = [
        {
            "email": default_admin_email,
            "full_name": "System Administrator",
            "phone": "+919820098200",
            "role": admin_role,
        },
        {
            "email": "manager@mediatehealthcare.com",
            "full_name": "Regional Manager Demo",
            "phone": "+919820098201",
            "role": manager_role,
        },
        {
            "email": "mr@mediatehealthcare.com",
            "full_name": "Field MR Demo",
            "phone": "+919820098202",
            "role": mr_role,
        },
    ]

    for u_data in core_users:
        if not u_data["role"]:
            continue
        existing = session.query(User).filter(User.email == u_data["email"]).first()
        if existing:
            changed = False
            if existing.full_name != u_data["full_name"]:
                existing.full_name = u_data["full_name"]
                changed = True
            if existing.role_id != u_data["role"].id:
                existing.role_id = u_data["role"].id
                changed = True
            if existing.is_deleted:
                existing.is_deleted = False
                existing.is_active = True
                changed = True
            if changed:
                result.updated += 1
            else:
                result.unchanged += 1
        else:
            new_u = User(
                email=u_data["email"],
                hashed_password=hash_password(default_admin_password),
                full_name=u_data["full_name"],
                phone=u_data["phone"],
                role_id=u_data["role"].id,
                is_active=True,
                force_password_change=False,
            )
            session.add(new_u)
            result.created += 1

    session.flush()

    if dev and mr_role:
        # Seed 10 synthetic MRs for development
        for i in range(1, 11):
            email = f"test.mr{i}@mediatehealthcare.com"
            existing = session.query(User).filter(User.email == email).first()
            if not existing:
                mr = User(
                    email=email,
                    hashed_password=hash_password("MrTest@123"),
                    full_name=f"Test MR {i:02d}",
                    phone=f"+9198000000{i:02d}",
                    role_id=mr_role.id,
                    is_active=True,
                    force_password_change=False,
                )
                session.add(mr)
                result.created += 1
            else:
                result.unchanged += 1

    session.flush()
    return result
