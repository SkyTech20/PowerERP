"""PowerWARE XML: the documents SkyAI reads (dsGLCC, dsSupplier, dsPO, dsPOdetail, dsReceiving...) and the
dsInput / dsOutput of the invoice services. Same formats as the real PowerWARE web services and the SkyAI mock API
(copied from mock-apis/skyai-api/app.py so both answer exactly the same way)."""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from xml.sax.saxutils import escape

from flask import Response


def xml_escape(s):
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
        c_code = xml_escape(item.get("cCode", ""))
        c_desc = xml_escape(item.get("cDesc", ""))
        xml_content += f"""    <ttGL>
        <cCode>{c_code}</cCode>
        <cDesc>{c_desc}</cDesc>
    </ttGL>
"""
    for item in ttcc_list:
        c1 = xml_escape(item.get("cCC1", ""))
        c2 = xml_escape(item.get("cCC2", ""))
        desc = xml_escape(item.get("cDesc", ""))
        c2_tag = f"<cCC2>{c2}</cCC2>" if c2 else "<cCC2/>"
        xml_content += f"""    <ttCC>
        <cCC1>{c1}</cCC1>
        {c2_tag}
        <cDesc>{desc}</cDesc>
    </ttCC>
"""
    xml_content += "</dsGLCC>"
    return Response(xml_content, mimetype="application/xml; charset=utf-8")


def create_supplier_xml_response(data):
    """Créer une réponse XML dsPO/ttSupplier alignée à la prod (incl. cDeptSauv)."""
    xml_content = """<?xml version="1.0"?>
<dsPO xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
"""

    for supplier in data:
        c_code = xml_escape(supplier.get("cCode", ""))
        c_name = xml_escape(supplier.get("cName", ""))
        c_term_code = xml_escape(supplier.get("cTermCode", ""))
        c_term_desc = xml_escape(supplier.get("cTermDesc", ""))
        c_address1 = xml_escape(supplier.get("cAddress1", ""))
        c_address2 = xml_escape(supplier.get("cAddress2", ""))
        c_city = xml_escape(supplier.get("cCity", ""))
        c_province = xml_escape(supplier.get("cProvince", ""))
        c_country = xml_escape(supplier.get("cCountry", ""))
        c_zip_code = xml_escape(supplier.get("cZipCode", ""))
        c_no_tps = xml_escape(supplier.get("cNoTPS", ""))
        c_no_tvq = xml_escape(supplier.get("cNoTVQ", ""))
        c_code_ach = xml_escape(supplier.get("cCodeAch", ""))
        c_desc_ach = xml_escape(supplier.get("cDescAch", ""))
        c_dept_sauv = xml_escape(supplier.get("cDeptSauv", ""))
        i_type_po = supplier.get("iTypePO", 0)
        i_statut_ach = supplier.get("iStatutAch", 0)
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

    return Response(xml_content, mimetype="application/xml; charset=utf-8")


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
    rough_string = ET.tostring(root, encoding="unicode")
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
    "cSupplierCode",
    "cSupplierName",
    "cBuyerCode",
    "cBuyerName",
    "cApplicantCode",
    "dOrderDate",
    "dSubTotal",
    "dFreight",
    "dGST",
    "dPST",
    "dTotalAmount",
)
_PO_DETAIL_KEYS = (
    "cUnique",
    "cProductcode",
    "cProductDesc",
    "dQuantity",
    "dUnitCost",
    "dSubTotal",
    "dFreight",
    "dGST",
    "dPST",
    "dTotalAmount",
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
        val = xml_escape(str(h.get(key, "") or ""))
        lines.append(f"        <{key}>{val}</{key}>")
    lines.append("    </ttPOheader>")
    for item in ttpodetail_list or []:
        lines.append("    <ttPOdetail>")
        for key in _PO_DETAIL_KEYS:
            val = xml_escape(str(item.get(key, "") or ""))
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
                    element_name = key[:-1] if key.endswith("s") else key
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
    rough_string = ET.tostring(root, encoding="unicode")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding=None)


def create_xml_response(data):
    """Créer une réponse XML avec les en-têtes appropriés"""
    xml_content = dict_to_xml(data)
    return Response(xml_content, mimetype="application/xml; charset=utf-8")


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
        c_po = xml_escape(rec.get("NoBonCommande", ""))
        d_receiving_date = xml_escape(rec.get("DateReception", ""))
        xml_content += f"""    <ttReceiving>
        <iReceiving>{i_receiving}</iReceiving>
        <cPO>{c_po}</cPO>
        <dReceivingDate>{d_receiving_date}</dReceivingDate>
    </ttReceiving>
"""
    xml_content += "</dsReceiving>"
    return Response(xml_content, mimetype="application/xml; charset=utf-8")


def create_receiving_details_xml_response(reception):
    """Build XML response in Powerware dsReceiving format: optional ttRcvHeader + ttRcvDetail rows."""
    xml_content = (
        """<?xml version="1.0"?>
<dsReceiving xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
"""
        + RECEIVING_DETAILS_XSD_SCHEMA
        + "\n"
    )
    try:
        i_receiving = int(reception.get("NoReception") or 0)
    except (TypeError, ValueError):
        i_receiving = 0

    # Emit header when a canonical total is present (matches real PowerWARE feed).
    montant_total = reception.get("MontantTotal")
    if montant_total is not None and str(montant_total).strip() != "":
        c_po = xml_escape(reception.get("NoBonCommande", "") or "")
        d_date = xml_escape(reception.get("DateReception", "") or "")
        d_sub = xml_escape(str(reception.get("SousTotal") or ""))
        d_freight = xml_escape(str(reception.get("Transport") or "0.00"))
        d_gst = xml_escape(str(reception.get("TPS") or ""))
        d_pst = xml_escape(str(reception.get("TVQ") or ""))
        d_total = xml_escape(str(montant_total))
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
        c_product_code = xml_escape(article.get("CodeArticle", ""))
        c_description = xml_escape(article.get("Description", ""))
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
        c_gl = xml_escape(article.get("cGL", "") or article.get("CodeGL", "") or "")
        c_cc1 = xml_escape(article.get("cCC1", "") or article.get("CC1", "") or "")
        c_cc2 = xml_escape(article.get("cCC2", "") or article.get("CC2", "") or "")
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
        <dUnitCost>{xml_escape(str(d_unit_cost))}</dUnitCost>
        <dSubTotal>{xml_escape(str(d_sub_total))}</dSubTotal>
        <dFreight>{xml_escape(str(d_freight))}</dFreight>
        <dGST>{xml_escape(str(d_gst))}</dGST>
        <dPST>{xml_escape(str(d_pst))}</dPST>
        <dTotalAmount>{d_total_amount}</dTotalAmount>
        <cGL>{c_gl}</cGL>
        <cCC1>{c_cc1}</cCC1>
        <cCC2>{c_cc2}</cCC2>
    </ttRcvDetail>
"""
    xml_content += "</dsReceiving>"
    return Response(xml_content, mimetype="application/xml; charset=utf-8")


def invoice_error_response(c_no_fourn, c_no_facture, d_date_facture, c_erreur):
    """Build dsOutput XML with ttError (Powerware format)."""
    xml = f"""<?xml version="1.0"?>
<dsOutput xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ttError>
        <cNoFourn>{xml_escape(c_no_fourn)}</cNoFourn>
        <cNoFacture>{xml_escape(c_no_facture)}</cNoFacture>
        <dDateFacture>{xml_escape(d_date_facture)}</dDateFacture>
        <cErreur>{xml_escape(c_erreur)}</cErreur>
    </ttError>
</dsOutput>"""
    return Response(xml, mimetype="application/xml; charset=utf-8"), 200


def invoice_success_response(c_no_fourn, c_no_facture, d_date_facture):
    """Build dsOutput XML with ttInvoice (Powerware format)."""
    xml = f"""<?xml version="1.0"?>
<dsOutput xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <ttInvoice>
        <cNoFourn>{xml_escape(c_no_fourn)}</cNoFourn>
        <cNoFacture>{xml_escape(c_no_facture)}</cNoFacture>
        <dDateFacture>{xml_escape(d_date_facture)}</dDateFacture>
    </ttInvoice>
</dsOutput>"""
    return Response(xml, mimetype="application/xml; charset=utf-8"), 200


def _local(elem):
    return (elem.tag or "").split("}")[-1]


def parse_dsinput(body):
    """Parse a dsInput XML body into (header dict, list of line dicts)."""
    root = ET.fromstring(body)
    hd = next((e for e in root.iter() if _local(e) == "ttInputHD"), None)
    if hd is None:
        raise ValueError("ttInputHD manquant")
    header = {_local(c): (c.text or "").strip() for c in hd}
    lines = [{_local(c): (c.text or "").strip() for c in dt} for dt in root.iter() if _local(dt) == "ttInputDT"]
    return header, lines
