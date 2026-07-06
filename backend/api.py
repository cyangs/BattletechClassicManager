import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Import your shared configurations and models
from config import SessionLocal
#  To this absolute package layout path:
from database.models.mech import Mech
from database.models.weapon import MechWeapon, Weapon
from database.models.enums import TechBaseEnum
import sqlalchemy as sa

from database.models.session import SessionMech, Session
from game.combat import CombatResolver

app = FastAPI(title="BattleTech Classic Manager API")

# --- CONFIGURE CORS ---
# This allows your React app (running on localhost:3000 or 5173) to fetch data safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your exact frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from pydantic import BaseModel, Field
from typing import List, Optional


# Request validation schemas
class CreateSessionRequest(BaseModel):
    name: str
    enemy_mech_ids: List[int] = []  # chassis to deploy as the opposing force

class AddMechsRequest(BaseModel):
    mech_ids: List[int]
    team: str = "player"  # "player" (friendly) or "enemy"

class FireWeaponsRequest(BaseModel):
    mech_id: int
    weapon_link_ids: List[int]  # MechWeapon.id values that were selected to fire
    target_mech_id: Optional[int] = None  # master Mech id of the enemy being fired upon
    facing: str = "Front/Rear"  # target arc: "Left Side", "Front/Rear", "Right Side"
    distance: int = 0 # the distance in hexes to the target
    target_movement_modifier: int = 0  # to-hit penalty from the target's movement


class WeaponSaveRequest(BaseModel):
    id: Optional[int] = None  # Included if we are updating an existing row
    name: str = Field(..., min_length=1, max_length=50)  # internal SKU
    full_name: Optional[str] = Field(None, max_length=100)  # display name
    use_ammo: bool = False
    damage: int = Field(..., ge=0)
    heat: int = Field(..., ge=0)
    minimum_range: Optional[int] = Field(None, ge=0)
    short_range: Optional[int] = Field(None, ge=0)
    medium_range: Optional[int] = Field(None, ge=0)
    long_range: Optional[int] = Field(None, ge=0)


# Request Validation Schema using Pydantic
class MechSaveRequest(BaseModel):
    id: Optional[int] = None  # Included if we are updating an existing row
    designation: str = Field(..., min_length=1, max_length=100)
    model: Optional[str] = "Prime"
    mass: int = Field(..., ge=20, le=100)  # mechs range from 20 to 100 tons
    tech_base: str  # "clan" or "inner_sphere"
    uuid: Optional[str] = None


class AddWeaponLinkRequest(BaseModel):
    weapon_id: int
    count: int = Field(1, ge=1)
    location: str = Field(..., min_length=1, max_length=50)


@app.post("/api/mechs/save")
def save_or_update_mech(payload: MechSaveRequest):
    with SessionLocal() as session:
        with session.begin():
            try:
                tech_enum = TechBaseEnum(payload.tech_base)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid tech_base value. Use 'clan', 'is', or 'mixed'")

            # --- UPDATE PATH ---
            if payload.id:
                mech = session.get(Mech, payload.id)
                if not mech:
                    raise HTTPException(status_code=404, detail="Target BattleMech row not found")

                mech.name = payload.designation  # Maps to your database name/designation column
                mech.model = payload.model
                mech.tonnage = payload.mass
                mech.tech_base = tech_enum
                mech.uuid = payload.uuid
                status = "updated"

            # --- CREATE PATH ---
            else:
                # Check for a unique constraint designation clash before inserting
                existing = session.execute(sa.select(Mech).where(Mech.name == payload.designation)).scalar_one_or_none()
                if existing:
                    raise HTTPException(status_code=400,
                                        detail=f"A Mech designated '{payload.designation}' already exists.")

                mech = Mech(
                    name=payload.designation,
                    model=payload.model,
                    tonnage=payload.mass,
                    tech_base=tech_enum,
                )
                session.add(mech)
                status = "created"

            session.flush()  # Forces ID tracking assignment generation
            return {"status": "success", "action": status, "mech_id": mech.id}


@app.post("/api/mechs/{mech_id}/weapons")
def add_weapon_to_mech(mech_id: int, payload: AddWeaponLinkRequest):
    """Mounts a weapon from the catalog onto a mech at a given location."""
    with SessionLocal() as session:
        with session.begin():
            if not session.get(Mech, mech_id):
                raise HTTPException(status_code=404, detail="Target BattleMech row not found")
            if not session.get(Weapon, payload.weapon_id):
                raise HTTPException(status_code=404, detail="Weapon not found in catalog")

            link = MechWeapon(
                mech_id=mech_id,
                weapon_id=payload.weapon_id,
                count=payload.count,
                location=payload.location,
            )
            session.add(link)
            session.flush()  # Assign the link id
            return {"status": "success", "link_id": link.id}


@app.delete("/api/mechs/{mech_id}/weapons/{link_id}")
def remove_weapon_from_mech(mech_id: int, link_id: int):
    with SessionLocal() as session:
        with session.begin():
            link = session.get(MechWeapon, link_id)
            if not link or link.mech_id != mech_id:
                raise HTTPException(status_code=404, detail="Weapon hardpoint not found on this mech")
            session.delete(link)
            return {"status": "removed", "link_id": link_id}


@app.post("/api/sessions")
def create_session(payload: CreateSessionRequest):
    with SessionLocal() as session:
        with session.begin():
            new_session = Session(name=payload.name)
            session.add(new_session)
            session.flush() # Populate the ID

            # Deploy any chosen enemy chassis straight into the new lobby.
            for m_id in payload.enemy_mech_ids:
                if not session.get(Mech, m_id):
                    raise HTTPException(status_code=404, detail=f"Enemy chassis {m_id} not found")
                session.add(SessionMech(session_id=new_session.id, mech_id=m_id, team="enemy"))

            return {
                "id": new_session.id,
                "name": new_session.name,
                "status": new_session.status,
                "current_turn": new_session.current_turn,
            }


@app.post("/api/sessions/{session_id}/start")
def start_session(session_id: int):
    """Kicks a lobby session into play: status -> in_progress, turn -> 1."""
    with SessionLocal() as session:
        with session.begin():
            game = session.get(Session, session_id)
            if not game:
                raise HTTPException(status_code=404, detail="Game session not found")
            if not game.mechs:
                raise HTTPException(status_code=400, detail="Add at least one mech before starting")
            game.status = "in_progress"
            game.current_turn = 1
            return {"status": game.status, "current_turn": game.current_turn}


@app.post("/api/sessions/{session_id}/turn")
def run_turn(session_id: int):
    """Advances the session to the next turn."""
    with SessionLocal() as session:
        with session.begin():
            game = session.get(Session, session_id)
            if not game:
                raise HTTPException(status_code=404, detail="Game session not found")
            if game.status != "in_progress":
                raise HTTPException(status_code=400, detail="Session has not been started")
            game.current_turn += 1
            return {"status": game.status, "current_turn": game.current_turn}


@app.post("/api/sessions/{session_id}/fire")
def fire_weapons(session_id: int, payload: FireWeaponsRequest):
    """Resolves a mech firing its selected weapons (placeholder combat logic)."""
    with SessionLocal() as session:
        game = session.get(Session, session_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game session not found")

        mech = session.execute(
            select(Mech)
            .options(selectinload(Mech.weapon_links).selectinload(MechWeapon.weapon))
            .where(Mech.id == payload.mech_id)
        ).scalar_one_or_none()
        if not mech:
            raise HTTPException(status_code=404, detail="Mech not found")

        selected_ids = set(payload.weapon_link_ids)
        weapons = [{
            "name": link.weapon.full_name or link.weapon.name,
            "count": link.count,
            "damage": link.weapon.damage,
            "heat": link.weapon.heat,
            "location": link.location,
        } for link in mech.weapon_links if link.id in selected_ids]

        if not weapons:
            raise HTTPException(status_code=400, detail="No weapons selected to fire")

        target_name = None
        if payload.target_mech_id is not None:
            target = session.get(Mech, payload.target_mech_id)
            if not target:
                raise HTTPException(status_code=404, detail="Target mech not found")
            target_name = target.name

        result = CombatResolver().resolve_fire(
            mech.name,
            weapons,
            target_name=target_name,
            facing=payload.facing,
            target_movement_modifier=payload.target_movement_modifier,
        )
        result["turn"] = game.current_turn
        return result

@app.post("/api/sessions/{session_id}/mechs")
def add_mechs_to_session(session_id: int, payload: AddMechsRequest):
    with SessionLocal() as session:
        with session.begin():
            if not session.get(Session, session_id):
                raise HTTPException(status_code=404, detail="Game session not found")
            inserted_units = []
            for m_id in payload.mech_ids:
                unit = SessionMech(session_id=session_id, mech_id=m_id, team=payload.team)
                session.add(unit)
                inserted_units.append(m_id)
            return {"status": "success", "added_mech_ids": inserted_units}


@app.get("/api/sessions")
def get_all_sessions():
    """Lists every game session with the roster of mechs deployed into it."""
    with SessionLocal() as session:
        stmt = (
            select(Session)
            .options(selectinload(Session.mechs).selectinload(SessionMech.master_mech))
            .order_by(Session.id)
        )
        sessions = session.execute(stmt).scalars().all()

        data = []
        for s in sessions:
            units = []
            for unit in s.mechs:
                m = unit.master_mech
                units.append({
                    "id": unit.id,           # session_mech row id (used for removal)
                    "mech_id": unit.mech_id,
                    "team": unit.team,
                    "name": m.name if m else "Unknown Chassis",
                    "tonnage": m.tonnage if m else None,
                    "tech_base": m.tech_base.name.lower() if m and hasattr(m.tech_base, "name") else None,
                })
            data.append({
                "id": s.id,
                "name": s.name,
                "status": s.status,
                "current_turn": s.current_turn,
                "mechs": units,
            })
        return data


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int):
    with SessionLocal() as session:
        with session.begin():
            target = session.get(Session, session_id)
            if not target:
                raise HTTPException(status_code=404, detail="Game session not found")
            session.delete(target)  # cascade removes its session_mechs
            return {"status": "deleted", "session_id": session_id}


@app.delete("/api/sessions/{session_id}/mechs/{session_mech_id}")
def remove_mech_from_session(session_id: int, session_mech_id: int):
    with SessionLocal() as session:
        with session.begin():
            unit = session.get(SessionMech, session_mech_id)
            if not unit or unit.session_id != session_id:
                raise HTTPException(status_code=404, detail="Mech not found in this session")
            session.delete(unit)
            return {"status": "removed", "session_mech_id": session_mech_id}


@app.post("/api/weapons/save")
def save_or_update_weapon(payload: WeaponSaveRequest):
    with SessionLocal() as session:
        with session.begin():
            # --- UPDATE PATH ---
            if payload.id:
                weapon = session.get(Weapon, payload.id)
                if not weapon:
                    raise HTTPException(status_code=404, detail="Target weapon row not found")

                # Guard the unique name constraint against a different existing row
                clash = session.execute(
                    sa.select(Weapon).where(Weapon.name == payload.name, Weapon.id != payload.id)
                ).scalar_one_or_none()
                if clash:
                    raise HTTPException(status_code=400,
                                        detail=f"A weapon named '{payload.name}' already exists.")
                status = "updated"

            # --- CREATE PATH ---
            else:
                existing = session.execute(
                    sa.select(Weapon).where(Weapon.name == payload.name)
                ).scalar_one_or_none()
                if existing:
                    raise HTTPException(status_code=400,
                                        detail=f"A weapon named '{payload.name}' already exists.")
                weapon = Weapon()
                session.add(weapon)
                status = "created"

            weapon.name = payload.name
            weapon.full_name = payload.full_name
            weapon.use_ammo = payload.use_ammo
            weapon.damage = payload.damage
            weapon.heat = payload.heat
            weapon.minimum_range = payload.minimum_range
            weapon.short_range = payload.short_range
            weapon.medium_range = payload.medium_range
            weapon.long_range = payload.long_range

            session.flush()  # Forces ID assignment for the create path
            return {"status": "success", "action": status, "weapon_id": weapon.id}


@app.get("/api/weapons")
def get_all_weapons():
    """Returns the full weapons_master catalog for the Weapons Library tab."""
    with SessionLocal() as session:
        weapons = session.execute(select(Weapon).order_by(Weapon.name)).scalars().all()
        return [{
            "id": w.id,
            "name": w.name,
            "full_name": w.full_name,
            "use_ammo": w.use_ammo,
            "damage": w.damage,
            "heat": w.heat,
            "minimum_range": w.minimum_range,
            "short_range": w.short_range,
            "medium_range": w.medium_range,
            "long_range": w.long_range,
        } for w in weapons]


@app.get("/api/mechs")
def get_all_mechs():
    """
    Fetches all Mechs from PostgreSQL, including their nested weapon hardpoint
    configurations and individual weapon stats, formatted cleanly for React.
    """
    # Open a clean database session
    with SessionLocal() as session:
        try:
            # SQLAlchemy 2.0 select statement
            # selectinload() handles the JOIN operations efficiently behind the scenes
            stmt = (
                select(Mech)
                .options(
                    selectinload(Mech.weapon_links).selectinload(MechWeapon.weapon)
                )
                .order_by(Mech.name)
            )

            result = session.execute(stmt)
            mechs = result.scalars().all()

            # --- FORMAT DATA FOR REACT ---
            response_data = []
            for mech in mechs:
                # Format the nested weapons list
                weapons_payload = []
                for link in mech.weapon_links:
                    weapons_payload.append({
                        "id": link.id,
                        "count": link.count,
                        "location": link.location,
                        "weapon": {
                            "name": link.weapon.name,
                            "full_name": link.weapon.full_name,
                            "use_ammo": link.weapon.use_ammo,
                            "damage": link.weapon.damage,
                            "heat": link.weapon.heat
                        }
                    })

                # Construct the master Mech object
                response_data.append({
                    "id": mech.id,
                    "name": mech.name,
                    "model": mech.model,
                    "tech_base": mech.tech_base.name.lower() if hasattr(mech.tech_base, 'name') else str(
                        mech.tech_base),
                    "tonnage": mech.tonnage,
                    "weapon_links": weapons_payload
                })

            return response_data

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database retrieval failure: {str(e)}")


# --- LAUNCHER ---
if __name__ == "__main__":
    # Start the server on localhost port 8000
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
