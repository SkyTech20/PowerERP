"""Production services. M0: the reference lists used by the shop floor and, later, the scheduler.

- capabilities: what a resource can do (CUT, BAKE, WIND...); an operation asks for a capability, any resource
  having it can run the operation (alternative resources for the scheduler).
- setup families: products that change over alike; the setup matrix (M1) gives the minutes from one family to
  another, which makes the setup time depend on the sequence (M6, OR scheduling).
- downtime reasons: why a machine stopped, grouped by TPM loss; lAffectsOEE = False for planned stops (breaks,
  planned maintenance), which are left out of the OEE availability.
- scrap reasons: why a quantity was rejected, grouped by cause.
"""

from __future__ import annotations

from powererp import schemas as S
from powererp.core.http import require
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store


class ReferenceListService(CrudService):
    """A code list with a French (required) and an English description. `kind` is its name in the references
    registry: a record still used elsewhere (e.g. a setup family on a product) cannot be deleted."""

    kind = ""

    def __init__(self, repo: Store, schema: dict, defaults: Row, references: ReferenceRegistry):
        super().__init__(repo, schema, defaults)
        self.references = references

    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        row["cCode"] = row["cCode"].upper()

    def before_delete(self, row: Row) -> None:
        self.references.check(self.kind, row["cCode"])

    def active(self) -> list[Row]:
        return [r for r in self.repo.all(lines=False) if r.get("lActive")]


class CapabilityService(ReferenceListService):
    kind = "capability"

    def __init__(self, repo: Store, references: ReferenceRegistry):
        super().__init__(repo, S.CAPABILITY, S.DEFAULTS["capabilities"], references)


class SetupFamilyService(ReferenceListService):
    kind = "setup_family"

    def __init__(self, repo: Store, references: ReferenceRegistry):
        super().__init__(repo, S.SETUP_FAMILY, S.DEFAULTS["setup_families"], references)


class DowntimeReasonService(ReferenceListService):
    kind = "downtime_reason"

    def __init__(self, repo: Store, references: ReferenceRegistry):
        super().__init__(repo, S.DOWNTIME_REASON, S.DEFAULTS["downtime_reasons"], references)

    def validate(self, row: Row, is_new: bool) -> None:
        super().validate(row, is_new)
        if row["cGroup"] == "planned":
            row["lAffectsOEE"] = False  # a planned stop is not lost time


class ScrapReasonService(ReferenceListService):
    kind = "scrap_reason"

    def __init__(self, repo: Store, references: ReferenceRegistry):
        super().__init__(repo, S.SCRAP_REASON, S.DEFAULTS["scrap_reasons"], references)
