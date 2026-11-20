"""Setup matrix (P6): how long it takes to change over from one setup family to another.

This is what makes the setup time depend on the sequence of the orders, and what the OR scheduler (M6)
optimizes. Families (P1) avoid a product x product matrix: products of the same family change over alike.

A matrix belongs to a work center (all its resources) or to one resource (overrides its work center's).
Each line: from family -> to family ("*" = any), minutes, cost and scrap of the changeover.

Lookup of a changeover on a resource, first match wins:
1. the resource's matrix, then its work center's matrix; in each one:
   exact pair -> (from, *) -> (*, to) -> (*, *);
2. no line found: same family -> no changeover (0); else the setup of the operation (the default given).
"""

from __future__ import annotations

from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.values import number, text
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store

ANY = "*"


class SetupMatrixService(CrudService):
    keys = ("cScope", "cScopeCode")
    line_schema = S.SETUP_MATRIX_LINE

    def __init__(self, repo: Store, refs: dict[str, Any], references: ReferenceRegistry):
        """refs: finders given by the container: work_centers, resources, setup_families, and families()
        listing the active setup families."""
        super().__init__(repo, S.SETUP_MATRIX, S.DEFAULTS["setup_matrices"])
        self.refs = refs
        references.register("setup_family", self._uses_family)
        references.register("work_center", lambda code: self._has_matrix("work_center", code))
        references.register("resource", lambda code: self._has_matrix("resource", code))

    def _uses_family(self, code: str) -> bool:
        c = code.upper()
        return any(
            c in (ln["cFromFamily"].upper(), ln["cToFamily"].upper()) for m in self.repo.all() for ln in m["lines"]
        )

    def _has_matrix(self, scope: str, code: str) -> bool:
        return self.find(scope, code) is not None

    def keep_line(self, line: Row) -> bool:
        return bool(text(line["cFromFamily"]) or text(line["cToFamily"]))

    def validate(self, row: Row, is_new: bool) -> None:
        finder = self.refs["work_centers" if row["cScope"] == "work_center" else "resources"]
        target = finder(row["cScopeCode"]) if text(row["cScopeCode"]) else None
        if target is None:
            raise AppError("unknown_ref" if text(row["cScopeCode"]) else "required", "cScopeCode")
        row["cScopeCode"] = target["cCode"]
        seen = set()
        for i, ln in enumerate(row.get("lines", []), 1):
            where = f"line {i}"
            for field in ("cFromFamily", "cToFamily"):
                v = text(ln[field]).upper() or ANY
                if v != ANY:
                    fam = self.refs["setup_families"](v)
                    if fam is None:
                        raise AppError("unknown_ref", "lines", detail=f"{where}: {v}")
                    v = fam["cCode"]
                ln[field] = v
            pair = (ln["cFromFamily"], ln["cToFamily"])
            if pair in seen:
                raise AppError("duplicate", "lines", detail=f"{where}: {pair[0]} → {pair[1]}")
            seen.add(pair)
            for field in ("dSetupMin", "dSetupCost", "dScrapQty"):
                if text(ln[field]) and number(ln[field]) < 0:
                    raise AppError("negative", "lines", detail=f"{where}: {field}")
            if not text(ln["dSetupMin"]):
                ln["dSetupMin"] = "0"
        # the exact pairs first, then the ones with "*" (the order the lookup reads them)
        row["lines"] = sorted(
            row.get("lines", []),
            key=lambda x: (x["cFromFamily"] == ANY, x["cToFamily"] == ANY, x["cFromFamily"], x["cToFamily"]),
        )

    def view(self, row: Row, full: bool = True) -> Row:
        return row if full else {**row, "iPairs": len(row.get("lines", []))}

    # ---------------------------------------------------------- lookup
    @staticmethod
    def _match(matrix: Row | None, src: str, dst: str) -> Row | None:
        if not matrix or not matrix.get("lActive", True):
            return None
        lines = {(ln["cFromFamily"].upper(), ln["cToFamily"].upper()): ln for ln in matrix.get("lines", [])}
        for pair in ((src, dst), (src, ANY), (ANY, dst), (ANY, ANY)):
            if pair in lines:
                return {**lines[pair], "cMatchFrom": pair[0], "cMatchTo": pair[1]}
        return None

    def changeover(self, src: str, dst: str, resource: str = "", work_center: str = "", default_min: float = 0) -> Row:
        """Minutes, cost and scrap to go from family `src` to `dst` on a resource (or a work center)."""
        src, dst = text(src).upper(), text(dst).upper()
        scopes: list[tuple[str, str]] = []
        if text(resource):
            res = self.refs["resources"](resource)
            if res is None:
                raise AppError("unknown_ref", "resource")
            scopes.append(("resource", res["cCode"]))
            work_center = work_center or res["cWorkCenter"]
        if text(work_center):
            wc = self.refs["work_centers"](work_center)
            if wc is None:
                raise AppError("unknown_ref", "workCenter")
            scopes.append(("work_center", wc["cCode"]))
        for scope, code in scopes:
            hit = self._match(self.find(scope, code), src, dst)
            if hit is not None:
                return {
                    "dSetupMin": number(hit["dSetupMin"]),
                    "dSetupCost": number(hit["dSetupCost"]),
                    "dScrapQty": number(hit["dScrapQty"]),
                    "cRule": "matrix",
                    "cScope": scope,
                    "cScopeCode": code,
                    "cFromFamily": hit["cMatchFrom"],
                    "cToFamily": hit["cMatchTo"],
                }
        same = src and src == dst
        return {
            "dSetupMin": 0.0 if same else float(default_min),
            "dSetupCost": 0.0,
            "dScrapQty": 0.0,
            "cRule": "same_family" if same else "operation",
            "cScope": "",
            "cScopeCode": "",
            "cFromFamily": src,
            "cToFamily": dst,
        }

    def grid(self, scope: str, code: str, default_min: float = 0) -> Row:
        """Every family x family changeover of a work center / resource (the screen's grid)."""
        families = [f["cCode"] for f in self.refs["families"]()]
        kwargs = {"resource": code} if scope == "resource" else {"work_center": code}
        cells = [[self.changeover(a, b, default_min=default_min, **kwargs) for b in families] for a in families]
        return {"families": families, "cells": cells}
