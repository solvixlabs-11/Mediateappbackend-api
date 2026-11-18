"""Navigation menu business service."""

import json
from pathlib import Path
from typing import Any

from app.modules.navigation.schemas import (
    MobileDrawerItem,
    NavigationGroup,
    NavigationItem,
    NavigationMenuResponse,
    NavigationSubgroup,
    QuickCardItem,
)
from app.modules.users.models import User

# Load raw inventory data from verified JSON specification
_INVENTORY_PATH = Path(__file__).parent / "navigation_items.json"
with open(_INVENTORY_PATH, "r", encoding="utf-8") as _f:
    RAW_INVENTORY_ITEMS: list[dict[str, Any]] = json.load(_f)

# Group structure definitions matching MR Buddy reference specification
GROUP_METADATA: list[dict[str, Any]] = [
    {
        "key": "masters",
        "label": "Masters",
        "iconName": "DatabaseOutlined",
        "subgroups": ["Company", "Customers", "Direct", "Products"],
    },
    {
        "key": "parameters",
        "label": "Parameters",
        "iconName": "EnvironmentOutlined",
        "subgroups": [],
    },
    {
        "key": "reports",
        "label": "Reports",
        "iconName": "BarChartOutlined",
        "subgroups": [],
    },
    {
        "key": "activities",
        "label": "Activities",
        "iconName": "CheckSquareOutlined",
        "subgroups": [],
    },
    {
        "key": "utility",
        "label": "Utility",
        "iconName": "ToolOutlined",
        "subgroups": [
            "Admin Panel",
            "Leaves",
            "Manage Routes",
            "Direct",
            "Reimbursement",
            "Visit Approvals",
        ],
    },
    {
        "key": "detail-reports",
        "label": "Detail Reports",
        "iconName": "FileTextOutlined",
        "subgroups": [],
    },
]


class NavigationService:
    """Service to produce dynamic, role-filtered navigation hierarchies."""

    @staticmethod
    def get_navigation_menu(current_user: User) -> NavigationMenuResponse:
        """Build authorized menu tree based on current user permissions and role."""
        is_admin = bool(
            current_user.role
            and current_user.role.code in ("ADMIN", "ERP ADMIN", "SUPERADMIN")
        )
        user_permissions = (
            {p.code for p in current_user.role.permissions}
            if current_user.role and current_user.role.permissions
            else set()
        )

        all_items: list[NavigationItem] = []
        permitted_items_list: list[NavigationItem] = []

        for raw in RAW_INVENTORY_ITEMS:
            req_perm = raw.get("requiredPermission")
            is_permitted = bool(is_admin or not req_perm or req_perm in user_permissions)

            item = NavigationItem(
                id=raw["id"],
                key=raw["key"],
                label=raw["label"],
                path=raw["path"],
                group=raw["group"],
                groupLabel=raw["groupLabel"],
                subgroup=raw.get("subgroup"),
                requiredPermission=req_perm,
                status=raw["status"],
                tier=raw["tier"],
                ourApp=raw["ourApp"],
                purpose=raw["purpose"],
                isPermitted=is_permitted,
            )
            all_items.append(item)
            if is_permitted:
                permitted_items_list.append(item)

        # Build group trees
        groups: list[NavigationGroup] = []
        for g_meta in GROUP_METADATA:
            g_key = g_meta["key"]
            expected_subgroups: list[str] = g_meta["subgroups"]

            # Filter items belonging to this group
            group_candidates = [
                it for it in (all_items if is_admin else permitted_items_list)
                if it.group == g_key
            ]

            if expected_subgroups:
                subgroups_list: list[NavigationSubgroup] = []
                for sub_name in expected_subgroups:
                    sub_items = [
                        it for it in group_candidates
                        if it.subgroup == sub_name
                    ]
                    if sub_items or is_admin:
                        subgroups_list.append(
                            NavigationSubgroup(name=sub_name, items=sub_items)
                        )
                groups.append(
                    NavigationGroup(
                        key=g_key,
                        label=g_meta["label"],
                        iconName=g_meta["iconName"],
                        count=len(group_candidates),
                        subgroups=subgroups_list,
                        items=[],
                    )
                )
            else:
                groups.append(
                    NavigationGroup(
                        key=g_key,
                        label=g_meta["label"],
                        iconName=g_meta["iconName"],
                        count=len(group_candidates),
                        subgroups=[],
                        items=group_candidates,
                    )
                )

        return NavigationMenuResponse(
            totalItems=len(all_items),
            permittedItems=len(permitted_items_list),
            groups=groups,
            allItems=all_items if is_admin else permitted_items_list,
        )

    @staticmethod
    def get_quick_cards(current_user: User) -> list[QuickCardItem]:
        """Fetch dashboard quick management module cards dynamically for user role."""
        is_manager = bool(current_user.role and current_user.role.code == "MANAGER")
        is_admin = bool(
            current_user.role
            and current_user.role.code in ("ADMIN", "ERP ADMIN", "SUPERADMIN")
        )

        cards: list[QuickCardItem] = [
            QuickCardItem(
                id="users",
                title="Field Team" if is_manager else "User Management",
                subtitle="Assigned MRs & Activity" if is_manager else "Admins, Managers & MRs",
                description=(
                    "Browse your field team members, inspect account profiles and assignments."
                    if is_manager
                    else "Search, filter, paginate and inspect user profiles across all roles and territories."
                ),
                path="/team" if is_manager else "/users",
                icon="UserOutlined",
                color="#006A4E",
                bgColor="#E8F5E9",
                buttonText="View Team" if is_manager else "Open Users",
                requiredPermission="users:read",
            ),
            QuickCardItem(
                id="customers",
                title="Customer Directory",
                subtitle="Doctors, Hospitals, Chemists, Stockists",
                description="Explore registered doctors, healthcare institutions, retail chemists, and distribution stockists with real-time server queries.",
                path="/customers",
                icon="MedicineBoxOutlined",
                color="#0284C7",
                bgColor="#EBF3FC",
                buttonText="Browse Customers",
                requiredPermission="customers:read",
            ),
            QuickCardItem(
                id="approvals",
                title="Approvals Inbox",
                subtitle="Pending Tour, Leave & Expense Approvals",
                description="Review and authorize field force leave requests, monthly tour programmes, and expense claim disbursements.",
                path="/utility/visit-approvals/leave-approval",
                icon="AuditOutlined",
                color="#D97706",
                bgColor="#FEF3C7",
                buttonText="Open Approvals",
                requiredPermission="approvals:read",
            ),
            QuickCardItem(
                id="reports",
                title="Team Reports" if is_manager else "Executive Reports",
                subtitle="Coverage & DCR Analysis",
                description="Generate comprehensive field performance reports, call coverage rates, and export to PDF/Excel.",
                path="/reports/dcr-report",
                icon="BarChartOutlined",
                color="#16A34A",
                bgColor="#F0FDF4",
                buttonText="View Reports",
                requiredPermission="reports:read",
            ),
        ]

        if is_admin:
            cards.extend([
                QuickCardItem(
                    id="masters",
                    title="Master Data",
                    subtitle="Divisions, Specializations & Classes",
                    description="Configure company divisions, doctor categories, product catalogs, and state/city masters.",
                    path="/parameters/state",
                    icon="DatabaseOutlined",
                    color="#006A4E",
                    bgColor="#E8F5E9",
                    buttonText="Open Masters",
                    requiredPermission="masters:read",
                ),
                QuickCardItem(
                    id="territories",
                    title="Territories & HQs",
                    subtitle="Geographical Sales Beats",
                    description="Define headquarters clusters, territory geographical bounds, and representative assignments.",
                    path="/masters/company/territory",
                    icon="EnvironmentOutlined",
                    color="#7E22CE",
                    bgColor="#F3E8FF",
                    buttonText="Manage Territories",
                    requiredPermission="territories:read",
                ),
            ])

        return cards

    @staticmethod
    def get_mobile_drawer_items(current_user: User) -> list[MobileDrawerItem]:
        """Fetch mobile drawer menu items dynamically."""
        return [
            MobileDrawerItem(key="change_territory", label="Change Territory", icon="location-outline", route="ChangeTerritory"),
            MobileDrawerItem(key="my_visits", label="My Visits", icon="calendar-outline", route="MyVisits"),
            MobileDrawerItem(key="reports", label="Reports", icon="bar-chart-outline", route="ReportsCatalog"),
            MobileDrawerItem(key="sample_receive", label="Sample Receive", icon="cube-outline", route="SampleReceive"),
            MobileDrawerItem(key="reimbursement", label="Reimbursement", icon="cash-outline", route="ExpenseList"),
            MobileDrawerItem(key="dr_monthly_business", label="Dr. Monthly Business", icon="trending-up-outline", route="MonthlyBusiness"),
            MobileDrawerItem(key="near_by_me", label="Near By Me", icon="navigate-outline", route="NearByMe"),
            MobileDrawerItem(key="employee_route", label="Employee Route", icon="map-outline", route="EmployeeRoute"),
            MobileDrawerItem(key="settings", label="Settings", icon="settings-outline", route="Settings"),
            MobileDrawerItem(key="whats_new", label="What's New", icon="information-circle-outline", route="WhatsNew"),
        ]
