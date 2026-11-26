# PowerERP — Stock card (movements of a stock line): test script

Script to test the stock card of a line of **Inventory > Stock on hand**: a click on the line shows every movement of that product, in that warehouse, location, lot and serial number, oldest first, with in, out, the balance after each movement and the document behind it (reception, production order, invoice, credit note, count). The product screen is still reached from the product code in the list and from the **Open the product** button of the card. Expected values are those of the **Maple products** scenario right after restoring the demo.

**Before you start:** sign in as an administrator, go to **Administration > System settings**, pick the **Maple products** scenario and restore the demo data.

---

## 1. From the list to the stock card

**Inventory > Stock on hand**

| Step | Expected |
|---|---|
| Hover a line | The whole line is highlighted (clickable). The product code is a link. |
| Click the **code** MAPLE-SYRUP-540 | Opens the product (as before). Go back. |
| Click elsewhere on the line MAPLE-SYRUP-540 / FG-06 / MO8 (e.g. the *Location* column) | Opens the stock card. The address is `#/inv/stock/card/MAPLE-SYRUP-540/PLANT/FG-06/MO8/-` (the `-` is the empty serial number). |

## 2. The stock card of the cans of lot MO8

| What to check | Expected |
|---|---|
| Top | "Stock on hand /" (link back to the list), title **MAPLE-SYRUP-540 — Amber maple syrup, 540 ml can**, buttons **?**, **Open the product** and **Trace the lot**. |
| Facts card | *Warehouse / location* PLANT — Usine de transformation - Saint-Georges / FG-06, *Lot* MO8, *Expiry date* 2028-11-02. |
| Figures | *On hand* 236 UN, *Reserved* 0 UN, *Available* 236 UN. |
| *Movements* table (4 movements) | 2026-11-03 *Made by a production order* · Order 8 · in 1,000 · balance 1,000 |
| | 2026-11-06 *Invoice* · Invoice 6 · DISTRIB-CHAUDIERE · out −364 · balance 636 |
| | 2026-11-18 *Invoice* · Invoice 8 · LAURENTIAN-HOTELS · out −200 · balance 436 |
| | 2026-11-20 *Invoice* · Invoice 9 · EPICERIE-STDENIS · out −200 · balance 236 |
| Last line | *Balance today* 236 UN (the *On hand* of the list). |
| Click **Order 8** | Opens production order 8. Go back. |
| Click **Invoice 6** | Opens invoice 6 of DISTRIB-CHAUDIERE. Go back. |
| Click **movement #…** under a date | Opens the movement in **Inventory > Stock movements**. Go back. |
| **Open the product** | Opens product MAPLE-SYRUP-540. |
| **Trace the lot** | Opens **Production > Lots and traceability** on lot MO8. |

## 3. Period (From / To)

| Step | Expected |
|---|---|
| *From* = 2026-11-10 | First line: *Opening balance (movements before this date)* 636. Then only invoices 8 and 9; last line *Balance today* 236. The **All dates** button and "2 movement(s)" appear. |
| *To* = 2026-11-18 | Only invoice 8; last line *Balance at the end of the period* 436. |
| *From* = 2026-12-01, *To* empty | "No movement between these dates."; opening and closing balance 236. |
| **All dates** | Back to the 4 movements. |

## 4. A barrel of raw material (reception and consumption)

In the list, click the line **SYRUP-BULK-AMB / BAR-04 / lot 900102-4**.

| What to check | Expected |
|---|---|
| Movements | 2026-09-10 *Reception* · Reception 900102 · in 270 · balance 270; 2026-11-02 *Used by a production order* · Order 7 · SYRUP-STD · out −175 · balance 95. |
| Click **Reception 900102** | Opens reception 900102. |
| Figures | *On hand* 95 KG. |

## 5. New movements show on the card

| Step | Expected |
|---|---|
| In **Inventory > Stock movements**, a new *Reservation* movement of 10 UN of MAPLE-SYRUP-540, PLANT / FG-06, lot MO8 | Saved. |
| Open the stock card of MO8 again | New line *Reservation (Manual)*: the balance stays 236 with "reserved 10" under it. *Reserved* 10 UN, *Available* 226 UN. |
| A new *Transfer* movement of 6 UN of MAPLE-SYRUP-540 lot MO8, from PLANT / FG-06 to an empty finished goods location | Saved. On the FG-06 card: *Transfer to PLANT / …* out −6, balance 230. In the list, the new line of the destination opens a card with *Transfer from PLANT / FG-06* in 6. |

## 6. Help and French

| Step | Expected |
|---|---|
| **?** on the card | Opens the help of *Stock on hand*, with the **Stock card** section (columns, From, To). The ⓘ icons next to *From* and *To* open the text of each field. |
| **FR** button | Title "Fiche de stock…", columns *Date, Quoi, Document, Client / fournisseur / note, Entrée, Sortie, Solde, Coût unitaire, Valeur, Utilisateur*; kinds *Fabriqué par un ordre de production*, *Facture*... |
| Phone (narrow screen) | The three figures sit side by side; the table scrolls sideways. |

## 7. Access

| Step | Expected |
|---|---|
| A user whose role has **Stock on hand** but not **Products** | The line opens the card; the product code is not a link and **Open the product** is not shown. Documents of screens the role may not open are plain text, without a link. |
| A user without **Stock on hand** | The address of a stock card leads to the Dashboard. |
