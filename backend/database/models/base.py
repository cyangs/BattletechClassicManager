from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """The shared metadata registry for all application tables."""
    pass