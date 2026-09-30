import logging

from sqlalchemy.orm import Session

import app.db  # noqa: F401
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.modules.users.models import ManagerMRAssignment, Permission, Role, RolePermission, User

logger = logging.getLogger(__name__)

INITIAL_ROLES = [
    {
        "code": "ADMIN",
        "name": "System Administrator",
        "description": "Head office superuser with full system access across all modules",
    },
    {
        "code": "MANAGER",
        "name": "Regional Manager",
        "description": "Area and regional manager overseeing assigned MR team members",
    },
    {
        "code": "MR",
        "name": "Medical Representative",
        "description": "Field force representative executing doctor visits, DCR, and orders",
    },
]

INITIAL_PERMISSIONS = [
    # Auth
    {"code": "auth:me", "module": "auth", "description": "View own profile and active permissions"},
    {"code": "auth:change_password", "module": "auth", "description": "Change own login password"},
    # Users
    {"code": "users:read", "module": "users", "description": "View user accounts and profiles"},
    {"code": "users:write", "module": "users", "description": "Create and update user accounts"},
    {
        "code": "users:manage_roles",
        "module": "users",
        "description": "Manage user role assignments",
    },
    # Customers
    {
        "code": "customers:read",
        "module": "customers",
        "description": "View doctors, hospitals, chemists, stockists",
    },
    {
        "code": "customers:write",
        "module": "customers",
        "description": "Create or update customer records",
    },
    # DCR & Attendance
    {
        "code": "attendance:checkin",
        "module": "attendance",
        "description": "Perform daily check-in and checkout",
    },
    {"code": "dcr:read", "module": "dcr", "description": "View daily call reports"},
    {"code": "dcr:write", "module": "dcr", "description": "Submit and edit daily call reports"},
    # Approvals (Tour, Expense, Leave)
    {"code": "tours:read", "module": "tours", "description": "View tour plans"},
    {"code": "tours:write", "module": "tours", "description": "Submit tour plans"},
    {"code": "tours:approve", "module": "tours", "description": "Approve or reject tour plans"},
    {"code": "expenses:read", "module": "expenses", "description": "View expense claims"},
    {"code": "expenses:write", "module": "expenses", "description": "Submit expense claims"},
    {"code": "expenses:approve", "module": "expenses", "description": "Approve or reject expenses"},
    {"code": "leaves:read", "module": "leaves", "description": "View leave requests"},
    {"code": "leaves:write", "module": "leaves", "description": "Submit leave requests"},
    {"code": "leaves:approve", "module": "leaves", "description": "Approve or reject leaves"},
    # Orders & Tasks & Reports
    {"code": "orders:read", "module": "orders", "description": "View orders"},
    {"code": "orders:write", "module": "orders", "description": "Create orders"},
    {"code": "tasks:read", "module": "tasks", "description": "View tasks"},
    {"code": "tasks:write", "module": "tasks", "description": "Create and update tasks"},
    {"code": "reports:read", "module": "reports", "description": "View analytics and reports"},
]

DEV_SAMPLE_USERS = [
    {
        "email": "admin@mediatehealthcare.com",
        "full_name": "System Administrator",
        "password": "Admin@123",
        "phone": "+919876543210",
        "role_code": "ADMIN",
    },
    {
        "email": "manager@mediatehealthcare.com",
        "full_name": "Regional Manager Demo",
        "password": "Manager@123",
        "phone": "+919876543211",
        "role_code": "MANAGER",
    },
    {
        "email": "mr@mediatehealthcare.com",
        "full_name": "Field MR Demo",
        "password": "Mr@123",
        "phone": "+919876543212",
        "role_code": "MR",
    },
]


def seed_database(db: Session) -> None:
    """Seed initial roles, permissions, and default accounts."""
    # 1. Seed Roles
    role_map: dict[str, Role] = {}
    for role_data in INITIAL_ROLES:
        role = db.query(Role).filter(Role.code == role_data["code"]).first()
        if not role:
            role = Role(
                code=role_data["code"],
                name=role_data["name"],
                description=role_data["description"],
            )
            db.add(role)
            db.flush()
            logger.info("Seeded role: %s", role.code)
        role_map[role.code] = role

    # 2. Seed Permissions
    perm_map: dict[str, Permission] = {}
    for perm_data in INITIAL_PERMISSIONS:
        perm = db.query(Permission).filter(Permission.code == perm_data["code"]).first()
        if not perm:
            perm = Permission(
                code=perm_data["code"],
                module=perm_data["module"],
                description=perm_data["description"],
            )
            db.add(perm)
            db.flush()
        perm_map[perm.code] = perm

    # 3. Associate Permissions to Roles
    # ADMIN gets all permissions
    admin_role = role_map["ADMIN"]
    existing_admin_perm_ids = {
        rp.permission_id
        for rp in db.query(RolePermission).filter(RolePermission.role_id == admin_role.id).all()
    }
    for perm in perm_map.values():
        if perm.id not in existing_admin_perm_ids:
            db.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))

    # MANAGER permissions
    manager_perms = [
        "auth:me",
        "auth:change_password",
        "users:read",
        "customers:read",
        "customers:write",
        "dcr:read",
        "attendance:checkin",
        "tours:read",
        "tours:approve",
        "expenses:read",
        "expenses:approve",
        "leaves:read",
        "leaves:approve",
        "orders:read",
        "tasks:read",
        "tasks:write",
        "reports:read",
    ]
    manager_role = role_map["MANAGER"]
    existing_mgr_perm_ids = {
        rp.permission_id
        for rp in db.query(RolePermission).filter(RolePermission.role_id == manager_role.id).all()
    }
    for code in manager_perms:
        perm = perm_map.get(code)
        if perm and perm.id not in existing_mgr_perm_ids:
            db.add(RolePermission(role_id=manager_role.id, permission_id=perm.id))

    # MR permissions
    mr_perms = [
        "auth:me",
        "auth:change_password",
        "customers:read",
        "customers:write",
        "dcr:read",
        "dcr:write",
        "attendance:checkin",
        "tours:read",
        "tours:write",
        "expenses:read",
        "expenses:write",
        "leaves:read",
        "leaves:write",
        "orders:read",
        "orders:write",
        "tasks:read",
    ]
    mr_role = role_map["MR"]
    existing_mr_perm_ids = {
        rp.permission_id
        for rp in db.query(RolePermission).filter(RolePermission.role_id == mr_role.id).all()
    }
    for code in mr_perms:
        perm = perm_map.get(code)
        if perm and perm.id not in existing_mr_perm_ids:
            db.add(RolePermission(role_id=mr_role.id, permission_id=perm.id))

    db.flush()

    # 4. Seed Users
    for user_data in DEV_SAMPLE_USERS:
        existing_user = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing_user:
            role = role_map[user_data["role_code"]]
            new_user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                phone=user_data["phone"],
                hashed_password=hash_password(user_data["password"]),
                role_id=role.id,
                is_active=True,
                force_password_change=False,
            )
            db.add(new_user)
            logger.info("Seeded user: %s (%s)", new_user.email, user_data["role_code"])
    db.commit()

    # 5. Seed initial Manager-MR relationship if not exists
    manager_user = db.query(User).filter(User.email == "manager@mediatehealthcare.com").first()
    mr_user = db.query(User).filter(User.email == "mr@mediatehealthcare.com").first()
    if manager_user and mr_user:
        existing_assignment = (
            db.query(ManagerMRAssignment)
            .filter(
                ManagerMRAssignment.manager_id == manager_user.id,
                ManagerMRAssignment.mr_id == mr_user.id,
                ManagerMRAssignment.unassigned_at.is_(None),
            )
            .first()
        )
        if not existing_assignment:
            db.add(
                ManagerMRAssignment(
                    manager_id=manager_user.id,
                    mr_id=mr_user.id,
                )
            )
            db.commit()
            logger.info("Seeded manager-MR assignment: %s -> %s", manager_user.email, mr_user.email)

    logger.info("Seeding completed successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    session = SessionLocal()
    try:
        seed_database(session)
    finally:
        session.close()
