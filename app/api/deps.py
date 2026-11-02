from app.db.session import get_db

# re-exported here so routers import dependencies from one place
__all__ = ["get_db"]
