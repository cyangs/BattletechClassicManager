# This is a sample Python script.

from config import SessionLocal
from mech_repository import MechRepository
from weapon_repository import WeaponRepository
from backend.importer.mech_importer import MechImporter

def print_hi(name):
    # Create distinct data layers sharing the same connection pool
    weapon_db = WeaponRepository(SessionLocal)
    mech_db = MechRepository(SessionLocal)

    # Instantiate the engine passing BOTH references
    importer = MechImporter(weapon_repository=weapon_db, mech_repository=mech_db)
    importer.import_from_flechs_sheets("backend/resource/flechs")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')


