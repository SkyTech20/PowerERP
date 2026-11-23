"""Price lists and discounts (V2): what a customer pays for a product.

A price list gives prices by product, unit and quantity (quantity breaks: the line with the highest minimum
quantity reached wins), and discounts by product category (a category's discount also covers its
subcategories). Each customer points to one price list (shared by several customers, or its own).

The price of a line (PriceResolver.price), in the unit asked for (the sales unit of the product by default):
1. price: the customer's price list, when it is active and valid that day and has the product; else the list
   price of the product (Price 1, per sales unit). A line in another unit is converted (1 CS = 12 UN).
2. discount: the discount of the price list line; else the discount of the product's category (or of a parent
   category) in the price list; else the customer's discount; else none.
3. net price = price x (1 - discount %); below the product's minimum price, it is flagged (the invoice refuses
   it, V3).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from powererp import schemas as S
from powererp.core.errors import AppError
from powererp.core.http import require
from powererp.core.values import number, quantity, text, today, unit_cost
from powererp.modules.common.crud import CrudService
from powererp.modules.common.forms import Row
from powererp.modules.common.registry import ReferenceRegistry
from powererp.store import Store


def _pct(value: Any, field: str, detail: str | None = None) -> None:
    if text(value) and not 0 <= number(value) <= 100:
        raise AppError("out_of_range", field, detail=f"{detail}: 0-100" if detail else "0-100")


def is_valid_on(plist: Row, on: str) -> bool:
    """Active, and the day within its validity (an empty date is no limit)."""
    return bool(
        plist.get("lActive")
        and (not plist.get("dStartDate") or plist["dStartDate"] <= on)
        and (not plist.get("dEndDate") or plist["dEndDate"] >= on)
    )


class PriceListService(CrudService):
    kind = "price_list"
    line_schema = S.PRICE_LIST_LINE
    children = {"discounts": S.PRICE_LIST_DISCOUNT}

    def __init__(self, repo: Store, refs: dict[str, Any], references: ReferenceRegistry):
        """refs: given by the container: products, categories (finders), converter (the unit converter)."""
        super().__init__(repo, S.PRICE_LIST, S.DEFAULTS["price_lists"])
        self.refs = refs
        self.references = references
        self.customers_of: Callable[[str], list[str]] = lambda code: []  # set by the module (customers)
        references.register("product", self.uses_product)
        references.register("category", self.uses_category)

    # ---------------------------------------------------------- references
    def uses_product(self, code: str) -> bool:
        return any(ln["cProduct"].upper() == code.upper() for p in self.repo.all() for ln in p.get("lines", []))

    def uses_category(self, code: str) -> bool:
        return any(d["cCategory"].upper() == code.upper() for p in self.repo.all() for d in p.get("discounts", []))

    def keep_line(self, line: Row) -> bool:
        return bool(text(line.get("cProduct")))

    def keep_child(self, key: str, line: Row) -> bool:
        return bool(text(line.get("cCategory")))

    # ---------------------------------------------------------- rules
    def validate(self, row: Row, is_new: bool) -> None:
        require(row, "cDescFR")
        row["cCode"] = row["cCode"].strip().upper()
        if row["dStartDate"] and row["dEndDate"] and row["dEndDate"] < row["dStartDate"]:
            raise AppError("invalid_range", "dEndDate")
        self._check_lines(row)
        self._check_discounts(row)

    def _check_lines(self, row: Row) -> None:
        seen = set()
        for i, ln in enumerate(row.get("lines", []), 1):
            where = f"line {i}"
            prod = self.refs["products"](ln["cProduct"])
            if prod is None:
                raise AppError("unknown_ref", "lines", detail=f"{where}: {ln['cProduct']}")
            if not prod.get("lSellable"):
                raise AppError("not_sellable", "lines", detail=f"{where}: {prod['cCode']}")
            ln["cProduct"] = prod["cCode"]
            sales_uom = prod.get("cSalesUOM") or prod.get("cStockUOM") or ""
            ln["cUOM"] = (ln["cUOM"].strip() or sales_uom).upper()
            if self.refs["converter"].factor(ln["cUOM"], sales_uom, prod) is None:
                raise AppError("no_conversion", "lines", detail=f"{where}: {ln['cUOM']} -> {sales_uom}")
            if not text(ln["dPrice"]):
                raise AppError("required", "lines", detail=f"{where}: dPrice")
            if number(ln["dPrice"]) < 0 or number(ln["dMinQty"]) < 0:
                raise AppError("negative", "lines", detail=where)
            _pct(ln["dDiscountPct"], "lines", where)
            ln["dMinQty"] = quantity(number(ln["dMinQty"])) if text(ln["dMinQty"]) else "0"
            key = (ln["cProduct"].upper(), ln["cUOM"], number(ln["dMinQty"]))
            if key in seen:
                raise AppError("duplicate", "lines", detail=f"{where}: {ln['cProduct']} {ln['cUOM']} {ln['dMinQty']}")
            seen.add(key)
        row["lines"] = sorted(
            row.get("lines", []), key=lambda ln: (ln["cProduct"].upper(), ln["cUOM"], number(ln["dMinQty"]))
        )

    def _check_discounts(self, row: Row) -> None:
        seen = set()
        for i, d in enumerate(row.get("discounts", []), 1):
            where = f"line {i}"
            cat = self.refs["categories"](d["cCategory"])
            if cat is None:
                raise AppError("unknown_ref", "discounts", detail=f"{where}: {d['cCategory']}")
            d["cCategory"] = cat["cCode"]
            if cat["cCode"].upper() in seen:
                raise AppError("duplicate", "discounts", detail=f"{where}: {cat['cCode']}")
            seen.add(cat["cCode"].upper())
            if not text(d["dDiscountPct"]):
                raise AppError("required", "discounts", detail=f"{where}: dDiscountPct")
            _pct(d["dDiscountPct"], "discounts", where)

    def before_delete(self, row: Row) -> None:
        self.references.check(self.kind, row["cCode"])  # the customers using it

    def view(self, row: Row, full: bool = True) -> Row:
        customers = self.customers_of(row["cCode"])
        if full:
            return {**row, "customers": customers}
        return {
            **row,
            "iProducts": len({ln["cProduct"].upper() for ln in row.get("lines", [])}),
            "iCustomers": len(customers),
        }


class PriceResolver:
    """The price a customer pays for a product (see the module's docstring)."""

    def __init__(self, price_lists: PriceListService, customers: Any, products: Any, categories: Any, converter: Any):
        self.price_lists = price_lists
        self.customers = customers
        self.products = products
        self.categories = categories
        self.converter = converter

    def _category_discount(self, plist: Row, category: str) -> tuple[str, str] | None:
        """The discount of the category, else of its parent, grandparent... (category, pct)."""
        by_cat = {d["cCategory"].upper(): d["dDiscountPct"] for d in plist.get("discounts", [])}
        seen: set[str] = set()
        code = text(category)
        while code and code.upper() not in seen:
            seen.add(code.upper())
            if code.upper() in by_cat:
                return code, by_cat[code.upper()]
            cat = self.categories.find(code)
            code = text((cat or {}).get("cParent"))
        return None

    def _best_line(self, plist: Row, prod: Row, uom: str, qty: float) -> tuple[Row, float] | None:
        """The line of the product with the highest minimum quantity reached, and the factor uom -> its unit."""
        best: tuple[float, Row, float] | None = None
        for ln in plist.get("lines", []):
            if ln["cProduct"].upper() != prod["cCode"].upper():
                continue
            f = self.converter.factor(uom, ln["cUOM"] or prod.get("cSalesUOM", ""), prod)
            if f is None:
                continue
            threshold = number(ln["dMinQty"]) / f  # the minimum quantity in the unit asked for
            if threshold <= qty + 1e-9 and (best is None or threshold > best[0]):
                best = (threshold, ln, f)
        return (best[1], best[2]) if best else None

    def price(self, customer_code: str, product_code: str, qty: Any = 1, uom: str = "", on: str | None = None) -> Row:
        on = on or today()
        prod = self.products.find(product_code) if text(product_code) else None
        if prod is None:
            raise AppError("required" if not text(product_code) else "unknown_ref", "product")
        customer = None
        if text(customer_code):
            customer = self.customers.find(customer_code)
            if customer is None:
                raise AppError("unknown_ref", "customer")
        q = number(qty, 1.0) if text(qty) else 1.0
        if q <= 0:
            raise AppError("positive", "qty")
        sales_uom = prod.get("cSalesUOM") or prod.get("cStockUOM") or ""
        uom = (text(uom) or sales_uom).upper()
        to_sales = self.converter.factor(uom, sales_uom, prod)
        if to_sales is None:
            raise AppError("no_conversion", "uom", detail=f"{uom} -> {sales_uom}")

        list_price = number(prod.get("dPrice1")) * to_sales
        price, source, min_qty, line = list_price, "product", "", None
        plist_code = text((customer or {}).get("cPriceList"))
        plist = self.price_lists.find(plist_code) if plist_code else None
        if plist is not None and not is_valid_on(plist, on):
            plist = None
        if plist is not None:
            found = self._best_line(plist, prod, uom, q)
            if found:
                line, f = found
                price, source, min_qty = number(line["dPrice"]) * f, "price_list", line["dMinQty"]

        discount, discount_source, discount_category = "", "", ""
        if line is not None and text(line["dDiscountPct"]):
            discount, discount_source = line["dDiscountPct"], "line"
        elif plist is not None and (cat := self._category_discount(plist, prod.get("cCategory", ""))):
            discount_category, discount = cat
            discount_source = "category"
        elif customer is not None and text(customer.get("dDiscountPct")):
            discount, discount_source = customer["dDiscountPct"], "customer"
        net = price * (1 - number(discount) / 100)
        min_price = number(prod.get("dMinPrice")) * to_sales
        return {
            "cCustomer": (customer or {}).get("cCode", ""),
            "cProduct": prod["cCode"],
            "cUOM": uom,
            "dQty": quantity(q),
            "dDate": on,
            "cPriceList": plist["cCode"] if plist else "",
            "cPriceSource": source,
            "dMinQty": min_qty,
            "dListPrice": unit_cost(list_price),
            "dPrice": unit_cost(price),
            "dDiscountPct": quantity(number(discount)) if discount_source else "",
            "cDiscountSource": discount_source,
            "cDiscountCategory": discount_category,
            "dNetPrice": unit_cost(net),
            "dMinPrice": unit_cost(min_price) if text(prod.get("dMinPrice")) else "",
            "lBelowMinPrice": bool(text(prod.get("dMinPrice")) and net < min_price - 1e-9),
            "lNoPrice": price <= 0,
        }
