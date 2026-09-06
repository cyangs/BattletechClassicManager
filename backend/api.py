import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import os
import subprocess
from urllib.parse import urlparse

# Import your shared configurations and models
from config import SessionLocal, DATABASE_URL
#  To this absolute package layout path:
from database.models.mech import Mech
from database.models.weapon import MechWeapon, Weapon
from database.models.attachments import Attachments
from database.models.ammo_type import AmmoType
from database.models.enums import TechBaseEnum, AttachmentType, WeaponType
import sqlalchemy as sa

from database.models.session import (
    SessionMech,
    Session,
    SessionEvent,
    SessionWeaponState,
    SessionMechWeapon,
    SessionMechAttachment,
)
from database.dao.weapon_repository import WeaponRepository
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
    pilot_name: Optional[str] = None            # persists on the unit for the session
    pilot_gunnery_skill: int = Field(4, ge=0, le=8)  # base to-hit number (0 best, 8 worst)
    accent_color: Optional[str] = None          # palette label ('amber', 'sky', …) or None

class FireWeaponsRequest(BaseModel):
    mech_id: int                            # master Mech id of the firing chassis (fallback label)
    session_mech_id: int                    # SessionMech id of the firing unit
    weapon_link_ids: List[int]              # SessionMechWeapon.id values that were selected to fire
    double_tap_ids: List[int] = []          # SessionMechWeapon.id values firing double-tap (ULTRA ballistics)
    pilot_gunnery_skill: int = 4            # attacker's gunnery skill (base to-hit number)
    target_mech_id: Optional[int] = None    # master Mech id of the enemy being fired upon
    facing: str = "Front/Rear"              # target arc: "Left Side", "Front/Rear", "Right Side"
    distance_modifier: int = 0              # the distance in hexes to the target
    additional_modifier: int = 0            # any additional modifiers, such as partial cover, intervening terrain...
    self_movement_modifier: int = 0         # to-hit penalty from self movement modifier
    target_movement_modifier: int = 0       # to-hit penalty from the target's movement
    partial_cover: bool = False             # if the target is partially obscured


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
    # Per-range-band to-hit modifiers (may be negative, e.g. pulse lasers).
    short_range_modifier: Optional[int] = None
    medium_range_modifier: Optional[int] = None
    long_range_modifier: Optional[int] = None
    # Cluster weapons: shot count and damage per cluster hit.
    num_shots: Optional[int] = Field(None, ge=1)
    cluster_damage: Optional[int] = Field(None, ge=0)
    # Weapon system category (MISSILE, BALLISTIC, LASER, PPC, ARTY, OTHER).
    type: Optional[str] = None
    # Free-form JSON blob (e.g. {"weapon_type": "ULTRA"} for autocannons).
    modifications: Optional[dict] = None


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


class AddMechAttachmentRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)  # attachments.sku to fit


class WeaponStateRequest(BaseModel):
    session_weapon_id: int   # SessionMechWeapon.id to toggle
    disabled: bool


class WeaponDestroyedRequest(BaseModel):
    session_weapon_id: int   # SessionMechWeapon.id to toggle
    destroyed: bool


class AttachmentDestroyedRequest(BaseModel):
    session_attachment_id: int   # SessionMechAttachment.id to toggle
    destroyed: bool


class AttachmentSaveRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)          # primary key, e.g. "ARTEMISIV"
    display_name: str = Field(..., min_length=1, max_length=100)
    to_hit_modifier: Optional[int] = None
    cluster_modifier: Optional[int] = None
    tonnage: Optional[float] = None
    description: Optional[str] = None


class AmmoSaveRequest(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)          # primary key, e.g. "INFERNO"
    display_name: str = Field(..., min_length=1, max_length=100)
    damage: Optional[int] = None
    heat: Optional[int] = None
    special_effect: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


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


@app.post("/api/mechs/{mech_id}/attachments")
def add_attachment_to_mech(mech_id: int, payload: AddMechAttachmentRequest):
    """Fits a chassis-level attachment (attachment_type "mech") onto a mech."""
    with SessionLocal() as session:
        with session.begin():
            mech = session.execute(
                select(Mech)
                .options(selectinload(Mech.attachments))
                .where(Mech.id == mech_id)
            ).scalar_one_or_none()
            if not mech:
                raise HTTPException(status_code=404, detail="Target BattleMech row not found")

            attachment = session.get(Attachments, payload.sku)
            if not attachment:
                raise HTTPException(status_code=404, detail="Attachment not found in catalog")
            if attachment.attachment_type != AttachmentType.MECH:
                raise HTTPException(status_code=400,
                                    detail="Only 'mech' attachments can be fitted to a chassis")

            if attachment not in mech.attachments:
                mech.attachments.append(attachment)
            return {"status": "success", "mech_id": mech_id, "sku": payload.sku}


@app.delete("/api/mechs/{mech_id}/attachments/{sku}")
def remove_attachment_from_mech(mech_id: int, sku: str):
    with SessionLocal() as session:
        with session.begin():
            mech = session.execute(
                select(Mech)
                .options(selectinload(Mech.attachments))
                .where(Mech.id == mech_id)
            ).scalar_one_or_none()
            if not mech:
                raise HTTPException(status_code=404, detail="Target BattleMech row not found")

            attachment = next((a for a in mech.attachments if a.sku == sku), None)
            if not attachment:
                raise HTTPException(status_code=404, detail="Attachment not fitted to this mech")
            mech.attachments.remove(attachment)
            return {"status": "removed", "mech_id": mech_id, "sku": sku}


def _deploy_unit(db, session_id: int, master: "Mech", *, team: str,
                 pilot_name: Optional[str] = None, pilot_gunnery_skill: int = 4,
                 accent_color: Optional[str] = None) -> SessionMech:
    """Create a SessionMech and snapshot the master mech's loadout into
    session-owned rows. A master mount of count N becomes N individual weapon
    instances so each can be disabled/destroyed on its own during play."""
    unit = SessionMech(
        session_id=session_id,
        mech_id=master.id,
        team=team,
        pilot_name=pilot_name,
        pilot_gunnery_skill=pilot_gunnery_skill,
        accent_color=accent_color,
    )
    db.add(unit)

    for link in master.weapon_links:
        for _ in range(max(1, link.count)):
            unit.weapons.append(SessionMechWeapon(
                weapon_id=link.weapon_id,
                location=link.location,
            ))

    for attachment in master.attachments:
        unit.attachments.append(SessionMechAttachment(
            attachment_sku=attachment.sku,
        ))

    return unit


@app.post("/api/sessions")
def create_session(payload: CreateSessionRequest):
    with SessionLocal() as session:
        with session.begin():
            new_session = Session(name=payload.name)
            session.add(new_session)
            session.flush() # Populate the ID

            # Deploy any chosen enemy chassis straight into the new lobby.
            for m_id in payload.enemy_mech_ids:
                master = session.get(Mech, m_id)
                if not master:
                    raise HTTPException(status_code=404, detail=f"Enemy chassis {m_id} not found")
                _deploy_unit(session, new_session.id, master, team="enemy")

            return {
                "id": new_session.id,
                "name": new_session.name,
                "status": new_session.status,
                "current_turn": new_session.current_turn,
                "created_on": new_session.created_on,
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


@app.post("/api/sessions/{session_id}/end")
def end_session(session_id: int):
    """Ends a session: status -> completed. No more turns or weapon fire; the
    session becomes a read-only history record."""
    with SessionLocal() as session:
        with session.begin():
            game = session.get(Session, session_id)
            if not game:
                raise HTTPException(status_code=404, detail="Game session not found")
            game.status = "completed"
            return {"status": game.status, "current_turn": game.current_turn}


@app.post("/api/sessions/{session_id}/fire")
def fire_weapons(session_id: int, payload: FireWeaponsRequest):
    """Resolves a mech firing its selected weapons (placeholder combat logic)."""
    with SessionLocal() as session:
        game = session.get(Session, session_id)
        if not game:
            raise HTTPException(status_code=404, detail="Game session not found")
        if game.status == "completed":
            raise HTTPException(status_code=400, detail="Session has ended; weapons cannot fire")

        unit = session.execute(
            select(SessionMech)
            .options(
                selectinload(SessionMech.weapons)
                .selectinload(SessionMechWeapon.weapon),
                selectinload(SessionMech.master_mech),
            )
            .where(SessionMech.id == payload.session_mech_id)
        ).scalar_one_or_none()
        if not unit or unit.session_id != session_id:
            raise HTTPException(status_code=404, detail="Mech not found in this session")

        attacker_name = unit.master_mech.name if unit.master_mech else "Unknown Chassis"

        # TODO swap to session mech ID
        # TODO needed for mech attachments like TC

        # Each entry in weapon_link_ids is one shot, referencing a session-owned
        # weapon instance. A weapon appears once per instance the player chose to
        # fire — duplicates are meaningful and must not be collapsed. Destroyed
        # weapons cannot fire and are silently skipped.
        weapons_by_id = {w.id: w for w in unit.weapons}
        double_tap_ids = set(payload.double_tap_ids)
        # Build the fireable shot list, keeping a per-shot double-tap flag aligned
        # by index with the weapon names (the instance identity is only available
        # here, before names collapse duplicates).
        weapon_names = []
        double_tap_flags = []
        for wid in payload.weapon_link_ids:
            session_weapon = weapons_by_id.get(wid)
            if session_weapon is None or session_weapon.destroyed:
                continue
            weapon_names.append(session_weapon.weapon.name)
            double_tap_flags.append(wid in double_tap_ids)

        if not weapon_names:
            raise HTTPException(status_code=400, detail="No weapons selected to fire")

        target_name = None
        if payload.target_mech_id is not None:
            target = session.get(Mech, payload.target_mech_id)
            if not target:
                raise HTTPException(status_code=404, detail="Target mech not found")
            target_name = target.name

        result = CombatResolver(WeaponRepository(SessionLocal)).resolve_fire(
            unit,
            weapon_names,
            pilot_gunnery_skill=payload.pilot_gunnery_skill,
            target_name=target_name,
            target_facing=payload.facing,
            distance_modifier=payload.distance_modifier,
            additional_modifier=payload.additional_modifier,
            self_movement_modifier=payload.self_movement_modifier,
            target_movement_modifier=payload.target_movement_modifier,
            partial_cover=payload.partial_cover,
            double_tap_flags=double_tap_flags,
        )
        result["turn"] = game.current_turn

        # Log the fire into the session history so Run Turn preserves it and the
        # History view can replay it. The event's presence also marks the unit
        # as having fired this turn (which greys out its Fire button in the UI).
        event = SessionEvent(
            session_id=session_id,
            turn=game.current_turn,
            event_type="fire",
            session_mech_id=payload.session_mech_id,
            attacker=attacker_name,
            target=target_name,
            payload=result,
        )
        session.add(event)
        session.commit()
        result["event_id"] = event.id
        return result


@app.delete("/api/sessions/{session_id}/events/{event_id}")
def undo_event(session_id: int, event_id: int):
    """Removes a logged event (used to undo a weapon fire before the turn ends)."""
    with SessionLocal() as session:
        with session.begin():
            event = session.get(SessionEvent, event_id)
            if not event or event.session_id != session_id:
                raise HTTPException(status_code=404, detail="Event not found in this session")
            session.delete(event)
            return {"status": "removed", "event_id": event_id}


def _get_session_weapon(session, session_id, session_mech_id, weapon_id) -> SessionMechWeapon:
    """Fetch a session-owned weapon instance, verifying it belongs to the given
    unit and session."""
    weapon = session.get(SessionMechWeapon, weapon_id)
    if not weapon or weapon.session_mech_id != session_mech_id:
        raise HTTPException(status_code=404, detail="Weapon not found on this unit")
    unit = weapon.session_mech
    if not unit or unit.session_id != session_id:
        raise HTTPException(status_code=404, detail="Mech not found in this session")
    return weapon


@app.post("/api/sessions/{session_id}/mechs/{session_mech_id}/weapon-state")
def set_weapon_state(session_id: int, session_mech_id: int, payload: WeaponStateRequest):
    """Enable/disable an individual weapon instance on a unit for the session."""
    with SessionLocal() as session:
        with session.begin():
            weapon = _get_session_weapon(session, session_id, session_mech_id, payload.session_weapon_id)
            weapon.disabled = payload.disabled
            return {"status": "success", "session_weapon_id": weapon.id, "disabled": weapon.disabled}


@app.post("/api/sessions/{session_id}/mechs/{session_mech_id}/weapon-destroyed")
def set_weapon_destroyed(session_id: int, session_mech_id: int, payload: WeaponDestroyedRequest):
    """Mark an individual weapon instance destroyed (or repair it) for the session."""
    with SessionLocal() as session:
        with session.begin():
            weapon = _get_session_weapon(session, session_id, session_mech_id, payload.session_weapon_id)
            weapon.destroyed = payload.destroyed
            return {"status": "success", "session_weapon_id": weapon.id, "destroyed": weapon.destroyed}


@app.post("/api/sessions/{session_id}/mechs/{session_mech_id}/attachment-destroyed")
def set_attachment_destroyed(session_id: int, session_mech_id: int, payload: AttachmentDestroyedRequest):
    """Mark a fitted attachment destroyed (or repair it) for the session."""
    with SessionLocal() as session:
        with session.begin():
            attachment = session.get(SessionMechAttachment, payload.session_attachment_id)
            if not attachment or attachment.session_mech_id != session_mech_id:
                raise HTTPException(status_code=404, detail="Attachment not found on this unit")
            unit = attachment.session_mech
            if not unit or unit.session_id != session_id:
                raise HTTPException(status_code=404, detail="Mech not found in this session")
            attachment.destroyed = payload.destroyed
            return {"status": "success", "session_attachment_id": attachment.id, "destroyed": attachment.destroyed}


@app.post("/api/sessions/{session_id}/mechs")
def add_mechs_to_session(session_id: int, payload: AddMechsRequest):
    with SessionLocal() as session:
        with session.begin():
            if not session.get(Session, session_id):
                raise HTTPException(status_code=404, detail="Game session not found")
            inserted_units = []
            for m_id in payload.mech_ids:
                master = session.get(Mech, m_id)
                if not master:
                    raise HTTPException(status_code=404, detail=f"Chassis {m_id} not found")
                _deploy_unit(
                    session, session_id, master,
                    team=payload.team,
                    pilot_name=payload.pilot_name,
                    pilot_gunnery_skill=payload.pilot_gunnery_skill,
                    accent_color=payload.accent_color,
                )
                inserted_units.append(m_id)
            return {"status": "success", "added_mech_ids": inserted_units}


@app.get("/api/sessions")
def get_all_sessions():
    """Lists every game session with the roster of mechs deployed into it."""
    with SessionLocal() as session:
        stmt = (
            select(Session)
            .options(
                selectinload(Session.mechs).selectinload(SessionMech.master_mech),
                selectinload(Session.mechs).selectinload(SessionMech.weapons).selectinload(SessionMechWeapon.weapon),
                selectinload(Session.mechs).selectinload(SessionMech.attachments).selectinload(SessionMechAttachment.attachment),
                selectinload(Session.events),
            )
            .order_by(Session.status.desc())
        )
        sessions = session.execute(stmt).scalars().all()

        data = []
        for s in sessions:
            # Which units have already fired this turn (marks Fire button spent).
            fired_events = {
                e.session_mech_id: e.id
                for e in s.events
                if e.event_type == "fire" and e.turn == s.current_turn
            }
            units = []
            for unit in s.mechs:
                m = unit.master_mech
                # Session-owned loadout (each row is one fireable weapon instance).
                weapons = [{
                    "id": w.id,                    # SessionMechWeapon id (fire/disable/destroy key)
                    "weapon_id": w.weapon_id,
                    "name": w.weapon.name if w.weapon else None,
                    "full_name": w.weapon.full_name if w.weapon else None,
                    "location": w.location,
                    "use_ammo": w.weapon.use_ammo if w.weapon else False,
                    "damage": w.weapon.damage if w.weapon else None,
                    "heat": w.weapon.heat if w.weapon else None,
                    "disabled": w.disabled,
                    "destroyed": w.destroyed,
                    # Ballistic sub-class from the master weapon's modifications
                    # (e.g. "ULTRA" enables double-tap firing).
                    "weapon_type": (w.weapon.modifications or {}).get("weapon_type")
                        if w.weapon else None,
                } for w in unit.weapons]
                attachments = [{
                    "id": a.id,                    # SessionMechAttachment id (destroy key)
                    "sku": a.attachment_sku,
                    "display_name": a.attachment.display_name if a.attachment else a.attachment_sku,
                    "tech_base": a.attachment.tech_base if a.attachment else None,
                    "tonnage": a.attachment.tonnage if a.attachment else None,
                    "destroyed": a.destroyed,
                } for a in unit.attachments]
                units.append({
                    "id": unit.id,           # session_mech row id (used for removal)
                    "mech_id": unit.mech_id,
                    "team": unit.team,
                    "pilot_name": unit.pilot_name,
                    "pilot_gunnery_skill": unit.pilot_gunnery_skill,
                    "name": m.name if m else "Unknown Chassis",
                    "model": m.model if m else None,
                    "tonnage": m.tonnage if m else None,
                    "tech_base": m.tech_base.name.lower() if m and hasattr(m.tech_base, "name") else None,
                    "weapons": weapons,
                    "attachments": attachments,
                    "fired_this_turn": unit.id in fired_events,
                    "fire_event_id": fired_events.get(unit.id),
                    "accent_color": unit.accent_color,
                })
            data.append({
                "id": s.id,
                "name": s.name,
                "status": s.status,
                "current_turn": s.current_turn,
                "created_on": s.created_on,
                "mechs": units,
                "events": [{
                    "id": e.id,
                    "turn": e.turn,
                    "event_type": e.event_type,
                    "session_mech_id": e.session_mech_id,
                    "attacker": e.attacker,
                    "target": e.target,
                    "payload": e.payload,
                } for e in s.events],
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
            weapon.short_range_modifier = payload.short_range_modifier
            weapon.medium_range_modifier = payload.medium_range_modifier
            weapon.long_range_modifier = payload.long_range_modifier
            weapon.num_shots = payload.num_shots
            weapon.cluster_damage = payload.cluster_damage

            if payload.type:
                try:
                    weapon.type = WeaponType(payload.type)
                except ValueError:
                    raise HTTPException(status_code=400,
                                        detail=f"Invalid weapon type '{payload.type}'.")
            else:
                weapon.type = None

            weapon.modifications = payload.modifications

            session.flush()  # Forces ID assignment for the create path
            return {"status": "success", "action": status, "weapon_id": weapon.id}


@app.get("/api/weapons")
def get_all_weapons():
    """Returns the full weapons_master catalog for the Weapons Library tab."""
    with SessionLocal() as session:
        weapons = session.execute(select(Weapon).order_by(Weapon.name)).scalars().all()
        return [{
            "id": w.id,
            "tech_base": w.tech_base,
            "name": w.name,
            "full_name": w.full_name,
            "use_ammo": w.use_ammo,
            "damage": w.damage,
            "heat": w.heat,
            "minimum_range": w.minimum_range,
            "short_range": w.short_range,
            "medium_range": w.medium_range,
            "long_range": w.long_range,
            "short_range_modifier": w.short_range_modifier,
            "medium_range_modifier": w.medium_range_modifier,
            "long_range_modifier": w.long_range_modifier,
            "num_shots": w.num_shots,
            "cluster_damage": w.cluster_damage,
            "type": w.type,
            "modifications": w.modifications,
        } for w in weapons]


# ---------------------------------------------------------------------------
# Weapon attachments (Artemis IV, etc.) — keyed by their string SKU.
# ---------------------------------------------------------------------------
@app.get("/api/weapon-attachments")
def get_all_attachments(attachment_type: Optional[str] = None):
    """Returns the weapon_attachments catalog, optionally filtered by
    attachment_type (e.g. "mech" or "weapon")."""
    with SessionLocal() as session:
        stmt = select(Attachments).order_by(Attachments.display_name)
        if attachment_type is not None:
            try:
                type_enum = AttachmentType(attachment_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid attachment_type. Use 'mech' or 'weapon'.",
                )
            stmt = stmt.where(Attachments.attachment_type == type_enum)
        rows = session.execute(stmt).scalars().all()
        return [{
            "sku": a.sku,
            "display_name": a.display_name,
            "to_hit_modifier": a.to_hit_modifier,
            "cluster_modifier": a.cluster_modifier,
            "tonnage": a.tonnage,
            "tech_base": a.tech_base,
            "attachment_type": a.attachment_type.value if a.attachment_type else None,
            "description": a.description,
        } for a in rows]


@app.post("/api/weapon-attachments/save")
def save_or_update_attachment(payload: AttachmentSaveRequest):
    """Create or update an attachment (upsert on its SKU)."""
    with SessionLocal() as session:
        with session.begin():
            attachment = session.get(Attachments, payload.sku)
            action = "updated" if attachment else "created"
            if not attachment:
                attachment = Attachments(sku=payload.sku)
                session.add(attachment)

            attachment.display_name = payload.display_name
            attachment.to_hit_modifier = payload.to_hit_modifier
            attachment.cluster_modifier = payload.cluster_modifier
            attachment.tonnage = payload.tonnage
            attachment.description = payload.description
            return {"status": "success", "action": action, "sku": payload.sku}


# ---------------------------------------------------------------------------
# Ammo types (Inferno, etc.) — keyed by their string SKU.
# ---------------------------------------------------------------------------
@app.get("/api/ammo-types")
def get_all_ammo_types():
    """Returns the full ammo_types catalog."""
    with SessionLocal() as session:
        rows = session.execute(
            select(AmmoType).order_by(AmmoType.display_name)
        ).scalars().all()
        return [{
            "sku": a.sku,
            "display_name": a.display_name,
            "damage": a.damage,
            "heat": a.heat,
            "special_effect": a.special_effect,
            "description": a.description,
        } for a in rows]


@app.post("/api/ammo-types/save")
def save_or_update_ammo_type(payload: AmmoSaveRequest):
    """Create or update an ammo type (upsert on its SKU)."""
    with SessionLocal() as session:
        with session.begin():
            ammo = session.get(AmmoType, payload.sku)
            action = "updated" if ammo else "created"
            if not ammo:
                ammo = AmmoType(sku=payload.sku)
                session.add(ammo)

            ammo.display_name = payload.display_name
            ammo.damage = payload.damage
            ammo.heat = payload.heat
            ammo.special_effect = payload.special_effect
            ammo.description = payload.description
            return {"status": "success", "action": action, "sku": payload.sku}


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
                    selectinload(Mech.weapon_links).selectinload(MechWeapon.weapon),
                    selectinload(Mech.attachments),
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

                # Chassis-level equipment fitted onto this mech.
                attachments_payload = [{
                    "sku": a.sku,
                    "display_name": a.display_name,
                    "to_hit_modifier": a.to_hit_modifier,
                    "cluster_modifier": a.cluster_modifier,
                    "tonnage": a.tonnage,
                    "tech_base": a.tech_base,
                    "attachment_type": a.attachment_type.value if a.attachment_type else None,
                } for a in mech.attachments]

                # Construct the master Mech object
                response_data.append({
                    "id": mech.id,
                    "name": mech.name,
                    "model": mech.model,
                    "tech_base": mech.tech_base.name.lower() if hasattr(mech.tech_base, 'name') else str(
                        mech.tech_base),
                    "tonnage": mech.tonnage,
                    "weapon_links": weapons_payload,
                    "attachments": attachments_payload,
                })

            return response_data

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Database retrieval failure: {str(e)}")


# --- ADMIN: DATABASE BACKUP -------------------------------------------------
# Where the seed dump is written. This path is bind-mounted (see
# docker-compose.yml) to the host ./db_seed directory, which is ALSO mounted
# into the Postgres container's /docker-entrypoint-initdb.d. So a dump written
# here is automatically loaded the next time Postgres starts on a fresh volume
# (e.g. `docker compose up` on another machine), seeding the database.
SEED_DIR = os.getenv("SEED_DIR", "/seed")
SEED_FILE = os.path.join(SEED_DIR, "seed.sql")


def _parse_database_url(url: str) -> dict:
    """Break a SQLAlchemy Postgres URL into pg_dump connection parameters.

    Accepts the ``postgresql+psycopg://user:pass@host:port/dbname`` form used
    by :data:`config.DATABASE_URL` and returns a dict of the pieces plus a
    ``PGPASSWORD`` value for the subprocess environment.
    """
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "user": parsed.username or "postgres",
        "password": parsed.password or "",
        "dbname": (parsed.path or "/postgres").lstrip("/") or "postgres",
    }


@app.post("/api/admin/backup-database")
def backup_database():
    """Dump the entire database to the seed file for portable re-seeding.

    Runs ``pg_dump`` with ``--clean --if-exists`` so the resulting SQL can be
    replayed on a fresh database (it drops then recreates every object). The
    file lands in the shared seed directory that Postgres auto-loads on first
    boot, so committing it to the repo lets another machine come up pre-seeded.
    """
    conn = _parse_database_url(DATABASE_URL)

    os.makedirs(SEED_DIR, exist_ok=True)

    cmd = [
        "pg_dump",
        "--host", conn["host"],
        "--port", conn["port"],
        "--username", conn["user"],
        "--dbname", conn["dbname"],
        "--clean",          # emit DROP statements
        "--if-exists",      # ...guarded so a fresh DB doesn't error on the DROPs
        "--no-owner",       # portable across differing role names
        "--no-privileges",
        "--file", SEED_FILE,
    ]
    env = {**os.environ, "PGPASSWORD": conn["password"]}

    try:
        result = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=120,
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="pg_dump not found on the server. Ensure postgresql-client is installed.",
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Database backup timed out.")

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"pg_dump failed: {result.stderr.strip() or 'unknown error'}",
        )

    size_bytes = os.path.getsize(SEED_FILE) if os.path.exists(SEED_FILE) else 0
    return {
        "status": "success",
        "file": SEED_FILE,
        "size_bytes": size_bytes,
    }


# --- LAUNCHER ---
if __name__ == "__main__":
    import os
    # reload=True spawns a child process (the StatReload "reloader"), which the
    # debugger can't attach to and which breaks under pydevd — so it's OFF by
    # default and breakpoints work. Set UVICORN_RELOAD=1 for hot-reload dev.
    reload = os.getenv("UVICORN_RELOAD", "0") == "1"
    # Start the server on localhost port 8000
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=reload)
