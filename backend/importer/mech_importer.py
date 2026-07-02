import json
import re
from pathlib import Path

# Explicitly import your separated repository classes for type hinting
from dao.weapon_repository import WeaponRepository
from dao.mech_repository import MechRepository
from enums import TechBaseEnum


class MechImporter:
    def __init__(self, weapon_repository: WeaponRepository, mech_repository: MechRepository):
        """Inject both specialized repositories to coordinate data layers."""
        self.weapon_repo = weapon_repository
        self.mech_repo = mech_repository

    def import_from_flechs_sheets(self, folder_path: str) -> None:
        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            print(f"Directory not found: {folder}")
            return

        # Initialize a set to collect unique weapon data across all files first
        # This prevents unique constraint errors by filtering out duplicates
        unique_weapons = set()

        # A list to keep track of mechs and their weapons for the second pass
        parsed_mechs_queue = []

        print(f"Scanning '{folder}' for operational layouts...")

        # --- STEP 1: PARSE THE FILES AND COLLECT WEAPON TYPES ---
        for file_path in folder.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    parsed_json = json.load(file)
                    sheets = parsed_json.get("sheets", [])

                    for sheet in sheets:
                        # Extract core Mech data
                        mech_name = sheet.get("designation")
                        meta_data = sheet.get("meta", {})
                        tonnage = meta_data.get("mass", 20)
                        src_mtf_string = meta_data.get("srcMTF", "")

                        tech_base_match = match = re.search(r"TechBase:(.*)", src_mtf_string)
                        tech_base = None
                        if match:
                            tech_base = tech_base_match.group(1).strip()
                            try:
                                tech_base = TechBaseEnum(tech_base)
                            except ValueError:
                                print(f"Error: '{tech_base}' is not a valid TechBase.")

                        # Prepare a sub-list to hold weapons specifically for this single mech
                        mech_weapons_list = []

                        # Isolate the Weapons text block
                        flechs_pattern = r"(Weapons:.*?\n\n)"
                        match_block = re.search(flechs_pattern, src_mtf_string, re.DOTALL)

                        if match_block:
                            extracted_text = match_block.group(1)
                            split_pattern = r"\s+(?=\d+\s+)"
                            lines = re.split(split_pattern, extracted_text.strip())

                            # Regex handles Count, Name, Location, and Optional Ammo digits
                            weapon_pattern = r"^(\d+)\s+([^,]+),\s*([^,\n]+?)(?:,\s*Ammo:(\d+))?$"

                            for line in lines:
                                clean_line = line.strip()
                                if clean_line.startswith("Weapons:"):
                                    continue

                                match_weapon = re.match(weapon_pattern, clean_line)
                                if match_weapon:
                                    count = int(match_weapon.group(1).strip())
                                    weapon_name = match_weapon.group(2).strip()
                                    location = match_weapon.group(3).strip()
                                    ammo_string = match_weapon.group(4)
                                    use_ammo = True if ammo_string else False

                                    # 1. Add weapon profile to our global deduping set
                                    unique_weapons.add((weapon_name, use_ammo))

                                    # 2. Track this placement info locally for this specific mech
                                    mech_weapons_list.append({
                                        "name": weapon_name,
                                        "count": count,
                                        "location": location
                                    })

                        # Store everything we need to construct the Mech configuration later
                        parsed_mechs_queue.append({
                            "mech_name": mech_name,
                            "tonnage": tonnage,
                            "tech_base": tech_base,
                            "weapons": mech_weapons_list
                        })

            except Exception as e:
                print(f"❌ Error extracting data from {file_path.name}: {e}")

        # --- STEP 2: INSERT MASTER WEAPONS (GLOBAL CATALOG) ---
        print(f"\nPopulating master weapons catalog ({len(unique_weapons)} types)...")
        for weapon_name, use_ammo in unique_weapons:
            # Delegate directly to the weapon repository
            self.weapon_repo.save_weapon(
                name=weapon_name,
                use_ammo=use_ammo,
                damage=10,  # Default placeholder stats
                heat=5
            )

        # --- STEP 3: INSERT MECHS AND ESTABLISH RELATIONSHIPS ---
        print("\nConstructing Mech units and linking weapons configuration lists...")
        for mech_data in parsed_mechs_queue:
            print(f"🤖 Processing BattleMech: {mech_data['mech_name']}")

            # Delegate to the Mech repository to get or create the core entity row
            mech_record = self.mech_repo.get_or_create_mech(
                name=mech_data["mech_name"],
                tech_base=mech_data["tech_base"],
                model="fooo",
                tonnage=mech_data["tonnage"],
            )

            # Link each individual weapon placement to that specific mech record ID
            for w in mech_data["weapons"]:
                self.mech_repo.link_weapon_to_mech(
                    mech_id=mech_record.id,
                    weapon_name=w["name"],
                    count=w["count"],
                    location=w["location"]
                )
                print(f"   ↳ Linked {w['count']}x {w['name']} to the {w['location']}")

        print("\n🎉 All components successfully separated and imported!")
