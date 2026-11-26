# Supply chain indicators {#rep.scor}

The figures that say how the supply chain is doing over a period, grouped by the four SCOR performance attributes: **reliability**, **responsiveness**, **cost** and **assets**. They answer ISO 9001 9.1 (monitoring, measurement, analysis and evaluation) and give the management review its data. Nothing is typed here: every figure is calculated from the invoices, receptions, production orders, shop floor records, nonconformances and stock movements already in the ERP.

**Where:** **Reports > Supply chain indicators**. The screen is read only; it needs the *View* permission of the screen.

## Period {#rep.scor.period}

The days the figures are calculated on: the last 30 days, the last 90 days (the default), the last 12 months, this year, or **Other dates** (type them in *From* and *To*). The number of days of the period is shown on the right. The stock value, the lots and the open nonconformances are always those of today.

## From {#rep.scor.from}

The first day of the period. Changing it chooses *Other dates*.

## To {#rep.scor.to}

The last day of the period (today by default). A start after the end is refused.

## Lots expiring within {#rep.scor.horizon}

How far ahead the lots that expire are shown (7 to 90 days, 30 by default): the *Lots to expire* figure and the list *Expired or expiring within*. The lots already expired are always shown.

## Reliability {#rep.scor.reliability}

Doing it right: the right product, the right quantity, the right quality, on time. Each figure shows what it is made of (for example *2 of 3 invoices*); a dash means there is nothing to measure in the period.

- **Perfect orders:** the posted sales invoices of the period that no credit note credits. An invoice with a credit note had a problem (wrong quantity, price, product, or goods returned).
- **Production on time:** the production orders completed in the period on or before their due date. Orders without a due date are left out.
- **Production yield:** the quantity made / the quantity ordered, of the orders completed in the period.
- **Supplier fill rate:** the quantity received / the quantity ordered on the receptions of the period (a line counts at most what was ordered).
- **Receptions without a problem:** the receptions of the period without a nonconformance found at reception (a nonconformance with *Found at* Reception and the reception number in *Document*).
- **Steps right first time:** the records of the recipe steps on the shop floor within their limits, of the period.

## Responsiveness {#rep.scor.responsiveness}

How fast things go through.

- **Production cycle time:** the days from the release to the completion of the orders completed in the period, on average.
- **Time to close a nonconformance:** the days from the creation to the closing of the nonconformances closed in the period, on average.

## Cost {#rep.scor.cost}

- **Production cost variance:** (actual cost − estimated cost of the quantity made) / estimated cost, of the orders closed in the period. Above 0: the orders cost more than estimated.
- **Gross margin:** (sales − cost of the goods sold) / sales, of the invoices posted in the period, before taxes. The credit notes subtract.

## Assets {#rep.scor.assets}

The stock: how much there is, how fast it turns and what is at risk.

- **Stock value:** the stock of today in every warehouse, at the unit cost of each product (as in **Inventory > Inventory valuation**).
- **Stock turns:** the value of the stock used in the period (gone out for the sales invoices and the production orders), counted for a year, / the stock value. 12 means the stock is used up about once a month.
- **Days of supply:** the stock value / the value used per day in the period: how many days the stock lasts at this pace.
- **Lots held back:** the value of the lots in stock that are on hold, in quarantine or rejected (**Quality > Lot status**).
- **Lots to expire:** the value of the lots in stock expired or expiring within the horizon.

Click a figure to open the screen behind it (when the role may).

## Lots to watch {#rep.scor.lots}

Two lists: the lots in stock expired or expiring within the horizon (soonest first, red when 7 days or less are left), and the lots held back by quality (largest value first). Click a lot to trace it in **Production > Lots and traceability**.

## Nonconformances {#rep.scor.nc}

How many nonconformances were found in the period and how many are open today, by where they were found (reception, production, internal check, customer complaint) and how serious they are.

## Stock by product {#rep.scor.products}

The products in stock with their quantity, value, the value used in the period, the days of supply and the last day the stock went out. The products not used in the period come first (*Not used*: the slow movers, stock that does not turn), then those with the most days of supply. The 15 first are shown; click one to open it.

## Deviations on the shop floor {#rep.scor.deviations}

The values out of their limits recorded on the steps of the production orders in the period, newest first: when, the order, the step, the value and why it was out, what it did (blocks, holds the lot, warning), the corrective action and who. Click a line to open the order.
