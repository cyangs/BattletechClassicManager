from sqlalchemy import select
from enums import TechBaseEnum
from mech import Mech
from weapon import Weapon, MechWeapon


class MechRepository:
    def __init__(self, session_factory):
        self.SessionLocal = session_factory

    def get_or_create_mech(self, name: str, tech_base: TechBaseEnum, model: str, tonnage: int) -> Mech:
        with self.SessionLocal() as session:
            with session.begin():
                stmt = select(Mech).where(Mech.name == name)
                mech = session.execute(stmt).scalar_one_or_none()
                if not mech:
                    mech = Mech(name=name, tech_base=tech_base, model=model, tonnage=tonnage)
                    session.add(mech)
                    session.flush()
                return mech

    def link_weapon_to_mech(self, mech_id: int, weapon_name: str, count: int, location: str) -> None:
        with self.SessionLocal() as session:
            with session.begin():
                w_stmt = select(Weapon).where(Weapon.name == weapon_name)
                weapon = session.execute(w_stmt).scalar_one_or_none()
                if not weapon:
                    return

                link = MechWeapon(mech_id=mech_id, weapon_id=weapon.id, count=count, location=location)
                session.add(link)
