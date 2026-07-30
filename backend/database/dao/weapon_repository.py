from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List
from database.models.weapon import Weapon

class WeaponRepository:
    def __init__(self, session_factory):
        self.SessionLocal = session_factory


    def save_weapon(self, name: str, use_ammo: bool, damage: int, heat: int) -> Weapon | None:
        """Saves a new weapon to the database. Returns the object or None if it exists."""
        # Using 'with' handles session opening/closing automatically
        with self.SessionLocal() as session:
            try:
                # Open a secure transaction
                with session.begin():
                    new_weapon = Weapon(name=name, use_ammo=use_ammo, damage=damage, heat=heat)
                    session.add(new_weapon)

                # Transaction auto-commits here if no error occurred
                return new_weapon

            except IntegrityError:
                # Safe rollback triggers automatically on exceptions
                print(f"- Weapon '{name}' already exists in the database. Skipping")
                return None

    def fetch_all_weapons(self) -> List[Weapon]:
        """Fetches every weapon record available in the database table."""
        with (self.SessionLocal() as session):
            # 2.0 Style: Explicitly execute a select statement construct
            statement = select(Weapon).order_by(Weapon.name)
            result = session.execute(statement)
            return list(result.scalars().all())

    def fetch_weapon_by_name(self, name: str) -> Weapon | None:
        """Finds a single weapon tracking its unique name string."""
        with self.SessionLocal() as session:
            statement = select(Weapon).where(Weapon.name == name)
            result = session.execute(statement)
            return result.scalar_one_or_none()
