"""Navigation menu Pydantic schemas."""

from pydantic import BaseModel, ConfigDict, Field


class NavigationItem(BaseModel):
    """Single menu navigation item."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    key: str
    label: str
    path: str
    group: str
    group_label: str = Field(alias="groupLabel")
    subgroup: str | None = None
    required_permission: str | None = Field(default=None, alias="requiredPermission")
    status: str
    tier: str
    our_app: str = Field(alias="ourApp")
    purpose: str
    is_permitted: bool = Field(default=True, alias="isPermitted")


class NavigationSubgroup(BaseModel):
    """Subgroup container inside a main navigation group."""

    name: str
    items: list[NavigationItem]


class NavigationGroup(BaseModel):
    """Main navigation category group."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    key: str
    label: str
    icon_name: str = Field(alias="iconName")
    count: int
    subgroups: list[NavigationSubgroup] = []
    items: list[NavigationItem] = []


class NavigationMenuResponse(BaseModel):
    """Full navigation hierarchy response."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    total_items: int = Field(alias="totalItems")
    permitted_items: int = Field(alias="permittedItems")
    groups: list[NavigationGroup]
    all_items: list[NavigationItem] = Field(alias="allItems")


class QuickCardItem(BaseModel):
    """Quick management module card for web dashboard."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    subtitle: str
    description: str
    path: str
    icon: str
    color: str
    bg_color: str = Field(alias="bgColor")
    button_text: str = Field(alias="buttonText")
    required_permission: str | None = Field(default=None, alias="requiredPermission")


class MobileDrawerItem(BaseModel):
    """Drawer menu item for mobile application."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    key: str
    label: str
    icon: str
    route: str
    badge: str | None = None

