"""The company logo (Administration > System settings): uploaded as a data URL, kept as a PNG fitting in 600 x 240,
printed on the invoices and credit notes."""

import base64
import io

import pytest
from PIL import Image

from powererp.core.errors import AppError
from powererp.modules.sales.company import LOGO_BOX, PNG_PREFIX, normalize_logo


def data_url(fmt="PNG", size=(1200, 300), mode="RGB", color=(31, 95, 168), mime=None):
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, fmt)
    return f"data:{mime or 'image/' + fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


def png_size(url):
    with Image.open(io.BytesIO(base64.b64decode(url[len(PNG_PREFIX) :]))) as im:
        return im.format, im.size, im.mode


def test_a_big_image_is_made_smaller_keeping_its_proportions():
    url = normalize_logo(data_url(size=(1200, 300)))
    assert url.startswith(PNG_PREFIX) and png_size(url) == ("PNG", (600, 150), "RGB")
    # a tall one fits in the height; a small one is not made bigger
    assert png_size(normalize_logo(data_url(size=(300, 900))))[1] == (80, LOGO_BOX[1])
    assert png_size(normalize_logo(data_url(size=(120, 40))))[1] == (120, 40)


def test_jpeg_becomes_png_and_transparency_is_kept():
    assert png_size(normalize_logo(data_url("JPEG", mime="image/jpeg")))[0] == "PNG"
    assert png_size(normalize_logo(data_url(mode="RGBA", color=(0, 0, 0, 0))))[2] == "RGBA"
    assert png_size(normalize_logo(data_url("GIF", mode="P", color=1)))[0] == "PNG"


@pytest.mark.parametrize(
    "bad",
    ["", "hello", "data:image/png;base64,@@@", "data:image/png;base64," + base64.b64encode(b"not an image").decode()],
)
def test_what_is_not_an_image_is_refused(bad):
    with pytest.raises(AppError) as e:
        normalize_logo(bad)
    assert (e.value.code, e.value.field) == ("logo_invalid", "cLogo")


def test_a_file_too_big_is_refused():
    huge = "data:image/png;base64," + "A" * (8 * 1024 * 1024)
    with pytest.raises(AppError) as e:
        normalize_logo(huge)
    assert e.value.code == "logo_too_big"


def test_upload_show_and_remove(app, admin):
    assert admin.get("/api/company").get_json()["lHasLogo"] is False
    assert admin.get("/api/company/logo").status_code == 404
    r = admin.put("/api/admin/company/logo", json={"cLogo": data_url()})
    assert r.status_code == 200
    me = r.get_json()
    assert (
        me["lHasLogo"] is True and "cLogo" not in me and me["cName"]
    )  # the profile is kept, the logo is not sent back
    img = admin.get("/api/company/logo")
    assert img.status_code == 200 and img.mimetype == "image/png" and img.data.startswith(b"\x89PNG")
    # saving the profile keeps the logo, even when the payload tries to change it
    assert admin.put("/api/admin/company", json={"cName": "Usine", "cLogo": "x"}).get_json()["lHasLogo"] is True
    bad = admin.put("/api/admin/company/logo", json={"cLogo": "data:text/plain;base64,aGVsbG8="})
    assert bad.status_code == 400 and bad.get_json()["error"] == "logo_invalid"
    assert admin.get("/api/company/logo").status_code == 200  # a refused upload keeps the logo
    assert admin.delete("/api/admin/company/logo").get_json()["lHasLogo"] is False
    assert admin.get("/api/company/logo").status_code == 404

    admin.put("/api/admin/company/logo", json={"cLogo": data_url()})
    admin.post("/api/users", json={"username": "lea", "name": "Léa", "password": "secret1", "role": "user"})
    c = app.test_client()
    assert c.post("/api/auth/login", json={"username": "lea", "password": "secret1"}).status_code == 200
    assert c.get("/api/company/logo").status_code == 200  # every user prints it
    assert c.put("/api/admin/company/logo", json={"cLogo": data_url()}).status_code == 403
    assert c.delete("/api/admin/company/logo").status_code == 403


def test_logo_after_clear(admin):
    admin.post("/api/clear")
    assert admin.put("/api/admin/company/logo", json={"cLogo": data_url()}).get_json()["lHasLogo"] is True
    assert admin.get("/api/company").get_json()["cName"] == ""  # set before the rest of the profile


def test_the_invoice_prints_the_logo(admin):
    no = admin.post(
        "/api/sales-invoices",
        json={"cCustomer": "HOTEL-LAURIER", "dDate": "2026-11-23", "lines": [{"cProduct": "TUBE-T8", "dQty": "1"}]},
    ).get_json()["iNo"]
    html = admin.get(f"/api/sales-invoices/{no}/print").get_data(as_text=True)
    assert 'class="logo"' not in html
    admin.put("/api/admin/company/logo", json={"cLogo": data_url()})
    html = admin.get(f"/api/sales-invoices/{no}/print").get_data(as_text=True)
    assert f'<img class="logo" src="{PNG_PREFIX}' in html
