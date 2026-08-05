from enum import Enum

# 1. Define your Enum choices
class TechBaseEnum(Enum):
    CLAN = "CLAN"
    IS = "IS"
    MIXED = "MIXED"

    @classmethod
    def _missing_(cls, value):
        # 1. Ensure the incoming value is a string
        if isinstance(value, str):
            # 2. Clean up spaces and convert to lowercase
            clean_value = value.strip().lower()

            # 3. Check if it matches any of the enum values
            for member in cls:
                if member.value == clean_value:
                    return member

        # Return None if no match is found (Python will then raise a ValueError)
        return None

class AttachmentType(Enum):
    MECH = "mech"
    WEAPON = "weapon"


class WeaponType(Enum):
    MISSILE = "MISSILE"
    BALLISTIC = "BALLISTIC"
    LASER = "LASER"
    PPC = "PPC"
    ARTY = "ARTY"
    OTHER = "OTHER"