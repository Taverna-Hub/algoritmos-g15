from app.routes.devices import router as devices_router
from app.routes.history import router as history_router
from app.routes.sensors import router as sensors_router

__all__ = ["devices_router", "history_router", "sensors_router"]
