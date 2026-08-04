"""Tests for weapon-related tables: WeaponAttachment, AmmoType, and their
many-to-many links to Weapon.

Uses an in-memory SQLite database so tests are fast and fully isolated —
no shared state between tests, no external DB required.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, Weapon, WeaponAttachment, AmmoType

@pytest.fixture()
def engine():
    """Fresh in-memory SQLite engine per test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def session(engine):
    """Fresh session per test, rolled back/closed automatically."""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture()
def artemis_iv(session) -> WeaponAttachment:
    attachment = WeaponAttachment(
        sku="ARTEMISIV",
        display_name="Artemis IV FCS",
        to_hit_modifier=-1,
        tonnage=1.0,
        attachment_type="WEAPON",
        description="Improves missile accuracy.",
    )
    session.add(attachment)
    session.commit()
    return attachment


@pytest.fixture()
def targeting_computer(session) -> WeaponAttachment:
    attachment = WeaponAttachment(
        sku="TARGETINGCOMPUTER",
        display_name="Targeting Computer",
        to_hit_modifier=None,
        tonnage=3.0,
        attachment_type="MECH",
        description="Improves direct-fire weapon accuracy.",
    )
    session.add(attachment)
    session.commit()
    return attachment


@pytest.fixture()
def standard_ammo(session) -> AmmoType:
    ammo = AmmoType(
        sku="STANDARD",
        display_name="Standard Ammo",
        damage=None,  # inherits weapon's base damage
        heat=None,
        special_effect=None,
    )
    session.add(ammo)
    session.commit()
    return ammo


@pytest.fixture()
def inferno_ammo(session) -> AmmoType:
    ammo = AmmoType(
        sku="INFERNO",
        display_name="Inferno",
        damage=2,
        heat=4,
        special_effect="fire",
    )
    session.add(ammo)
    session.commit()
    return ammo


@pytest.fixture()
def lrm20(session) -> Weapon:
    weapon = Weapon(
        name="ISLRM20",
        full_name="LRM-20",
        use_ammo=True,
        damage=20,
        heat=6,
        minimum_range=6,
        short_range=7,
        medium_range=14,
        long_range=21,
    )
    session.add(weapon)
    session.commit()
    return weapon


class TestWeaponAttachment:
    """Tests for the weapon_attachments lookup table."""

    def test_create_attachment(self, session, artemis_iv):
        fetched = session.get(WeaponAttachment, "ARTEMISIV")
        assert fetched is not None
        assert fetched.display_name == "Artemis IV FCS"
        assert fetched.to_hit_modifier == -1
        assert fetched.tonnage == 1.0

    def test_sku_is_primary_key(self, session, artemis_iv):
        # Attempting to insert a second row with the same SKU should fail.
        duplicate = WeaponAttachment(
            sku="ARTEMISIV",
            display_name="Duplicate Artemis IV",
            attachment_type="WEAPON",
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_optional_fields_can_be_null(self, session):
        attachment = WeaponAttachment(sku="TAG", attachment_type="WEAPON", display_name="TAG")
        session.add(attachment)
        session.commit()

        fetched = session.get(WeaponAttachment, "TAG")
        assert fetched.to_hit_modifier is None
        assert fetched.tonnage is None
        assert fetched.description is None


class TestAmmoType:
    """Tests for the ammo_types lookup table."""

    def test_create_ammo_type(self, session, inferno_ammo):
        fetched = session.get(AmmoType, "INFERNO")
        assert fetched is not None
        assert fetched.damage == 2
        assert fetched.heat == 4
        assert fetched.special_effect == "fire"

    def test_sku_is_primary_key(self, session, inferno_ammo):
        duplicate = AmmoType(sku="INFERNO", display_name="Duplicate Inferno")
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

    def test_standard_ammo_has_no_special_effect(self, session, standard_ammo):
        fetched = session.get(AmmoType, "STANDARD")
        assert fetched.special_effect is None


class TestWeaponAttachmentRelationship:
    """Tests for the many-to-many link between Weapon and WeaponAttachment."""

    def test_weapon_starts_with_no_attachments(self, session, lrm20):
        assert lrm20.attachments == []

    def test_attach_single_attachment(self, session, lrm20, artemis_iv):
        lrm20.attachments.append(artemis_iv)
        session.commit()

        fetched = session.get(Weapon, lrm20.id)
        skus = [a.sku for a in fetched.attachments]
        assert skus == ["ARTEMISIV"]

    def test_attach_multiple_attachments(
        self, session, lrm20, artemis_iv, targeting_computer
    ):
        lrm20.attachments.extend([artemis_iv, targeting_computer])
        session.commit()

        fetched = session.get(Weapon, lrm20.id)
        skus = {a.sku for a in fetched.attachments}
        assert skus == {"ARTEMISIV", "TARGETINGCOMPUTER"}

    def test_same_attachment_reusable_across_weapons(self, session, artemis_iv):
        weapon_a = Weapon(
            name="ISLRM15", damage=15, heat=5,
            short_range=7, medium_range=14, long_range=21,
        )
        weapon_b = Weapon(
            name="ISLRM10", damage=10, heat=4,
            short_range=7, medium_range=14, long_range=21,
        )
        session.add_all([weapon_a, weapon_b])
        session.commit()

        weapon_a.attachments.append(artemis_iv)
        weapon_b.attachments.append(artemis_iv)
        session.commit()

        assert weapon_a.attachments[0].sku == "ARTEMISIV"
        assert weapon_b.attachments[0].sku == "ARTEMISIV"

    def test_deleting_weapon_cascades_link_rows(self, session, lrm20, artemis_iv):
        lrm20.attachments.append(artemis_iv)
        session.commit()

        session.delete(lrm20)
        session.commit()

        # The attachment itself should survive; only the link row is removed.
        fetched_attachment = session.get(WeaponAttachment, "ARTEMISIV")
        assert fetched_attachment is not None


class TestWeaponAmmoRelationship:
    """Tests for the many-to-many link between Weapon and AmmoType."""

    def test_weapon_starts_with_no_compatible_ammo(self, session, lrm20):
        assert lrm20.compatible_ammo == []

    def test_add_compatible_ammo(self, session, lrm20, standard_ammo, inferno_ammo):
        lrm20.compatible_ammo.extend([standard_ammo, inferno_ammo])
        session.commit()

        fetched = session.get(Weapon, lrm20.id)
        skus = {a.sku for a in fetched.compatible_ammo}
        assert skus == {"STANDARD", "INFERNO"}

    def test_ammo_reusable_across_weapons(self, session, standard_ammo):
        weapon_a = Weapon(
            name="ISSRM6", damage=12, heat=4,
            short_range=3, medium_range=6, long_range=9,
        )
        weapon_b = Weapon(
            name="ISSRM4", damage=8, heat=3,
            short_range=3, medium_range=6, long_range=9,
        )
        session.add_all([weapon_a, weapon_b])
        session.commit()

        weapon_a.compatible_ammo.append(standard_ammo)
        weapon_b.compatible_ammo.append(standard_ammo)
        session.commit()

        assert weapon_a.compatible_ammo[0].sku == "STANDARD"
        assert weapon_b.compatible_ammo[0].sku == "STANDARD"

    def test_removing_ammo_from_weapon_does_not_delete_ammo_type(
        self, session, lrm20, inferno_ammo
    ):
        lrm20.compatible_ammo.append(inferno_ammo)
        session.commit()

        lrm20.compatible_ammo.remove(inferno_ammo)
        session.commit()

        assert lrm20.compatible_ammo == []
        # The ammo type itself should still exist independently.
        fetched_ammo = session.get(AmmoType, "INFERNO")
        assert fetched_ammo is not None


class TestWeaponWithAttachmentsAndAmmoTogether:
    """Integration-style tests combining both relationships on one weapon."""

    def test_weapon_with_attachment_and_multiple_ammo_types(
        self, session, lrm20, artemis_iv, standard_ammo, inferno_ammo
    ):
        lrm20.attachments.append(artemis_iv)
        lrm20.compatible_ammo.extend([standard_ammo, inferno_ammo])
        session.commit()

        fetched = session.get(Weapon, lrm20.id)
        assert [a.sku for a in fetched.attachments] == ["ARTEMISIV"]
        assert {a.sku for a in fetched.compatible_ammo} == {"STANDARD", "INFERNO"}

    def test_has_attachment_helper_pattern(self, session, lrm20, artemis_iv):
        # Mirrors the "any(a.sku == ...)" check pattern used in resolver code.
        lrm20.attachments.append(artemis_iv)
        session.commit()

        has_artemis = any(a.sku == "ARTEMISIV" for a in lrm20.attachments)
        has_tag = any(a.sku == "TAG" for a in lrm20.attachments)

        assert has_artemis is True
        assert has_tag is False