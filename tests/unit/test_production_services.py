"""Unit tests of the production services (M0: reference lists), on memory repositories."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.production.service import (
    CapabilityService,
    DowntimeReasonService,
    ScrapReasonService,
    SetupFamilyService,
)
from tests.unit.helpers import memory


@pytest.mark.parametrize("cls", [CapabilityService, SetupFamilyService, DowntimeReasonService, ScrapReasonService])
def test_reference_list_rules(cls):
    refs = ReferenceRegistry()
    svc = cls(memory([]), refs)
    row = svc.create({"cCode": "ab-1", "cDescFR": "Un"})
    assert row["cCode"] == "AB-1" and row["lActive"] is True
    with pytest.raises(AppError) as e:
        svc.create({"cCode": "x"})
    assert e.value.field == "cDescFR"
    refs.register(svc.kind, lambda code: code == "AB-1")  # e.g. used by a product or a resource
    with pytest.raises(AppError) as e:
        svc.delete(["ab-1"])
    assert e.value.status == 409
    svc.update(["AB-1"], {"lActive": False})
    assert svc.active() == []


def test_downtime_reason_defaults_and_planned_stops():
    svc = DowntimeReasonService(memory([]), ReferenceRegistry())
    row = svc.create({"cCode": "JAM", "cDescFR": "Bourrage"})
    assert (row["cGroup"], row["lAffectsOEE"]) == ("breakdown", True)
    assert svc.update(["JAM"], {"cGroup": "planned", "lAffectsOEE": True})["lAffectsOEE"] is False


def test_scrap_reason_group_is_checked():
    svc = ScrapReasonService(memory([]), ReferenceRegistry())
    assert svc.create({"cCode": "S", "cDescFR": "s"})["cGroup"] == "process"
    with pytest.raises(AppError) as e:
        svc.create({"cCode": "T", "cDescFR": "t", "cGroup": "weather"})
    assert (e.value.code, e.value.field) == ("invalid_choice", "cGroup")
