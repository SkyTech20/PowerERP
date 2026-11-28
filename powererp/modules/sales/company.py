"""Company profile (V1): the name, address and numbers printed at the top of the invoices.

One row (code MAIN). The GST / HST and QST registration numbers are not typed twice: they are the registration
numbers of the active tax codes (Administration > Taxes), returned with the profile.

The logo (Administration > System settings) is printed at the top of the invoices, the credit notes and the
traceability spreadsheet. It is uploaded on its own (PUT /api/admin/company/logo, a data URL) and kept as a PNG
data URL, made to fit in LOGO_BOX: a big photo or a scan is made smaller, the proportions are kept.
"""

from __future__ import annotations

import base64
import binascii
import io
from collections.abc import Callable

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.modules.common.forms import RecordForm, Row
from powererp.store import Store

from .customers import check_email

CODE = "MAIN"
LOGO_MAX_BYTES = 5 * 1024 * 1024  # the file uploaded
LOGO_MAX_PIXELS = 40_000_000  # refused above (a decompression bomb, not a logo)
LOGO_BOX = (600, 240)  # what is kept: wide logos are the usual ones on an invoice header
LOGO_FORMATS = ("PNG", "JPEG", "GIF", "WEBP")
PNG_PREFIX = "data:image/png;base64,"


def normalize_logo(data_url: str) -> str:
    """The logo uploaded (a data URL of a PNG, JPEG, GIF or WebP image) as a PNG data URL fitting in LOGO_BOX."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    head, sep, body = (data_url or "").partition(",")
    if not sep or not head.startswith("data:") or not head.endswith(";base64"):
        raise AppError("logo_invalid", "cLogo")
    if len(body) > LOGO_MAX_BYTES * 4 // 3 + 4:
        raise AppError("logo_too_big", "cLogo")
    try:
        raw = base64.b64decode(body, validate=True)
    except (binascii.Error, ValueError):
        raise AppError("logo_invalid", "cLogo") from None
    if len(raw) > LOGO_MAX_BYTES:
        raise AppError("logo_too_big", "cLogo")
    try:
        with Image.open(io.BytesIO(raw)) as im:
            if im.format not in LOGO_FORMATS:
                raise AppError("logo_invalid", "cLogo")
            if im.width * im.height > LOGO_MAX_PIXELS:
                raise AppError("logo_too_big", "cLogo")
            im.seek(0)  # the first frame of an animated GIF
            img = ImageOps.exif_transpose(im)  # a phone photo keeps its orientation
            has_alpha = img.mode in ("RGBA", "LA", "PA") or (img.mode == "P" and "transparency" in img.info)
            img = img.convert("RGBA" if has_alpha else "RGB")
            img.thumbnail(LOGO_BOX, Image.Resampling.LANCZOS)  # only made smaller, never bigger
            out = io.BytesIO()
            img.save(out, "PNG", optimize=True)
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError):
        raise AppError("logo_invalid", "cLogo") from None
    return PNG_PREFIX + base64.b64encode(out.getvalue()).decode("ascii")


class CompanyProfileService:
    def __init__(self, repo: Store, tax_codes: Callable[[], list[Row]]):
        self.repo = repo
        self.tax_codes = tax_codes
        self.form = RecordForm(S.COMPANY_PROFILE, S.DEFAULTS["company_profile"])

    def get(self) -> Row:
        """The profile (the defaults while it was never saved)."""
        return self.repo.get(CODE) or self.form.blank()

    def save(self, payload: Row) -> Row:
        current = self.repo.get(CODE)
        row = self.form.apply(dict(current) if current else self.form.blank(), payload, skip=("cCode", "cLogo"))
        row["cCode"] = CODE
        require(row, "cName")
        row["cEmail"] = check_email(row["cEmail"], "cEmail")
        row["cProvince"] = row["cProvince"].strip().upper()
        row["cCountry"] = row["cCountry"].strip().upper()
        self._write(row, current is not None)
        return row

    def _write(self, row: Row, exists: bool) -> None:
        if exists:
            self.repo.update(row, [CODE])
        else:
            self.repo.insert(row)

    # ---------------------------------------------------------------- logo
    def set_logo(self, data_url: str) -> None:
        current = self.repo.get(CODE)
        row = dict(current) if current else self.form.blank()
        row["cCode"] = CODE
        row["cLogo"] = normalize_logo(data_url)
        self._write(row, current is not None)

    def remove_logo(self) -> None:
        current = self.repo.get(CODE)
        if current and current.get("cLogo"):
            self._write({**current, "cLogo": ""}, True)

    def logo_url(self) -> str:
        """The logo as a data URL ("" without a logo): what the printouts put in their <img>."""
        return self.get().get("cLogo") or ""

    def logo_png(self) -> bytes | None:
        url = self.logo_url()
        return base64.b64decode(url[len(PNG_PREFIX) :]) if url.startswith(PNG_PREFIX) else None

    def tax_numbers(self) -> list[Row]:
        """The registration numbers to print: one per number (GST and HST share theirs), from the active codes."""
        out: list[Row] = []
        seen: set[str] = set()
        for t in sorted(self.tax_codes(), key=lambda t: t["cCode"]):
            number = t.get("cRegistrationNo", "").strip()
            if not t.get("lActive") or not number or number.upper() in seen:
                continue
            seen.add(number.upper())
            out.append({"cTaxCode": t["cCode"], "cKind": t.get("cKind", ""), "cRegistrationNo": number})
        return out

    def view(self) -> Row:
        """The profile without the logo itself (GET /api/company/logo serves it), with lHasLogo."""
        row = {k: v for k, v in self.get().items() if k != "cLogo"}
        return {**row, "lHasLogo": bool(self.logo_url()), "taxNumbers": self.tax_numbers()}
