"""Products: the purchase / sales units convert to the stock unit with the unit conversions (0015); the factors of
the product (purchase_factor, sales_factor) are dropped. A unit that did not convert gets a conversion of the
product with its old factor (a case of 25: 1 CS = 25 UN), so nothing that was bought or sold changes.

Revision ID: 0022
Revises: 0021
Create Date: 2026-11-24
"""
from collections import deque

from alembic import op
import sqlalchemy as sa


revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None


def _converts(graph, a, b):
    """True when unit a reaches unit b through the conversions (both upper case)."""
    if a == b:
        return True
    seen, todo = {a}, deque([a])
    while todo:
        for y in graph.get(todo.popleft(), ()):
            if y == b:
                return True
            if y not in seen:
                seen.add(y)
                todo.append(y)
    return False


def upgrade():
    bind = op.get_bind()
    general = {}  # company -> unit -> units it converts with
    for company, a, b in bind.execute(
        sa.text("SELECT company_id, upper(from_uom), upper(to_uom) FROM uom_conversions WHERE active AND factor > 0")
    ):
        g = general.setdefault(company, {})
        g.setdefault(a, set()).add(b)
        g.setdefault(b, set()).add(a)
    own = {}  # product -> [(unit, line_no)]
    for parent, uom, line_no in bind.execute(
        sa.text("SELECT parent_id, upper(uom), line_no FROM products_conversions WHERE factor > 0")
    ):
        own.setdefault(parent, []).append((uom, line_no))
    rows = bind.execute(
        sa.text(
            "SELECT id, company_id, upper(stock_uom), upper(purchase_uom), purchase_factor, upper(sales_uom), "
            "sales_factor FROM products ORDER BY id"
        )
    ).fetchall()
    for pid, company, stock, purchase, pfactor, sales, sfactor in rows:
        if not stock:
            continue
        graph = {k: set(v) for k, v in general.get(company, {}).items()}
        lines = own.get(pid, [])
        for uom, _ in lines:
            graph.setdefault(uom, set()).add(stock)
            graph.setdefault(stock, set()).add(uom)
        line_no = max((n for _, n in lines), default=0)
        for uom, factor in ((purchase, pfactor), (sales, sfactor)):
            if not uom or _converts(graph, uom, stock):
                continue
            line_no += 1
            bind.execute(
                sa.text(
                    "INSERT INTO products_conversions (parent_id, line_no, uom, factor, notes) "
                    "VALUES (:p, :n, COALESCE((SELECT code FROM uoms WHERE company_id = :c AND upper(code) = :u LIMIT 1), :u), "
                    ":f, '')"
                ),
                {"p": pid, "n": line_no, "c": company, "u": uom, "f": factor if factor and factor > 0 else 1},
            )
            graph.setdefault(uom, set()).add(stock)
            graph.setdefault(stock, set()).add(uom)
    op.drop_column('products', 'sales_factor')
    op.drop_column('products', 'purchase_factor')


def downgrade():
    op.add_column('products', sa.Column('purchase_factor', sa.Numeric(), nullable=True))
    op.add_column('products', sa.Column('sales_factor', sa.Numeric(), nullable=True))
    # Back to one factor per unit: the product's own conversion of that unit, else 1
    for col, unit in (('purchase_factor', 'purchase_uom'), ('sales_factor', 'sales_uom')):
        op.execute(
            f"UPDATE products p SET {col} = COALESCE((SELECT c.factor FROM products_conversions c "
            f"WHERE c.parent_id = p.id AND upper(c.uom) = upper(p.{unit}) ORDER BY c.line_no LIMIT 1), 1)"
        )
