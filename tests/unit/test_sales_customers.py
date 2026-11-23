"""Unit tests of the customers (V1): ship-to addresses, the tax group of a delivery, who receives the invoices."""

import pytest

from powererp.core.errors import AppError
from powererp.modules.common.registry import ReferenceRegistry
from powererp.modules.sales.company import CompanyProfileService
from powererp.modules.sales.customers import CustomerService, check_email
from tests.unit.helpers import memory


@pytest.fixture
def svc():
    refs = {
        "tax_groups": memory([{"cCode": "QC"}, {"cCode": "ON"}, {"cCode": "EXO"}]).get,
        "warehouses": memory([{"cCode": "ENT-01"}]).get,
    }
    return CustomerService(memory([]), refs, ReferenceRegistry())


def test_tax_group_follows_the_place_of_delivery(svc):
    c = svc.create(
        {
            "cCode": "c1",
            "cName": "C1",
            "cTaxGroup": "qc",
            "cWarehouse": "ent-01",
            "addresses": [
                {"cCode": "mtl", "cAddress1": "1 rue A"},
                {"cCode": "ott", "cAddress1": "2 B St", "cTaxGroup": "on", "lDefault": True},
            ],
        }
    )
    assert c["cWarehouse"] == "ENT-01"
    assert svc.ship_to(c)["cCode"] == "OTT"  # the default one
    assert svc.tax_group_for(c) == "ON"
    assert svc.tax_group_for(c, "mtl") == "QC"  # no tax group on the address: the customer's
    assert svc.ship_to(c, "nope") is None and svc.tax_group_for(c, "nope") == "QC"
    assert svc.tax_group_for(svc.create({"cCode": "c2", "cName": "C2", "cTaxGroup": "exo"})) == "EXO"


def test_invoice_emails(svc):
    c = svc.create({"cCode": "c1", "cName": "C1", "cEmail": " ap@c1.example ", "cTaxGroup": "QC"})
    assert c["cEmail"] == "ap@c1.example" and svc.invoice_emails(c) == ["ap@c1.example"]
    c = svc.update(
        ["C1"],
        {
            "contacts": [
                {"cName": "A", "cEmail": "a@c1.example", "lInvoices": True},
                {"cName": "B", "cEmail": "b@c1.example"},
            ]
        },
    )
    assert svc.invoice_emails(c) == ["a@c1.example"]


def test_terms_lookup(svc):
    svc.create({"cCode": "a", "cName": "A", "cTaxGroup": "QC", "cTermCode": "n30", "cTermDesc": "net 30"})
    svc.create({"cCode": "b", "cName": "B", "cTaxGroup": "QC", "cTermCode": "n30", "cTermDesc": "other"})
    assert svc.terms_lookup() == ([{"code": "n30", "label": "net 30"}], 200)


def test_check_email():
    assert check_email("", "f") == ""
    with pytest.raises(AppError) as e:
        check_email("a@b", "f")
    assert (e.value.code, e.value.field) == ("invalid_email", "f")


def test_company_tax_numbers_once_per_number():
    codes = [
        {"cCode": "TVQ", "cKind": "pst", "cRegistrationNo": "1234567890 TQ0001", "lActive": True},
        {"cCode": "TPS", "cKind": "gst", "cRegistrationNo": "123456789 RT0001", "lActive": True},
        {"cCode": "TVH-ON", "cKind": "hst", "cRegistrationNo": "123456789 rt0001", "lActive": True},
        {"cCode": "OLD", "cKind": "pst", "cRegistrationNo": "999", "lActive": False},
        {"cCode": "ECO", "cKind": "other", "cRegistrationNo": "", "lActive": True},
    ]
    company = CompanyProfileService(memory([]), lambda: codes)
    assert [t["cTaxCode"] for t in company.tax_numbers()] == ["TPS", "TVQ"]
    assert company.get()["cCode"] == "MAIN"
