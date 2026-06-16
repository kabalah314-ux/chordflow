"""
Tests de validación de los schemas Pydantic del núcleo de banda (T-049, giro V2).

Verifican que role/status solo aceptan los valores conocidos (defensa de usuario, 422 en la API)
y que los Literal de los schemas siguen alineados con las fuentes únicas de `models`.
"""

import pytest
from pydantic import ValidationError

from src.services import models, schemas

pytestmark = pytest.mark.unit


def test_band_create_exige_nombre():
    schemas.BandCreate(name="Los Pericos")  # OK
    with pytest.raises(ValidationError):
        schemas.BandCreate(name="")  # min_length=1


@pytest.mark.parametrize("role", ["admin", "member", "guest"])
def test_invite_acepta_roles_validos(role):
    inv = schemas.BandInviteCreate(role_to_grant=role)
    assert inv.role_to_grant == role


def test_invite_rechaza_rol_invalido():
    with pytest.raises(ValidationError):
        schemas.BandInviteCreate(role_to_grant="owner")  # no existe


def test_invite_default_es_member_y_max_uses_positivo():
    assert schemas.BandInviteCreate().role_to_grant == "member"
    with pytest.raises(ValidationError):
        schemas.BandInviteCreate(max_uses=0)  # ge=1


def test_membership_role_update_rechaza_estado_como_rol():
    schemas.MembershipRoleUpdate(role="admin")  # OK
    with pytest.raises(ValidationError):
        schemas.MembershipRoleUpdate(role="left")  # 'left' es status, no role


def test_literales_alineados_con_fuentes_unicas_de_models():
    """Los Literal de los schemas deben cubrir exactamente las fuentes únicas de models,
    para que validación de schema y CHECK de BD nunca diverjan."""
    import typing

    roles_schema = set(typing.get_args(schemas.MembershipRoleUpdate.model_fields["role"].annotation))
    assert roles_schema == set(models.BAND_ROLES)

    status_schema = set(
        typing.get_args(schemas.BandMembershipResponse.model_fields["status"].annotation)
    )
    assert status_schema == set(models.MEMBERSHIP_STATUSES)
