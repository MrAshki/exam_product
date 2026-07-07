from sqlalchemy.orm import Session


def init_db(db: Session) -> None:
    """Database bootstrap hook.

    Schema changes should be managed with Alembic migrations. Seed data can be
    added here in later phases if the product needs it.
    """
    return None
