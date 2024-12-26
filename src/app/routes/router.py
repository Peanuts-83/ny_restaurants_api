from fastapi import APIRouter

from .restaurant_routes import rest_router as restaurant_router
from .neighborhood_routes import neighb_router as neighborhood_router
from .borough_routes import borough_router
from .point_routes import point_router

router = APIRouter()

# include sub-routers
router.include_router(restaurant_router)
router.include_router(neighborhood_router)
router.include_router(borough_router)
router.include_router(point_router)