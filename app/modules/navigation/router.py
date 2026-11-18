"""Navigation REST API router."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.modules.navigation.schemas import (
    MobileDrawerItem,
    NavigationMenuResponse,
    QuickCardItem,
)
from app.modules.navigation.service import NavigationService
from app.modules.users.models import User

router = APIRouter(prefix="/navigation", tags=["Navigation"])


@router.get(
    "/menu",
    response_model=NavigationMenuResponse,
    summary="Get dynamic navigation menu tree filtered by user permissions",
)
def get_navigation_menu(
    current_user: User = Depends(get_current_user),
) -> NavigationMenuResponse:
    """Fetch complete hierarchical navigation tree with permissions and counts."""
    return NavigationService.get_navigation_menu(current_user=current_user)


@router.get(
    "/quick-cards",
    response_model=list[QuickCardItem],
    summary="Get dynamic quick dashboard module cards",
)
def get_quick_cards(
    current_user: User = Depends(get_current_user),
) -> list[QuickCardItem]:
    """Fetch dashboard management quick cards configured for user role."""
    return NavigationService.get_quick_cards(current_user=current_user)


@router.get(
    "/mobile-drawer",
    response_model=list[MobileDrawerItem],
    summary="Get dynamic mobile app drawer items",
)
def get_mobile_drawer_items(
    current_user: User = Depends(get_current_user),
) -> list[MobileDrawerItem]:
    """Fetch dynamic mobile drawer navigation items."""
    return NavigationService.get_mobile_drawer_items(current_user=current_user)

