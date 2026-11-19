"""Field schemas of the ERP records, shared by the API (validation, payloads) and the tables (powererp.models.master).

kind: s = text, d = number (kept as text "12.50" in the API, NUMERIC in the database), i = integer, b = yes / no,
date = YYYY-MM-DD, (choices) = one of.
"""

# --------------------------------------------------------------------------- general ledger and suppliers

GL_ACCOUNT = {"cCode": "s", "cDesc": "s"}
COST_CENTER = {"cCC1": "s", "cCC2": "s", "cDesc": "s"}
SUPPLIER = {"cCode": "s", "cName": "s", "cTermCode": "s", "cTermDesc": "s", "cAddress1": "s", "cAddress2": "s",
            "cCity": "s", "cProvince": "s", "cCountry": "s", "cZipCode": "s", "cNoTPS": "s", "cNoTVQ": "s",
            "cCodeAch": "s", "cDescAch": "s", "cDeptSauv": "s", "iTypePO": "i", "iStatutAch": "i"}

# --------------------------------------------------------------------------- choices

PRODUCT_TYPES = ("stock", "nonstock", "service", "kit", "raw")
STOCKED_TYPES = ("stock", "kit", "raw")
PRODUCT_STATUS = ("active", "inactive", "discontinued")
COST_METHODS = ("avg", "std")
TAX_KINDS = ("gst", "pst", "hst", "other")
TAX_TREATMENTS = ("taxable", "zero", "exempt")
UOM_TYPES = ("count", "weight", "length", "area", "volume", "time")
WAREHOUSE_TYPES = ("main", "transit", "consignment", "quarantine", "virtual")
LOCATION_TYPES = ("picking", "reserve", "receiving", "shipping", "quarantine", "staging")
MOVE_TYPES = ("IN", "OUT", "TRF", "ADJ", "CNT", "RSV")
DOC_TYPES = ("MAN", "PO", "REC", "INV", "SO", "CNT", "PROD")
COUNT_STATUS = ("Draft", "Posted")

# --------------------------------------------------------------------------- schemas
# kind: s = text, d = number (kept as text "12.50"), i = integer, b = yes / no, date = YYYY-MM-DD, (choices) = one of

TAX_CODE = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "cKind": TAX_KINDS, "cJurisdiction": "s",
            "cRegistrationNo": "s", "cGLCollected": "s", "cGLRecoverable": "s", "dRecoverablePct": "d", "lActive": "b"}
TAX_RATE = {"dStartDate": "date", "dEndDate": "date", "dRate": "d"}
TAX_GROUP = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "cProvince": "s", "cTreatment": TAX_TREATMENTS, "lActive": "b"}
TAX_GROUP_LINE = {"iSeq": "i", "cTaxCode": "s", "lCompound": "b"}
UOM = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "cType": UOM_TYPES, "lActive": "b"}
CATEGORY = {"cCode": "s", "cDescFR": "s", "cDescEN": "s", "cParent": "s", "lActive": "b"}
PRODUCT = {
    # identification
    "cCode": "s", "cStatus": PRODUCT_STATUS, "cType": PRODUCT_TYPES, "cDescFR": "s", "cDescEN": "s",
    "cLongDescFR": "s", "cLongDescEN": "s", "cCategory": "s", "cBrand": "s", "cModel": "s", "cUPC": "s",
    "cManufacturer": "s", "cMfrPartNo": "s", "cImageUrl": "s", "cSpecUrl": "s", "cSdsUrl": "s",
    # units and dimensions
    "cStockUOM": "s", "cPurchaseUOM": "s", "dPurchaseFactor": "d", "cSalesUOM": "s", "dSalesFactor": "d",
    "dWeight": "d", "cWeightUOM": "s", "dLength": "d", "dWidth": "d", "dHeight": "d", "cDimUOM": "s", "dVolume": "d",
    # costs and prices
    "cCostMethod": COST_METHODS, "dStdCost": "d", "cCurrency": "s", "dPrice1": "d", "dPrice2": "d", "dPrice3": "d",
    "dPrice4": "d", "dPrice5": "d", "dMinPrice": "d",
    # taxes
    "cSalesTaxGroup": "s", "cPurchaseTaxGroup": "s", "dEcoFee": "d", "cEcoFeeCode": "s",
    # accounting
    "cGLSales": "s", "cGLPurchase": "s", "cGLInventory": "s", "cGLCOGS": "s", "cCostCenter": "s", "cProject": "s",
    # inventory
    "lStocked": "b", "lLotControl": "b", "lSerialControl": "b", "lExpiryControl": "b", "iShelfLifeDays": "i",
    "cDefaultWarehouse": "s", "cABCClass": ("", "A", "B", "C"),
    # sales and logistics
    "lSellable": "b", "lPurchasable": "b", "lPORequired": "b", "iWarrantyMonths": "i", "cCountryOrigin": "s",
    "cHSCode": "s", "cFreightClass": "s", "lHazardous": "b", "cNotes": "s",
}
PRODUCT_SUPPLIER = {"cSupplierCode": "s", "cSupplierItem": "s", "dPurchasePrice": "d", "cCurrency": "s",
                    "iLeadTimeDays": "i", "dMinOrderQty": "d", "lPreferred": "b"}
WAREHOUSE = {"cCode": "s", "cNameFR": "s", "cNameEN": "s", "cType": WAREHOUSE_TYPES, "cAddress1": "s", "cCity": "s",
             "cProvince": "s", "cZipCode": "s", "cCountry": "s", "cManager": "s", "cPhone": "s", "cEmail": "s",
             "lUseLocations": "b", "lAllowNegative": "b", "cReceivingLoc": "s", "cShippingLoc": "s", "lActive": "b"}
LOCATION = {"cWarehouse": "s", "cCode": "s", "cZone": "s", "cAisle": "s", "cRack": "s", "cLevel": "s", "cBin": "s",
            "cDescription": "s", "cType": LOCATION_TYPES, "dMaxWeight": "d", "dMaxVolume": "d", "iMaxPallets": "i",
            "lMixProducts": "b", "lMixLots": "b", "lBlocked": "b", "iPickSeq": "i", "lActive": "b"}
STOCK_PARAM = {"cProduct": "s", "cWarehouse": "s", "dReorderPoint": "d", "dMinQty": "d", "dMaxQty": "d",
               "dOrderQty": "d", "cDefaultLocation": "s", "iLeadTimeDays": "i", "lActive": "b"}
MOVEMENT = {"dDate": "date", "cType": MOVE_TYPES, "cProduct": "s", "dQty": "d", "dUnitCost": "d",
            "cWarehouse": "s", "cLocation": "s", "cWhTo": "s", "cLocTo": "s", "cLot": "s", "cSerial": "s",
            "dExpiry": "date", "cDocType": DOC_TYPES, "cDocNo": "s", "cReason": "s", "cComment": "s"}
COUNT = {"cWarehouse": "s", "dDate": "date", "cDescription": "s", "cLocationPrefix": "s", "cProductPrefix": "s"}
COUNT_LINE = {"cProduct": "s", "cLocation": "s", "cLot": "s", "cSerial": "s", "dQtyExpected": "d", "dQtyCounted": "d"}

DEFAULTS = {
    "tax_codes": {"cKind": "other", "dRecoverablePct": "100", "lActive": True},
    "tax_groups": {"cTreatment": "taxable", "lActive": True},
    "uom": {"cType": "count", "lActive": True},
    "categories": {"lActive": True},
    "products": {"cStatus": "active", "cType": "stock", "cCostMethod": "avg", "cCurrency": "CAD", "cStockUOM": "UN",
                 "cPurchaseUOM": "UN", "dPurchaseFactor": "1", "cSalesUOM": "UN", "dSalesFactor": "1",
                 "lStocked": True, "lSellable": True,
                 "lPurchasable": True, "cWeightUOM": "kg", "cDimUOM": "cm", "cCountryOrigin": "CA"},
    "warehouses": {"cType": "main", "cProvince": "QC", "cCountry": "CA", "lUseLocations": True, "lActive": True},
    "locations": {"cType": "picking", "lMixProducts": True, "lMixLots": True, "lActive": True},
    "stock_params": {"lActive": True},
}
