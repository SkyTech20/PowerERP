"""Field schemas of the ERP records, shared by the API (validation, payloads) and the tables (powererp.models.master).

kind: s = text, d = number (kept as text "12.50" in the API, NUMERIC in the database), i = integer, b = yes / no,
date = YYYY-MM-DD, (choices) = one of.
"""

from typing import Any

# --------------------------------------------------------------------------- general ledger and suppliers

GL_ACCOUNT = {"cCode": "s", "cDesc": "s"}
COST_CENTER = {"cCC1": "s", "cCC2": "s", "cDesc": "s"}
SUPPLIER = {
    "cCode": "s",
    "cName": "s",
    "cTermCode": "s",
    "cTermDesc": "s",
    "cAddress1": "s",
    "cAddress2": "s",
    "cCity": "s",
    "cProvince": "s",
    "cCountry": "s",
    "cZipCode": "s",
    "cNoTPS": "s",
    "cNoTVQ": "s",
    "cCodeAch": "s",
    "cDescAch": "s",
    "cDeptSauv": "s",
    "iTypePO": "i",
    "iStatutAch": "i",
}

# --------------------------------------------------------------------------- choices

# a product is classified on three axes: physical or not (a software licence is not), product or service, and its
# class (empty for an item bought for resale, and for a service); only a physical product can have its stock controlled
PRODUCT_STOCK_TYPES = ("physical", "nonphysical")
PRODUCT_NATURES = ("product", "service")
PRODUCT_CLASSES = ("", "raw", "kit", "finished", "consumable", "asset")
PRODUCT_STATUS = ("active", "inactive", "discontinued")
COST_METHODS = ("avg", "std")
TAX_KINDS = ("gst", "pst", "hst", "other")
TAX_TREATMENTS = ("taxable", "zero", "exempt")
UOM_TYPES = ("count", "weight", "length", "area", "volume", "time")
WAREHOUSE_TYPES = ("main", "transit", "consignment", "quarantine", "virtual")
LOCATION_TYPES = ("picking", "reserve", "receiving", "shipping", "quarantine", "staging")
PICK_POLICIES = ("", "FEFO", "FIFO", "LIFO")  # first expired / first in / last in first out
MOVE_TYPES = ("IN", "OUT", "TRF", "ADJ", "CNT", "RSV")
DOC_TYPES = ("MAN", "PO", "REC", "INV", "SO", "CNT", "PROD")
COUNT_STATUS = ("Draft", "Posted")
# production: TPM loss groups of a stop (planned stops do not count against OEE availability) and scrap causes
DOWNTIME_GROUPS = (
    "breakdown",
    "setup",
    "minor_stop",
    "reduced_speed",
    "no_material",
    "no_operator",
    "quality",
    "planned",
    "other",
)
SCRAP_GROUPS = ("material", "process", "machine", "operator", "startup", "other")
WORK_CENTER_TYPES = ("machine", "line", "labor", "subcontract")
RUN_FORMATS = ("min_per_unit", "units_per_hour", "min_per_lot")
SETUP_SCOPES = ("work_center", "resource")
MAKE_BUY = ("make", "buy", "both")
TRACE_LEVELS = ("none", "lot", "serial")
RECIPE_STATUS = ("draft", "in_review", "approved", "obsolete")
PROCESS_TYPES = ("discrete", "batch", "continuous")
ISSUE_METHODS = ("manual", "backflush", "pick")
OUTPUT_KINDS = ("coproduct", "byproduct")
STEP_KINDS = ("instruction", "material_add", "parameter", "measure", "check", "timer", "output", "signature")
STEP_DATA_TYPES = ("number", "text", "yes_no", "list", "photo")
STEP_ON_FAIL = ("block", "warn", "hold_lot")
STEP_FREQUENCIES = ("once", "every_n_units", "every_n_min", "per_lot")
# M3: production orders: draft -> released -> in_progress -> completed -> closed; cancelled from draft / released
ORDER_STATUS = ("draft", "released", "in_progress", "completed", "closed", "cancelled")

# --------------------------------------------------------------------------- schemas
# kind: s = text, d = number (kept as text "12.50"), i = integer, b = yes / no, date = YYYY-MM-DD, (choices) = one of

TAX_CODE = {
    "cCode": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "cKind": TAX_KINDS,
    "cJurisdiction": "s",
    "cRegistrationNo": "s",
    "cGLCollected": "s",
    "cGLRecoverable": "s",
    "dRecoverablePct": "d",
    "lActive": "b",
}
TAX_RATE = {"dStartDate": "date", "dEndDate": "date", "dRate": "d"}
TAX_GROUP = {
    "cCode": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "cProvince": "s",
    "cTreatment": TAX_TREATMENTS,
    "lActive": "b",
}
TAX_GROUP_LINE = {"iSeq": "i", "cTaxCode": "s", "lCompound": "b"}
UOM = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "cType": UOM_TYPES, "lActive": "b"}
# general conversions between units, for every product: 1 cFromUOM = dFactor cToUOM (1 KG = 1000 G)
UOM_CONVERSION = {"cFromUOM": "s", "cToUOM": "s", "dFactor": "d", "cNotes": "s", "lActive": "b"}
# conversions of one product (its packaging): 1 cUOM = dFactor stock units (flour: 1 BAG = 25 KG)
PRODUCT_UOM = {"cUOM": "s", "dFactor": "d", "cNotes": "s"}
CATEGORY = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "cParent": "s", "lActive": "b"}
PRODUCT = {
    # identification
    "cCode": "s",
    "cStatus": PRODUCT_STATUS,
    "cStockType": PRODUCT_STOCK_TYPES,
    "cNature": PRODUCT_NATURES,
    "cClass": PRODUCT_CLASSES,
    "cDescFR": "s",
    "cDescEN": "s",
    "cLongDescFR": "s",
    "cLongDescEN": "s",
    "cCategory": "s",
    "cBrand": "s",
    "cModel": "s",
    "cUPC": "s",
    "cManufacturer": "s",
    "cMfrPartNo": "s",
    "cImageUrl": "s",
    "cSpecUrl": "s",
    "cSdsUrl": "s",
    # units and dimensions
    "cStockUOM": "s",
    "cPurchaseUOM": "s",
    "cSalesUOM": "s",
    "dWeight": "d",
    "cWeightUOM": "s",
    "dLength": "d",
    "dWidth": "d",
    "dHeight": "d",
    "cDimUOM": "s",
    "dVolume": "d",
    # costs and prices
    "cCostMethod": COST_METHODS,
    "dStdCost": "d",
    "cCurrency": "s",
    "dPrice1": "d",
    "dPrice2": "d",
    "dPrice3": "d",
    "dPrice4": "d",
    "dPrice5": "d",
    "dMinPrice": "d",
    # taxes
    "cSalesTaxGroup": "s",
    "cPurchaseTaxGroup": "s",
    "dEcoFee": "d",
    "cEcoFeeCode": "s",
    # accounting
    "cGLSales": "s",
    "cGLPurchase": "s",
    "cGLInventory": "s",
    "cGLCOGS": "s",
    "cCostCenter": "s",
    "cProject": "s",
    # inventory
    "lStocked": "b",
    "lLotControl": "b",
    "lSerialControl": "b",
    "lExpiryControl": "b",
    "cPickPolicy": PICK_POLICIES,  # which stock goes out first (a sale): "" = FEFO with an expiry date, else FIFO
    "iShelfLifeDays": "i",
    "cDefaultWarehouse": "s",
    "cABCClass": ("", "A", "B", "C"),
    # sales and logistics
    "lSellable": "b",
    "lPurchasable": "b",
    "lPORequired": "b",
    "iWarrantyMonths": "i",
    "cCountryOrigin": "s",
    "cHSCode": "s",
    "cFreightClass": "s",
    "lHazardous": "b",
    "cNotes": "s",
}
PRODUCT_SUPPLIER = {
    "cSupplierCode": "s",
    "cSupplierItem": "s",
    "dPurchasePrice": "d",
    "cCurrency": "s",
    "iLeadTimeDays": "i",
    "dMinOrderQty": "d",
    "lPreferred": "b",
}
WAREHOUSE = {
    "cCode": "s",
    "cNameFR": "s",
    "cNameEN": "s",
    "cType": WAREHOUSE_TYPES,
    "cAddress1": "s",
    "cCity": "s",
    "cProvince": "s",
    "cZipCode": "s",
    "cCountry": "s",
    "cManager": "s",
    "cPhone": "s",
    "cEmail": "s",
    "lUseLocations": "b",
    "lAllowNegative": "b",
    "cReceivingLoc": "s",
    "cShippingLoc": "s",
    "lActive": "b",
}
LOCATION = {
    "cWarehouse": "s",
    "cCode": "s",
    "cZone": "s",
    "cAisle": "s",
    "cRack": "s",
    "cLevel": "s",
    "cBin": "s",
    "cDescription": "s",
    "cType": LOCATION_TYPES,
    "dMaxWeight": "d",
    "dMaxVolume": "d",
    "iMaxPallets": "i",
    "lMixProducts": "b",
    "lBlocked": "b",
    "iPickSeq": "i",
    "lActive": "b",
}
STOCK_PARAM = {
    "cProduct": "s",
    "cWarehouse": "s",
    "dReorderPoint": "d",
    "dMinQty": "d",
    "dMaxQty": "d",
    "dOrderQty": "d",
    "cDefaultLocation": "s",
    "iLeadTimeDays": "i",
    "lActive": "b",
}
MOVEMENT = {
    "dDate": "date",
    "cType": MOVE_TYPES,
    "cProduct": "s",
    "dQty": "d",
    "dUnitCost": "d",
    "cWarehouse": "s",
    "cLocation": "s",
    "cWhTo": "s",
    "cLocTo": "s",
    "cLot": "s",
    "cSerial": "s",
    "dExpiry": "date",
    "cDocType": DOC_TYPES,
    "cDocNo": "s",
    "cReason": "s",
    "cComment": "s",
}
COUNT = {"cWarehouse": "s", "dDate": "date", "cDescription": "s", "cLocationPrefix": "s", "cProductPrefix": "s"}
COUNT_LINE = {"cProduct": "s", "cLocation": "s", "cLot": "s", "cSerial": "s", "dQtyExpected": "d", "dQtyCounted": "d"}

# --------------------------------------------------------------------------- production (M0: reference lists)
CAPABILITY = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "lActive": "b"}  # what a resource can do (e.g. CUT)
SETUP_FAMILY = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "lActive": "b"}  # products changing over alike
DOWNTIME_REASON = {
    "cCode": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "cGroup": DOWNTIME_GROUPS,
    "lAffectsOEE": "b",
    "lActive": "b",
}
SCRAP_REASON = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "cGroup": SCRAP_GROUPS, "lActive": "b"}
# P2: working calendars. Times are "HH:MM"; a shift ending at or before its start ends the next day (22:00-06:00).
CALENDAR = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "lActive": "b"}
CALENDAR_SHIFT = {"iWeekday": "i", "cShift": "s", "cStart": "s", "cEnd": "s", "iBreakMin": "i"}  # 1 = Monday
# A date that differs from the week: closed (holiday) or other hours (overtime). cCalendar "*" = every calendar.
CALENDAR_EXCEPTION = {
    "cCalendar": "s",
    "dDate": "date",
    "cDescFR": "s",
    "cDescEN": "s",
    "lClosed": "b",
    "cStart": "s",
    "cEnd": "s",
    "iBreakMin": "i",
}
# P3: work centers, the groups of machines / stations doing the same work (Epicor resource group)
WORK_CENTER = {
    "cCode": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "cType": WORK_CENTER_TYPES,
    "cCalendar": "s",
    "lFinite": "b",  # finite capacity: the scheduler never loads it beyond its calendar
    "dEfficiencyPct": "d",  # real output vs the standard times (100 = as planned)
    "dUtilizationPct": "d",  # share of the calendar time really available (breakdowns, meetings...)
    "dSetupRateHr": "d",
    "dRunRateHr": "d",
    "dBurdenRateHr": "d",
    "cCostCenter": "s",
    "cWarehouse": "s",
    "cInLocation": "s",  # where the materials are staged for the work center
    "cOutLocation": "s",  # where its output is put
    "iQueueMin": "i",
    "iMoveMin": "i",
    "cSupplier": "s",  # subcontract work centers
    "cNotes": "s",
    "lActive": "b",
}
# P4: resources, the machines / stations / teams that do the work, and their child lists
RESOURCE = {
    "cCode": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "cWorkCenter": "s",
    "cCalendar": "s",  # empty = the work center's
    "dSpeedFactor": "d",  # 1 = the standard times; 1.2 = 20 % faster
    "iParallel": "i",  # how many orders it runs at the same time
    "cManufacturer": "s",
    "cModel": "s",
    "cSerialNo": "s",
    "cNotes": "s",
    "lActive": "b",
}
RESOURCE_CAPABILITY = {"cCapability": "s", "iPreference": "i"}  # 1 = preferred
RESOURCE_ATTRIBUTE = {
    "cAttribute": "s",
    "cUOM": "s",
    "dMin": "d",
    "dMax": "d",
    "cValue": "s",
}  # e.g. width 2.5 to 5.4 m
RESOURCE_SUBRESOURCE = {"cCode": "s", "cDescFR": "s", "cDescEN": "s"}  # parts of the machine, to say where a stop was
# planned downtime (preventive maintenance...): from date + time to date + time
RESOURCE_DOWNTIME = {
    "dStart": "date",
    "cStartTime": "s",
    "dEnd": "date",
    "cEndTime": "s",
    "cReason": "s",
    "cNotes": "s",
}
# P5: standard operations (Epicor OpMaster): the catalog the recipe operations start from
OPERATION = {
    "cCode": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "cWorkCenter": "s",  # where it runs ... or
    "cCapability": "s",  # ... what it needs: any resource having the capability can run it
    "cRunFormat": RUN_FORMATS,
    "dSetupMin": "d",
    "dRunValue": "d",  # in cRunFormat: 6.5 min per unit, 1,200 units per hour, 25 min per lot
    "iCrew": "i",  # operators needed
    "lReportingPoint": "b",  # the operator reports the quantity done at this operation
    "lSubcontract": "b",
    "cSupplier": "s",
    "dSubcontractCost": "d",  # per unit
    "iSubcontractDays": "i",
    "cInstructionFR": "s",
    "cInstructionEN": "s",
    "lActive": "b",
}
# P6: setup matrix, one per work center or resource: minutes to change over from a setup family to another
SETUP_MATRIX = {"cScope": SETUP_SCOPES, "cScopeCode": "s", "cNotes": "s", "lActive": "b"}
SETUP_MATRIX_LINE = {
    "cFromFamily": "s",
    "cToFamily": "s",
    "dSetupMin": "d",
    "dSetupCost": "d",
    "dScrapQty": "d",
}  # "*" = any
# P7: the manufacturing data of a product (the "Manufacturing" tab), kept by Production next to the item master
PRODUCT_MFG = {
    "cProduct": "s",
    "cMakeBuy": MAKE_BUY,
    "cSetupFamily": "s",
    "dMfgLotMin": "d",
    "dMfgLotMultiple": "d",
    "iMfgLeadDays": "i",
    "lPhantom": "b",  # a sub-assembly never stocked: its materials go up to the parent's order
    "cTraceLevel": TRACE_LEVELS,
    "cNotes": "s",
}
PRODUCT_ATTRIBUTE = {"cAttribute": "s", "cUOM": "s", "dNumber": "d", "cValue": "s"}  # width 2.4 m, colour "white"
# P8: recipes, the full method to make a product (Epicor method of manufacturing): one per product + revision
RECIPE = {
    "cProduct": "s",
    "cRevision": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "cProcessType": PROCESS_TYPES,
    "dBaseQty": "d",  # the recipe is written for this quantity of the product
    "cUOM": "s",
    "dMinBatch": "d",
    "dMaxBatch": "d",  # also the lot size of the min_per_lot operations
    "dYieldPct": "d",  # good output / input of the whole recipe
    "cNotes": "s",
    "cChangeReason": "s",  # P10: why this version (shown in the history and the comparison)
    "dEffectiveFrom": "date",
    "dEffectiveTo": "date",
}
# changed by the approval flow (P10), not by an edit
RECIPE_EXTRA = {
    "cStatus": RECIPE_STATUS,
    "lDefault": "b",  # the approved version used by the new orders of the product
    "cSubmittedBy": "s",
    "cApprovedBy": "s",
    "dApprovedAt": "ts",
}
RECIPE_HISTORY = {"dAt": "ts", "cUser": "s", "cAction": "s", "cFrom": "s", "cTo": "s", "cComment": "s"}
RECIPE_MATERIAL = {
    "iSeq": "i",
    "cComponent": "s",
    "dQtyPer": "d",  # for the base quantity
    "cUOM": "s",
    "lFixedQty": "b",  # per batch whatever the quantity (e.g. a starter)
    "dScrapPct": "d",
    "iOpSeq": "i",  # the operation where it is consumed (0 = the first one)
    "cIssueMethod": ISSUE_METHODS,
    "cWarehouse": "s",
    "cNotes": "s",
}
RECIPE_OUTPUT = {"cProduct": "s", "cKind": OUTPUT_KINDS, "dQtyPer": "d", "cUOM": "s", "dCostPct": "d"}
RECIPE_OPERATION = {
    "iOpSeq": "i",
    "cOperation": "s",  # the standard operation it starts from (P5)
    "cDescFR": "s",
    "cDescEN": "s",
    "cWorkCenter": "s",  # where: a work center, a resource or a capability (one of them), or subcontracted
    "cResource": "s",
    "cCapability": "s",
    "dSetupMin": "d",
    "cRunFormat": RUN_FORMATS,
    "dRunValue": "d",
    "iCrew": "i",
    "iQueueMin": "i",
    "iMoveMin": "i",
    "dMinWaitMin": "d",  # after the operation, before the next one (proofing, curing)
    "dMaxWaitMin": "d",  # 0 / empty = no limit ("must not wait" otherwise)
    "dYieldPct": "d",
    "lReportingPoint": "b",
    "lSubcontract": "b",
    "cSupplier": "s",
    "dSubcontractCost": "d",
    "iSubcontractDays": "i",
    "cPredecessors": "s",  # "10, 20": operations that must end first; empty = the previous one
    "cInstructionFR": "s",
    "cInstructionEN": "s",
}
# P9: the steps of each operation of a recipe ("the recipe step by step"), one parameter per step
RECIPE_STEP = {
    "iOpSeq": "i",
    "iStep": "i",
    "cKind": STEP_KINDS,
    "cTitleFR": "s",
    "cTitleEN": "s",
    "cInstructionFR": "s",
    "cInstructionEN": "s",
    "cAttachmentUrl": "s",  # photo, drawing, video, safety data sheet
    "dDurationMin": "d",
    "cParam": "s",  # code of the value recorded (TEMP_PATE), used by the conditions of the next steps
    "cDataType": STEP_DATA_TYPES,
    "cUOM": "s",
    "dTarget": "d",
    "dMin": "d",
    "dMax": "d",
    "cOptions": "s",  # list: "OK, Retouche, Rebut"
    "lRequired": "b",
    "lCritical": "b",  # critical control point: out of limits -> cOnFail
    "cOnFail": STEP_ON_FAIL,
    "cFrequency": STEP_FREQUENCIES,
    "dFrequencyValue": "d",  # every N units / N minutes
    "iMaterialSeq": "i",  # material_add: the line of the materials
    "cRequiredRole": "s",
    "lSecondSignature": "b",
    "cCondition": "s",  # done only when an earlier value matches: "TEMP_PATE < 24"
}

# ---------------------------------------------------------------- production orders (M3)
PRODUCTION_ORDER = {  # what the screen sends; the rest comes from the recipe (PRODUCTION_ORDER_EXTRA)
    "cProduct": "s",
    "cRevision": "s",  # empty = the version new orders use on the start date (default approved recipe)
    "dQty": "d",  # in the unit of the recipe
    "cWarehouse": "s",  # where the materials come from and the product goes (empty = the product's default)
    "dStart": "date",
    "dDue": "date",
    "cNotes": "s",
}
PRODUCTION_ORDER_EXTRA = {
    "iNo": "i",
    "cStatus": ORDER_STATUS,
    "cDescFR": "s",
    "cDescEN": "s",
    "cUOM": "s",  # the unit of the recipe
    "dQtyDone": "d",  # M3b: good quantity reported
    "cLot": "s",  # M3b: the lot of the product made
    "dEstMaterialCost": "d",
    "dEstOperationCost": "d",
    "dEstCost": "d",
    "dEstUnitCost": "d",
    "dTotalMin": "d",
    "cUser": "s",
    "dCreated": "ts",
    "dReleased": "ts",
    "cReleasedBy": "s",
}
ORDER_MATERIAL = {  # the materials of the recipe for the quantity of the order, in stock units
    "iSeq": "i",
    "cComponent": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "iOpSeq": "i",
    "cIssueMethod": ISSUE_METHODS,
    "cWarehouse": "s",
    "dQtyRequired": "d",
    "cUOM": "s",  # stock unit of the component
    "dQtyIssued": "d",  # M3b
    "dUnitCost": "d",
    "dCost": "d",
}
ORDER_OPERATION = {
    "iOpSeq": "i",
    "cOperation": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "cWhere": "s",  # resource, work center, capability or supplier
    "dSetupMin": "d",
    "dRunMin": "d",
    "dWaitMin": "d",
    "dCost": "d",
}
ORDER_HISTORY = {"dAt": "ts", "cUser": "s", "cAction": "s", "cFrom": "s", "cTo": "s", "cComment": "s"}

# ---------------------------------------------------------------- sales (V1): company profile and customers
LANGS = ("fr", "en")
COMPANY_PROFILE = {  # one row (cCode MAIN): the header of the invoices; the GST / QST numbers are on the tax codes
    "cCode": "s",
    "cName": "s",
    "cLegalName": "s",
    "cAddress1": "s",
    "cAddress2": "s",
    "cCity": "s",
    "cProvince": "s",
    "cZipCode": "s",
    "cCountry": "s",
    "cPhone": "s",
    "cEmail": "s",
    "cWebsite": "s",
    "cNEQ": "s",  # Quebec enterprise number
    "cInvoiceNoteFR": "s",  # printed at the bottom of the invoices
    "cInvoiceNoteEN": "s",
    "iInvoiceStart": "i",  # the invoice numbers start at (V4: never below it; 0 = 1)
}
CUSTOMER = {
    "cCode": "s",
    "cName": "s",
    "cLegalName": "s",
    "cLang": LANGS,  # language of its invoices
    "cAddress1": "s",  # billing address
    "cAddress2": "s",
    "cCity": "s",
    "cProvince": "s",
    "cZipCode": "s",
    "cCountry": "s",
    "cPhone": "s",
    "cEmail": "s",  # where the invoices are sent
    "cTaxGroup": "s",  # taxes charged when its ship-to address has none
    "cTaxExemptNo": "s",
    "cTermCode": "s",
    "cTermDesc": "s",
    "cPriceList": "s",  # its prices (V2); empty = the list price of the products
    "dDiscountPct": "d",  # discount on every line, unless its price list gives another one (V2)
    "cWarehouse": "s",  # warehouse its orders are shipped from
    "cNotes": "s",
    "lActive": "b",
}
CUSTOMER_ADDRESS = {  # ship-to addresses
    "cCode": "s",
    "cName": "s",
    "cAddress1": "s",
    "cAddress2": "s",
    "cCity": "s",
    "cProvince": "s",
    "cZipCode": "s",
    "cCountry": "s",
    "cContact": "s",
    "cPhone": "s",
    "cTaxGroup": "s",  # taxes of the place of delivery (empty = the customer's)
    "lDefault": "b",
}
CUSTOMER_CONTACT = {"cName": "s", "cTitle": "s", "cPhone": "s", "cEmail": "s", "lInvoices": "b"}
# ---------------------------------------------------------------- sales (V2): price lists and discounts
PRICE_LIST = {
    "cCode": "s",
    "cDescFR": "s",
    "cDescEN": "s",
    "dStartDate": "date",  # valid from / to (empty = no limit); outside, its customers pay the list price
    "dEndDate": "date",
    "cNotes": "s",
    "lActive": "b",
}
PRICE_LIST_LINE = {  # the price of a product from a quantity (quantity breaks: one line per minimum quantity)
    "cProduct": "s",
    "cUOM": "s",  # empty = the sales unit of the product
    "dMinQty": "d",
    "dPrice": "d",
    "dDiscountPct": "d",  # replaces the category / customer discount for this product
}
PRICE_LIST_DISCOUNT = {"cCategory": "s", "dDiscountPct": "d"}  # also on the subcategories
# ---------------------------------------------------------------- sales (V3): invoices
INVOICE_STATUS = ("draft", "posted")
INVOICE_TYPES = ("invoice", "credit")  # V6: a credit note credits a posted invoice
SALES_INVOICE = {  # what the screen sends; the rest is calculated (SALES_INVOICE_EXTRA)
    "cType": INVOICE_TYPES,  # given when created, never changed
    "cOrigInvoice": "s",  # a credit note: the number of the invoice it credits
    "cCustomer": "s",
    "cShipTo": "s",  # code of a ship-to address of the customer (empty = its default one)
    "dDate": "date",
    "cWarehouse": "s",  # where the goods leave from (empty = the customer's)
    "cCustomerPO": "s",  # the customer's purchase order number
    "cLang": "s",  # fr / en (empty = the customer's)
    "cTermCode": "s",
    "cTermDesc": "s",
    "cNotes": "s",
}
SALES_INVOICE_EXTRA = {
    "iNo": "i",  # internal number (the drafts); the invoice number is given when it is posted (V4)
    "cStatus": INVOICE_STATUS,
    "cInvoiceNo": "s",
    "cCustomerName": "s",
    "cTaxGroup": "s",  # of the place of delivery: the ship-to address's, else the customer's
    "dSubTotal": "d",  # the lines after their discounts
    "dDiscountTotal": "d",
    "dTaxTotal": "d",
    "dTotal": "d",
    "cUser": "s",
    "dCreated": "ts",
    "dPosted": "ts",  # V4: posted (the stock went out, the invoice number given, no more changes)
    "cPostedBy": "s",
    "dCost": "d",  # cost of the goods sold (the value of the stock movements)
}
SALES_INVOICE_LINE = {
    "cProduct": "s",
    "cDescription": "s",
    "dQty": "d",
    "cUOM": "s",  # empty = the sales unit of the product
    "dPrice": "d",  # empty = the customer's price (V2)
    "dDiscountPct": "d",  # empty = the customer's discount (V2)
    "dNetPrice": "d",  # calculated from here on
    "dAmount": "d",
    "cTaxGroup": "s",
    "cPriceSource": "s",  # price_list / product / manual
    "iOrigLine": "i",  # a credit note: the line of the invoice it credits (0 = the first one of the product)
    "lReturn": "b",  # a credit note: the goods come back to the stock (else: a price adjustment)
}
SALES_INVOICE_TAX = {"cTaxGroup": "s", "cTaxCode": "s", "cKind": "s", "dRate": "d", "dBase": "d", "dTax": "d"}
SALES_INVOICE_ALLOC = {  # V4: what went out of the stock for each line (lots first expiring first), in stock units
    "iLine": "i",
    "cProduct": "s",
    "cWarehouse": "s",
    "cLocation": "s",
    "cLot": "s",
    "cSerial": "s",
    "dExpiry": "date",
    "dQty": "d",
    "cUOM": "s",
    "iMovement": "i",
    "dValue": "d",
}

DEFAULTS: dict[str, dict[str, Any]] = {
    "tax_codes": {"cKind": "other", "dRecoverablePct": "100", "lActive": True},
    "tax_groups": {"cTreatment": "taxable", "lActive": True},
    "uom": {"cType": "count", "lActive": True},
    "uom_conversions": {"lActive": True},
    "categories": {"lActive": True},
    "products": {
        "cStatus": "active",
        "cStockType": "physical",
        "cNature": "product",
        "cCostMethod": "avg",
        "cCurrency": "CAD",
        "cStockUOM": "UN",
        "cPurchaseUOM": "UN",
        "cSalesUOM": "UN",
        "lStocked": True,
        "lSellable": True,
        "lPurchasable": True,
        "cWeightUOM": "kg",
        "cDimUOM": "cm",
        "cCountryOrigin": "CA",
    },
    "warehouses": {"cType": "main", "cProvince": "QC", "cCountry": "CA", "lUseLocations": True, "lActive": True},
    "locations": {"cType": "picking", "lMixProducts": True, "lActive": True},
    "stock_params": {"lActive": True},
    "capabilities": {"lActive": True},
    "setup_families": {"lActive": True},
    "downtime_reasons": {"cGroup": "breakdown", "lAffectsOEE": True, "lActive": True},
    "scrap_reasons": {"cGroup": "process", "lActive": True},
    "calendars": {"lActive": True},
    "calendar_exceptions": {"cCalendar": "*", "lClosed": True},
    "work_centers": {
        "cType": "machine",
        "lFinite": True,
        "dEfficiencyPct": "100",
        "dUtilizationPct": "100",
        "lActive": True,
    },
    "resources": {"dSpeedFactor": "1", "iParallel": 1, "lActive": True},
    "operations": {"cRunFormat": "min_per_unit", "iCrew": 1, "lReportingPoint": True, "lActive": True},
    "setup_matrices": {"cScope": "work_center", "lActive": True},
    "product_mfg": {"cMakeBuy": "make", "cTraceLevel": "lot"},
    "company_profile": {"cCode": "MAIN", "cProvince": "QC", "cCountry": "CA"},
    "price_lists": {"lActive": True},
    "customers": {"cLang": "fr", "cProvince": "QC", "cCountry": "CA", "cTaxGroup": "QC", "lActive": True},
    "recipes": {"cRevision": "A", "cProcessType": "discrete", "dBaseQty": "1", "dYieldPct": "100", "cStatus": "draft"},
}
