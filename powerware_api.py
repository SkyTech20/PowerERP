"""
PowerWARE / SkyAI-compatible endpoints served by PowerERP.

Same paths, parameters and XML formats as the real PowerWARE web services
(and the SkyAI mock API), but backed by PowerERP's own data. Point the
SkyAI "APIs" configuration at this server (e.g. http://erp-sample:5050) and
SkyAI reads suppliers, GL accounts, POs and receptions from the ERP, and
creates its invoices in the ERP (apInvoiceNoPO.p / apInvoiceWithPO.p).

The XML builders and read endpoints below are copied from
mock-apis/skyai-api/app.py so both servers answer exactly the same way.
"""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom
from xml.sax.saxutils import escape

from flask import Blueprint, Response, jsonify, request

logger = logging.getLogger(__name__)

bp = Blueprint("powerware", __name__)

PW_PREFIX = "/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI"

# Shared data lists, bound by register_powerware() to the ERP's in-memory data.
receiving_details = []
unbilled_po = []
unbilled_receiving = []
gl_ttGL_data = []
gl_ttCC_data = []
po_details = []
supplier_terms_data = []
_invoice_hooks = {}


def _xml_escape(s):
    """Escape &, <, > so XML is well-formed (e.g. 'Santé & Sécurité' -> 'Santé &amp; Sécurité', 'R&D' -> 'R&amp;D')."""
    if s is None:
        return ""
    return escape(str(s))  # xml.sax.saxutils.escape handles &, <, >

def create_gl_xml_response(ttgl_list, ttcc_list):
    """Create XML response with Powerware dsGLCC structure: ttGL first, then ttCC."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<dsGLCC xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
"""
    for item in ttgl_list:
        c_code = _xml_escape(item.get("cCode", ""))
        c_desc = _xml_escape(item.get("cDesc", ""))
        xml_content += f"""    <ttGL>
        <cCode>{c_code}</cCode>
        <cDesc>{c_desc}</cDesc>
    </ttGL>
"""
    for item in ttcc_list:
        c1 = _xml_escape(item.get("cCC1", ""))
        c2 = _xml_escape(item.get("cCC2", ""))
        desc = _xml_escape(item.get("cDesc", ""))
        c2_tag = f"<cCC2>{c2}</cCC2>" if c2 else "<cCC2/>"
        xml_content += f"""    <ttCC>
        <cCC1>{c1}</cCC1>
        {c2_tag}
        <cDesc>{desc}</cDesc>
    </ttCC>
"""
    xml_content += "</dsGLCC>"
    return Response(xml_content, mimetype='application/xml; charset=utf-8')

def create_supplier_xml_response(data):
    """Créer une réponse XML dsPO/ttSupplier alignée à la prod (incl. cDeptSauv)."""
    xml_content = """<?xml version="1.0"?>
<dsPO xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
"""

    for supplier in data:
        c_code = _xml_escape(supplier.get('cCode', ''))
        c_name = _xml_escape(supplier.get('cName', ''))
        c_term_code = _xml_escape(supplier.get('cTermCode', ''))
        c_term_desc = _xml_escape(supplier.get('cTermDesc', ''))
        c_address1 = _xml_escape(supplier.get('cAddress1', ''))
        c_address2 = _xml_escape(supplier.get('cAddress2', ''))
        c_city = _xml_escape(supplier.get('cCity', ''))
        c_province = _xml_escape(supplier.get('cProvince', ''))
        c_country = _xml_escape(supplier.get('cCountry', ''))
        c_zip_code = _xml_escape(supplier.get('cZipCode', ''))
        c_no_tps = _xml_escape(supplier.get('cNoTPS', ''))
        c_no_tvq = _xml_escape(supplier.get('cNoTVQ', ''))
        c_code_ach = _xml_escape(supplier.get('cCodeAch', ''))
        c_desc_ach = _xml_escape(supplier.get('cDescAch', ''))
        c_dept_sauv = _xml_escape(supplier.get('cDeptSauv', ''))
        i_type_po = supplier.get('iTypePO', 0)
        i_statut_ach = supplier.get('iStatutAch', 0)
        xml_content += f"""    <ttSupplier>
        <cCode>{c_code}</cCode>
        <cName>{c_name}</cName>
        <cTermCode>{c_term_code}</cTermCode>
        <cTermDesc>{c_term_desc}</cTermDesc>
        <cAddress1>{c_address1}</cAddress1>
        <cAddress2>{c_address2}</cAddress2>
        <cCity>{c_city}</cCity>
        <cProvince>{c_province}</cProvince>
        <cCountry>{c_country}</cCountry>
        <cZipCode>{c_zip_code}</cZipCode>
        <cNoTPS>{c_no_tps}</cNoTPS>
        <cNoTVQ>{c_no_tvq}</cNoTVQ>
        <cCodeAch>{c_code_ach}</cCodeAch>
        <cDescAch>{c_desc_ach}</cDescAch>
        <cDeptSauv>{c_dept_sauv}</cDeptSauv>
        <iTypePO>{i_type_po}</iTypePO>
        <iStatutAch>{i_statut_ach}</iStatutAch>
    </ttSupplier>
"""

    xml_content += "</dsPO>"

    return Response(xml_content, mimetype='application/xml; charset=utf-8')


def build_dspo_xml(ttpo_list):
    """Build dsPO XML: ttPO with cPO, dCreationDate, cSupplierName, cSupplierCode, lBlanketOrder."""
    root = ET.Element("dsPO")
    for item in ttpo_list:
        ttpo = ET.SubElement(root, "ttPO")
        for key in ("cPO", "dCreationDate", "cSupplierName", "cSupplierCode"):
            elem = ET.SubElement(ttpo, key)
            elem.text = str(item.get(key, "") or "")
        blanket = item.get("lBlanketOrder", False)
        blanket_elem = ET.SubElement(ttpo, "lBlanketOrder")
        blanket_elem.text = "true" if blanket in (True, "true", "True", 1, "1") else "false"
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding=None)


# Embedded XSD (Progress / PowerWare prodata) — matches production getPODetails.p
PO_DETAILS_XSD_SCHEMA = """    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="" xmlns:prodata="urn:schemas-progress-com:xml-prodata:0001">
        <xsd:element name="dsPOdetail" prodata:proDataSet="true">
            <xsd:complexType>
                <xsd:sequence>
                    <xsd:element name="ttPOheader" minOccurs="0" maxOccurs="unbounded">
                        <xsd:complexType>
                            <xsd:sequence>
                                <xsd:element name="cSupplierCode" type="xsd:string" nillable="true"/>
                                <xsd:element name="cSupplierName" type="xsd:string" nillable="true"/>
                                <xsd:element name="cBuyerCode" type="xsd:string" nillable="true"/>
                                <xsd:element name="cBuyerName" type="xsd:string" nillable="true"/>
                                <xsd:element name="cApplicantCode" type="xsd:string" nillable="true"/>
                                <xsd:element name="dOrderDate" type="xsd:date" nillable="true"/>
                                <xsd:element name="dSubTotal" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dFreight" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dGST" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dPST" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dTotalAmount" type="xsd:decimal" nillable="true"/>
                            </xsd:sequence>
                        </xsd:complexType>
                    </xsd:element>
                    <xsd:element name="ttPOdetail" minOccurs="0" maxOccurs="unbounded">
                        <xsd:complexType>
                            <xsd:sequence>
                                <xsd:element name="cUnique" type="xsd:string" nillable="true"/>
                                <xsd:element name="cProductcode" type="xsd:string" nillable="true"/>
                                <xsd:element name="cProductDesc" type="xsd:string" nillable="true"/>
                                <xsd:element name="dQuantity" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dUnitCost" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dSubTotal" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dFreight" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dGST" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dPST" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dTotalAmount" type="xsd:decimal" nillable="true"/>
                            </xsd:sequence>
                        </xsd:complexType>
                    </xsd:element>
                </xsd:sequence>
            </xsd:complexType>
            <xsd:unique name="ttPOdetail" prodata:primaryIndex="true">
                <xsd:selector xpath=".//ttPOdetail"/>
                <xsd:field xpath="cUnique"/>
            </xsd:unique>
        </xsd:element>
    </xsd:schema>
"""

_PO_HEADER_KEYS = (
    "cSupplierCode", "cSupplierName", "cBuyerCode", "cBuyerName", "cApplicantCode",
    "dOrderDate", "dSubTotal", "dFreight", "dGST", "dPST", "dTotalAmount",
)
_PO_DETAIL_KEYS = (
    "cUnique", "cProductcode", "cProductDesc", "dQuantity", "dUnitCost",
    "dSubTotal", "dFreight", "dGST", "dPST", "dTotalAmount",
)


def build_dspodetail_xml(ttpoheader, ttpodetail_list):
    """Build dsPOdetail XML (real format): xsd:schema + ttPOheader + ttPOdetail rows."""
    h = ttpoheader or {}
    lines = [
        '<?xml version="1.0"?>',
        '<dsPOdetail xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
        PO_DETAILS_XSD_SCHEMA.rstrip(),
        "    <ttPOheader>",
    ]
    for key in _PO_HEADER_KEYS:
        val = _xml_escape(str(h.get(key, "") or ""))
        lines.append(f"        <{key}>{val}</{key}>")
    lines.append("    </ttPOheader>")
    for item in ttpodetail_list or []:
        lines.append("    <ttPOdetail>")
        for key in _PO_DETAIL_KEYS:
            val = _xml_escape(str(item.get(key, "") or ""))
            lines.append(f"        <{key}>{val}</{key}>")
        lines.append("    </ttPOdetail>")
    lines.append("</dsPOdetail>")
    return "\n".join(lines) + "\n"


def dict_to_xml(data, root_name="response"):
    """Convertir un dictionnaire ou une liste en XML formaté"""
    root = ET.Element(root_name)
    
    def add_element(parent, key, value):
        if isinstance(value, dict):
            element = ET.SubElement(parent, key)
            for k, v in value.items():
                add_element(element, k, v)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    # Pour les listes d'objets, créer un élément avec un nom singulier
                    element_name = key[:-1] if key.endswith('s') else key
                    element = ET.SubElement(parent, element_name)
                    for k, v in item.items():
                        add_element(element, k, v)
                else:
                    element = ET.SubElement(parent, key)
                    element.text = str(item)
        else:
            element = ET.SubElement(parent, key)
            element.text = str(value) if value is not None else ""
    
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                item_element = ET.SubElement(root, "item")
                for key, value in item.items():
                    add_element(item_element, key, value)
    elif isinstance(data, dict):
        for key, value in data.items():
            add_element(root, key, value)
    
    # Formatage XML
    rough_string = ET.tostring(root, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding=None)

def create_xml_response(data):
    """Créer une réponse XML avec les en-têtes appropriés"""
    xml_content = dict_to_xml(data)
    return Response(xml_content, mimetype='application/xml; charset=utf-8')


# Embedded XSD (Progress / PowerWare prodata) — matches production getReceivingDetails.p
RECEIVING_DETAILS_XSD_SCHEMA = """    <xsd:schema xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns="" xmlns:prodata="urn:schemas-progress-com:xml-prodata:0001">
        <xsd:element name="dsReceiving" prodata:proDataSet="true">
            <xsd:complexType>
                <xsd:sequence>
                    <xsd:element name="ttRcvHeader" minOccurs="0" maxOccurs="1">
                        <xsd:complexType>
                            <xsd:sequence>
                                <xsd:element name="iReceiving" type="xsd:int" nillable="true"/>
                                <xsd:element name="cPO" type="xsd:string" nillable="true"/>
                                <xsd:element name="dReceivingDate" type="xsd:date" nillable="true"/>
                                <xsd:element name="dSubTotal" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dFreight" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dGST" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dPST" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dTotalAmount" type="xsd:decimal" nillable="true"/>
                            </xsd:sequence>
                        </xsd:complexType>
                    </xsd:element>
                    <xsd:element name="ttRcvDetail" minOccurs="0" maxOccurs="unbounded">
                        <xsd:complexType>
                            <xsd:sequence>
                                <xsd:element name="iReceiving" type="xsd:int" nillable="true"/>
                                <xsd:element name="cProductCode" type="xsd:string" nillable="true"/>
                                <xsd:element name="cDescription" type="xsd:string" nillable="true"/>
                                <xsd:element name="dQtyReceived" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dUnitCost" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dSubTotal" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dFreight" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dGST" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dPST" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="dTotalAmount" type="xsd:decimal" nillable="true"/>
                                <xsd:element name="cGL" type="xsd:string" nillable="true"/>
                                <xsd:element name="cCC1" type="xsd:string" nillable="true"/>
                                <xsd:element name="cCC2" type="xsd:string" nillable="true"/>
                            </xsd:sequence>
                        </xsd:complexType>
                    </xsd:element>
                </xsd:sequence>
            </xsd:complexType>
        </xsd:element>
    </xsd:schema>
"""


def create_dsreceiving_xml_response(receiving_list):
    """Build XML response in Powerware dsReceiving format: root dsReceiving, each item ttReceiving with iReceiving, cPO, dReceivingDate only."""
    xml_content = """<?xml version="1.0"?>
<dsReceiving xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
"""
    for rec in receiving_list:
        try:
            i_receiving = int(rec.get("NoReception") or 0)
        except (TypeError, ValueError):
            i_receiving = 0
        c_po = _xml_escape(rec.get("NoBonCommande", ""))
        d_receiving_date = _xml_escape(rec.get("DateReception", ""))
        xml_content += f"""    <ttReceiving>
        <iReceiving>{i_receiving}</iReceiving>
        <cPO>{c_po}</cPO>
        <dReceivingDate>{d_receiving_date}</dReceivingDate>
    </ttReceiving>
"""
    xml_content += "</dsReceiving>"
    return Response(xml_content, mimetype='application/xml; charset=utf-8')


def create_receiving_details_xml_response(reception):
    """Build XML response in Powerware dsReceiving format: optional ttRcvHeader + ttRcvDetail rows."""
    xml_content = """<?xml version="1.0"?>
<dsReceiving xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
""" + RECEIVING_DETAILS_XSD_SCHEMA + "\n"
    try:
        i_receiving = int(reception.get("NoReception") or 0)
    except (TypeError, ValueError):
        i_receiving = 0

    # Emit header when a canonical total is present (matches real PowerWARE feed).
    montant_total = reception.get("MontantTotal")
    if montant_total is not None and str(montant_total).strip() != "":
        c_po = _xml_escape(reception.get("NoBonCommande", "") or "")
        d_date = _xml_escape(reception.get("DateReception", "") or "")
        d_sub = _xml_escape(str(reception.get("SousTotal") or ""))
        d_freight = _xml_escape(str(reception.get("Transport") or "0.00"))
        d_gst = _xml_escape(str(reception.get("TPS") or ""))
        d_pst = _xml_escape(str(reception.get("TVQ") or ""))
        d_total = _xml_escape(str(montant_total))
        xml_content += f"""    <ttRcvHeader>
        <iReceiving>{i_receiving}</iReceiving>
        <cPO>{c_po}</cPO>
        <dReceivingDate>{d_date}</dReceivingDate>
        <dSubTotal>{d_sub}</dSubTotal>
        <dFreight>{d_freight}</dFreight>
        <dGST>{d_gst}</dGST>
        <dPST>{d_pst}</dPST>
        <dTotalAmount>{d_total}</dTotalAmount>
    </ttRcvHeader>
"""

    for article in reception.get("Articles", []):
        c_product_code = _xml_escape(article.get("CodeArticle", ""))
        c_description = _xml_escape(article.get("Description", ""))
        try:
            d_qty_received = float(article.get("QuantiteRecue") or 0)
        except (TypeError, ValueError):
            d_qty_received = 0.0
        try:
            qty = float(article.get("QuantiteRecue") or 0)
            unit = float(article.get("PrixUnitaire") or article.get("dUnitCost") or 0)
            if article.get("dTotalAmount") is not None and str(article.get("dTotalAmount")).strip() != "":
                d_total_amount = round(float(article.get("dTotalAmount")), 2)
            else:
                d_total_amount = round(qty * unit, 2)
        except (TypeError, ValueError):
            d_total_amount = 0.0
        c_gl = _xml_escape(article.get("cGL", "") or article.get("CodeGL", "") or "")
        c_cc1 = _xml_escape(article.get("cCC1", "") or article.get("CC1", "") or "")
        c_cc2 = _xml_escape(article.get("cCC2", "") or article.get("CC2", "") or "")
        d_unit_cost = article.get("dUnitCost") or article.get("PrixUnitaire") or ""
        d_sub_total = article.get("dSubTotal") or ""
        d_freight = article.get("dFreight") or ""
        d_gst = article.get("dGST") or ""
        d_pst = article.get("dPST") or ""

        xml_content += f"""    <ttRcvDetail>
        <iReceiving>{i_receiving}</iReceiving>
        <cProductCode>{c_product_code}</cProductCode>
        <cDescription>{c_description}</cDescription>
        <dQtyReceived>{d_qty_received}</dQtyReceived>
        <dUnitCost>{_xml_escape(str(d_unit_cost))}</dUnitCost>
        <dSubTotal>{_xml_escape(str(d_sub_total))}</dSubTotal>
        <dFreight>{_xml_escape(str(d_freight))}</dFreight>
        <dGST>{_xml_escape(str(d_gst))}</dGST>
        <dPST>{_xml_escape(str(d_pst))}</dPST>
        <dTotalAmount>{d_total_amount}</dTotalAmount>
        <cGL>{c_gl}</cGL>
        <cCC1>{c_cc1}</cCC1>
        <cCC2>{c_cc2}</cCC2>
    </ttRcvDetail>
"""
    xml_content += "</dsReceiving>"
    return Response(xml_content, mimetype='application/xml; charset=utf-8')



# API 1: Détails de réception
@bp.route('/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI/getReceivingDetails.p', methods=['GET'])
def get_receiving_details():
    """Récupérer les détails d'une réception spécifique"""
    try:
        company = request.args.get('COMPANY', '')
        no_reception = request.args.get('NoReception', '')
        
        if not company:
            return jsonify({"error": "Paramètre COMPANY requis"}), 400
        
        if not no_reception:
            return jsonify({"error": "Paramètre NoReception requis"}), 400
        
        # Rechercher la réception
        reception = next((r for r in receiving_details 
                         if r['NoReception'] == no_reception and r['COMPANY'] == company), None)
        
        if not reception:
            return jsonify({"error": f"Réception {no_reception} non trouvée pour la compagnie {company}"}), 404
        
        return create_receiving_details_xml_response(reception)
    except Exception as e:
        return jsonify({"error": "Erreur lors de la récupération des détails de réception"}), 500

# API 2: Bons de commande non facturés (format réel dsPO / ttPO)
@bp.route('/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI/getUnbilledPO.p', methods=['GET'])
def get_unbilled_po():
    """Unbilled POs (XML dsPO / ttPO). Optional Supplier filters by cSupplierCode. Empty list = 200 empty dsPO."""
    try:
        company = request.args.get('COMPANY', '')
        
        if not company:
            return jsonify({"error": "Paramètre COMPANY requis"}), 400
        
        filtered_po = [po for po in unbilled_po if po.get('COMPANY') == company]
        supplier = (request.args.get('Supplier') or '').strip()
        if supplier:
            supplier_upper = supplier.upper()
            filtered_po = [
                po for po in filtered_po
                if (po.get('cSupplierCode') or '').strip().upper() == supplier_upper
            ]
        
        xml_content = build_dspo_xml(filtered_po)
        return Response(xml_content, mimetype='application/xml; charset=utf-8')
    except Exception as e:
        return jsonify({"error": "Erreur lors de la récupération des bons de commande non facturés"}), 500

# API 3: Réceptions non facturées
@bp.route('/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI/getUnbilledReceiving.p', methods=['GET'])
def get_unbilled_receiving():
    """Récupérer toutes les réceptions non facturées"""
    try:
        company = request.args.get('COMPANY', '')
        
        if not company:
            return jsonify({"error": "Paramètre COMPANY requis"}), 400
        
        # Filtrer par compagnie
        filtered_receiving = [r for r in unbilled_receiving if r['COMPANY'] == company]
        
        if not filtered_receiving:
            return jsonify({"error": f"Aucune réception non facturée trouvée pour la compagnie {company}"}), 404
        
        return create_dsreceiving_xml_response(filtered_receiving)
    except Exception as e:
        return jsonify({"error": "Erreur lors de la récupération des réceptions non facturées"}), 500

# API 4: Comptes GL (General Ledger) - JSON source, convert to dsGLCC XML or JSON conforme solicitado
@bp.route('/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI/getGLaccounts.p', methods=['GET'])
def get_gl_accounts():
    """Récupérer GL accounts et cost centers. Accept: application/json ou format=json → JSON. Sinon → XML dsGLCC."""
    try:
        company = request.args.get('COMPANY', '')
        cc1_filter = request.args.get('CC1', '')
        wants_json = (
            request.args.get('format', '').lower() == 'json'
            or 'application/json' in (request.headers.get('Accept') or '')
        )

        if not company:
            return jsonify({"error": "Paramètre COMPANY requis"}), 400

        filtered_ttcc = gl_ttCC_data
        if cc1_filter:
            filtered_ttcc = [acc for acc in gl_ttCC_data if acc.get('cCC1') == cc1_filter]

        if not gl_ttGL_data and not filtered_ttcc:
            return jsonify({"error": "Aucun compte GL trouvé"}), 404

        if wants_json:
            return jsonify({"gl_accounts": gl_ttGL_data, "cost_centers": filtered_ttcc})
        return create_gl_xml_response(gl_ttGL_data, filtered_ttcc)
    except Exception as e:
        return jsonify({"error": "Erreur lors de la récupération des comptes GL"}), 500

# API 5: Détails de bon de commande (format réel dsPOdetail / ttPOheader / ttPOdetail)
@bp.route('/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI/getPODetails.p', methods=['GET'])
def get_po_details():
    """Récupérer les détails complets d'un bon de commande (XML dsPOdetail avec ttPOheader et ttPOdetail)."""
    try:
        company = request.args.get('COMPANY', '')
        po_number = request.args.get('PO', '')
        
        if not company:
            return jsonify({"error": "Paramètre COMPANY requis"}), 400
        
        if not po_number:
            return jsonify({"error": "Paramètre PO requis"}), 400
        
        po_detail = next((po for po in po_details if po.get('cPO') == po_number and po.get('COMPANY') == company), None)
        
        if not po_detail:
            return jsonify({"error": f"Bon de commande {po_number} non trouvé pour la compagnie {company}"}), 404
        
        xml_content = build_dspodetail_xml(
            po_detail.get("ttPOheader", {}),
            po_detail.get("ttPOdetail", [])
        )
        return Response(xml_content, mimetype='application/xml; charset=utf-8')
    except Exception as e:
        return jsonify({"error": "Erreur lors de la récupération des détails du bon de commande"}), 500

# API 6: Termes des fournisseurs (NOUVELLE API)
@bp.route('/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI/getSupplierTerm.p', methods=['GET'])
def get_supplier_term():
    """Récupérer les informations et termes de paiement des fournisseurs"""
    try:
        company = request.args.get('COMPANY', '')
        supplier_code = request.args.get('SupplierCode', '')
        term_filter = request.args.get('TermCode', '')
        
        if not company:
            return jsonify({"error": "Paramètre COMPANY requis"}), 400
        
        # Filtrer les fournisseurs
        filtered_suppliers = supplier_terms_data
        
        # Filtrer par code fournisseur si spécifié
        if supplier_code:
            filtered_suppliers = [s for s in filtered_suppliers 
                                if s['cCode'].upper() == supplier_code.upper()]
        
        # Filtrer par code de terme si spécifié
        if term_filter:
            filtered_suppliers = [s for s in filtered_suppliers 
                                if s['cTermCode'].upper() == term_filter.upper()]
        
        if not filtered_suppliers:
            error_msg = "Aucun fournisseur trouvé"
            if supplier_code:
                error_msg += f" avec le code {supplier_code}"
            if term_filter:
                error_msg += f" avec le terme {term_filter}"
            return jsonify({"error": error_msg}), 404
        
        return create_supplier_xml_response(filtered_suppliers)
    except Exception as e:
        return jsonify({"error": "Erreur lors de la récupération des termes fournisseurs"}), 500

# API de statistiques pour le système
@bp.route('/cgi-bin/cgiip.exe/WService=wsbroker1/wm/custom/vol100/SkyAI/getStats.p', methods=['GET'])
def get_skyai_stats():
    """Récupérer les statistiques du système SkyAI"""
    try:
        company = request.args.get('COMPANY', 'MA2')
        
        # Calculer les statistiques (format unbilled_po: cPO, dCreationDate, cSupplierName; pas de MontantEnAttente)
        total_unbilled_po = len([po for po in unbilled_po if po.get('COMPANY') == company])
        total_unbilled_receiving = len([r for r in unbilled_receiving if r['COMPANY'] == company])
        total_amount_pending = 0.0
        total_suppliers = len(supplier_terms_data)
        
        stats = {
            "COMPANY": company,
            "DateGenerationStats": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "TotalBonesCommandeNonFactures": total_unbilled_po,
            "TotalReceptionsNonFacturees": total_unbilled_receiving,
            "MontantTotalEnAttente": f"{total_amount_pending:.2f}",
            "TotalFournisseurs": total_suppliers,
            "Devise": "CAD",
            "StatusSysteme": "Opérationnel",
            "DerniereMAJ": "2025-09-19 10:30:00"
        }
        
        return create_xml_response(stats)
    except Exception as e:
        return jsonify({"error": "Erreur lors du calcul des statistiques"}), 500




# ---------------------------------------------------------------------------
# Invoice creation (writes into the ERP)
# ---------------------------------------------------------------------------

def _invoice_response_error(c_no_fourn, c_no_facture, d_date_facture, c_erreur):
    """Build dsOutput XML with ttError (Powerware format)."""
    xml = f"""<?xml version="1.0"?>
<dsOutput xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ttError>
        <cNoFourn>{_xml_escape(c_no_fourn)}</cNoFourn>
        <cNoFacture>{_xml_escape(c_no_facture)}</cNoFacture>
        <dDateFacture>{_xml_escape(d_date_facture)}</dDateFacture>
        <cErreur>{_xml_escape(c_erreur)}</cErreur>
    </ttError>
</dsOutput>"""
    return Response(xml, mimetype="application/xml; charset=utf-8"), 200


def _invoice_response_success(c_no_fourn, c_no_facture, d_date_facture):
    """Build dsOutput XML with ttInvoice (Powerware format)."""
    xml = f"""<?xml version="1.0"?>
<dsOutput xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ttInvoice>
        <cNoFourn>{_xml_escape(c_no_fourn)}</cNoFourn>
        <cNoFacture>{_xml_escape(c_no_facture)}</cNoFacture>
        <dDateFacture>{_xml_escape(d_date_facture)}</dDateFacture>
    </ttInvoice>
</dsOutput>"""
    return Response(xml, mimetype="application/xml; charset=utf-8"), 200


def _local(elem):
    return (elem.tag or "").split("}")[-1]


def _parse_dsinput(body):
    """Parse a dsInput XML body into (header dict, list of line dicts)."""
    root = ET.fromstring(body)
    hd = next((e for e in root.iter() if _local(e) == "ttInputHD"), None)
    if hd is None:
        raise ValueError("ttInputHD manquant")
    header = {_local(c): (c.text or "").strip() for c in hd}
    lines = [{_local(c): (c.text or "").strip() for c in dt} for dt in root.iter() if _local(dt) == "ttInputDT"]
    return header, lines


def _create_invoice(with_po):
    today = datetime.now().strftime("%Y-%m-%d")
    body = request.get_data(as_text=True) or ""
    if not body.strip():
        return _invoice_response_error("", "", today, "Corps de la requête vide")
    try:
        header, lines = _parse_dsinput(body)
    except ET.ParseError as e:
        return _invoice_response_error("", "", today, f"XML invalide: {e}")
    except ValueError as e:
        return _invoice_response_error("", "", today, str(e))

    supplier = header.get("cNoFourn", "")
    number = header.get("cNoFacture", "")
    date = header.get("dDateFacture", "") or today
    if not supplier or not number:
        return _invoice_response_error(supplier, number, date, "Fournisseur et numéro de facture requis")

    # Same error simulation as the SkyAI mock API
    simulate = request.args.get("simulate_error", "").strip() in ("1", "true", "yes")
    if simulate or "FAIL" in number.upper() or "ERROR" in number.upper():
        return _invoice_response_error(supplier, number, date, "Facture existante")

    if _invoice_hooks["exists"](supplier, number):
        return _invoice_response_error(supplier, number, date, "Facture existante")

    try:
        _invoice_hooks["record"](header, lines, with_po)
    except Exception as e:  # keep the PowerWARE contract: errors come back as ttError
        logger.exception("PowerERP: could not create invoice")
        return _invoice_response_error(supplier, number, date, str(e))
    return _invoice_response_success(supplier, number, date)


@bp.route(PW_PREFIX + "/apInvoiceNoPO.p", methods=["POST"])
def ap_invoice_no_po():
    """Create an invoice without PO in the ERP (dsInput: ttInputHD + ttInputDT with cGL/cCC1/cCC2)."""
    return _create_invoice(with_po=False)


@bp.route(PW_PREFIX + "/apInvoiceWithPO.p", methods=["POST"])
def ap_invoice_with_po():
    """Create an invoice with PO in the ERP (dsInput: ttInputHD with cNoCommAch + ttInputDT with iNoReception)."""
    return _create_invoice(with_po=True)


def register_powerware(app, ns, invoice_exists, record_invoice):
    """Bind the endpoints to the ERP data (ns) and the ERP invoice hooks, then mount them."""
    g = globals()
    for name in ("receiving_details", "unbilled_po", "unbilled_receiving", "gl_ttGL_data", "gl_ttCC_data",
                 "po_details", "supplier_terms_data"):
        g[name] = ns[name]
    _invoice_hooks["exists"] = invoice_exists
    _invoice_hooks["record"] = record_invoice
    app.register_blueprint(bp)
