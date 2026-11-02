#!/usr/bin/env python3
"""Genera las 4 imágenes de prueba (2 pares contrato/adenda) en data/test_contracts/.

Los documentos son ficticios. Se dibujan con Pillow para que sean reproducibles; se les aplica
una rotación mínima y un fondo off-white para simular un escaneo.

Uso:  python scripts/generate_test_contracts.py     (requiere: pip install pillow)
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent.parent / "data" / "test_contracts"
W, H, MARGIN = 1240, 1754, 95  # A4 a 150 dpi

FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "C:/Windows/Fonts", "/Library/Fonts", "/System/Library/Fonts"]


def load_font(names, size):
    for d in FONT_DIRS:
        for n in names:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


BODY = load_font(["DejaVuSerif.ttf", "times.ttf", "Times New Roman.ttf"], 24)
BOLD = load_font(["DejaVuSerif-Bold.ttf", "timesbd.ttf", "Times New Roman Bold.ttf"], 24)
TITLE = load_font(["DejaVuSerif-Bold.ttf", "timesbd.ttf", "Times New Roman Bold.ttf"], 33)


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def render(filename, title, blocks, footer):
    """blocks: lista de (tipo, texto) con tipo en {'p', 'h', 'sig'}."""
    img = Image.new("RGB", (W, H), (251, 250, 247))
    d = ImageDraw.Draw(img)
    y = MARGIN
    tw = d.textlength(title, font=TITLE)
    d.text(((W - tw) / 2, y), title, font=TITLE, fill=(20, 20, 20))
    y += 40
    d.line([(MARGIN, y + 12), (W - MARGIN, y + 12)], fill=(60, 60, 60), width=2)
    y += 50
    max_w = W - 2 * MARGIN
    for kind, text in blocks:
        if kind == "h":
            y += 8
            d.text((MARGIN, y), text, font=BOLD, fill=(15, 15, 15))
            y += 36
        elif kind == "p":
            for line in wrap(d, text, BODY, max_w):
                d.text((MARGIN, y), line, font=BODY, fill=(25, 25, 25))
                y += 34
            y += 8
        elif kind == "sig":
            y += 50
            left, right = text.split("|")
            for x, label in ((MARGIN + 20, left), (W // 2 + 60, right)):
                d.line([(x, y), (x + 410, y)], fill=(40, 40, 40), width=2)
                d.text((x, y + 8), label, font=BODY, fill=(25, 25, 25))
            y += 60
    assert y < H - 90, f"{filename}: el texto no entra en la página (y={y})"
    fw = d.textlength(footer, font=BODY)
    d.text(((W - fw) / 2, H - 70), footer, font=BODY, fill=(90, 90, 90))
    img = img.rotate(0.35, resample=Image.BICUBIC, fillcolor=(251, 250, 247)).filter(ImageFilter.GaussianBlur(0.4))
    OUT.mkdir(parents=True, exist_ok=True)
    img.save(OUT / filename, "PNG")
    print("generado", filename, f"(contenido hasta y={y})")


# ------------------------------- PAR 1: contrato de servicios (cambios simples) -------------------------------
render("par1_original.png", "CONTRATO DE PRESTACIÓN DE SERVICIOS", [
    ("p", "Entre DISTRIBUIDORA LITORAL S.A. (en adelante, \"el Cliente\") y SOLUCIONES CLOUD NORTE S.R.L. "
          "(en adelante, \"el Prestador\"), se celebra el presente contrato, sujeto a las siguientes cláusulas:"),
    ("h", "PRIMERA – Objeto"),
    ("p", "El Prestador se obliga a brindar al Cliente servicios de soporte y mantenimiento de su infraestructura "
          "de servidores, con una disponibilidad mínima del 99,5% mensual."),
    ("h", "SEGUNDA – Vigencia y vencimiento"),
    ("p", "El presente contrato tendrá una vigencia de doce (12) meses a partir del 1 de marzo de 2025 y vencerá "
          "el 28 de febrero de 2026."),
    ("h", "TERCERA – Precio y forma de pago"),
    ("p", "El Cliente abonará al Prestador un monto mensual de USD 2.500 (dólares estadounidenses dos mil "
          "quinientos), pagadero entre los días 1 y 10 de cada mes mediante transferencia bancaria."),
    ("h", "CUARTA – Confidencialidad"),
    ("p", "Ambas partes se obligan a mantener en reserva toda información técnica y comercial a la que accedan "
          "con motivo del presente contrato."),
    ("h", "QUINTA – Terminación anticipada"),
    ("p", "Cualquiera de las partes podrá rescindir el contrato con un preaviso escrito de treinta (30) días."),
    ("h", "SEXTA – Jurisdicción"),
    ("p", "Para cualquier controversia las partes se someten a los tribunales ordinarios de la ciudad de Santa Fe."),
    ("p", "En prueba de conformidad, se firman dos ejemplares de un mismo tenor, en la ciudad de Santa Fe, "
          "a los 3 días del mes de febrero de 2025."),
    ("sig", "Por el Cliente|Por el Prestador"),
], "Contrato de Prestación de Servicios – Página 1 de 1")

render("par1_adenda.png", "ADENDA N° 1 AL CONTRATO DE PRESTACIÓN DE SERVICIOS", [
    ("p", "Entre DISTRIBUIDORA LITORAL S.A. (\"el Cliente\") y SOLUCIONES CLOUD NORTE S.R.L. (\"el Prestador\"), "
          "las partes acuerdan modificar el Contrato de Prestación de Servicios firmado el 3 de febrero de 2025, "
          "en los siguientes términos:"),
    ("h", "PRIMERA"),
    ("p", "Se modifica la cláusula TERCERA (Precio y forma de pago). El monto mensual pasa de USD 2.500 "
          "a USD 2.850 (dólares estadounidenses dos mil ochocientos cincuenta), a partir del 1 de marzo de 2026."),
    ("h", "SEGUNDA"),
    ("p", "Se modifica la cláusula SEGUNDA (Vigencia y vencimiento). La fecha de vencimiento del contrato "
          "pasa del 28 de febrero de 2026 al 31 de agosto de 2026."),
    ("h", "TERCERA"),
    ("p", "Las restantes cláusulas del contrato original no sufren modificación alguna y continúan en plena vigencia."),
    ("p", "Se firman dos ejemplares de un mismo tenor, en la ciudad de Santa Fe, a los 15 días del mes de enero de 2026."),
    ("sig", "Por el Cliente|Por el Prestador"),
], "Adenda N° 1 – Página 1 de 1")

# ------------------------------- PAR 2: acuerdo de confidencialidad (cambios complejos) -------------------------------
render("par2_original.png", "ACUERDO DE CONFIDENCIALIDAD", [
    ("p", "Entre INNOVATECH ARGENTINA S.A. (\"la Parte Divulgante\") y CONSULTORA ANDINA S.R.L. "
          "(\"la Parte Receptora\"), se celebra el presente acuerdo de confidencialidad:"),
    ("h", "PRIMERA – Información Confidencial"),
    ("p", "Se considera Información Confidencial toda información técnica, comercial, financiera o estratégica "
          "que la Parte Divulgante entregue a la Parte Receptora, en cualquier soporte."),
    ("h", "SEGUNDA – Obligación de reserva"),
    ("p", "La Parte Receptora mantendrá la Información Confidencial en estricta reserva y adoptará medidas de "
          "seguridad razonables para protegerla."),
    ("h", "TERCERA – Alcance territorial"),
    ("p", "La obligación de confidencialidad regirá exclusivamente en el territorio de la República Argentina."),
    ("h", "CUARTA – Restricciones de uso"),
    ("p", "La Parte Receptora se compromete a: a) utilizar la Información Confidencial únicamente para evaluar "
          "la operación comercial entre las partes; b) no realizar copias ni reproducciones, totales o parciales, "
          "sin autorización escrita de la Parte Divulgante; c) no comunicarla a terceros ajenos al acuerdo."),
    ("h", "QUINTA – Plazo"),
    ("p", "Las obligaciones de este acuerdo regirán durante tres (3) años contados desde la fecha de su firma."),
    ("h", "SEXTA – Devolución de la información"),
    ("p", "A requerimiento de la Parte Divulgante, la Parte Receptora devolverá o destruirá la Información "
          "Confidencial dentro de los diez (10) días corridos."),
    ("h", "SÉPTIMA – Jurisdicción"),
    ("p", "Las partes se someten a los tribunales ordinarios de la ciudad de Rosario, Provincia de Santa Fe."),
    ("p", "Firmado en Rosario, a los 12 días del mes de junio de 2025."),
    ("sig", "Parte Divulgante|Parte Receptora"),
], "Acuerdo de Confidencialidad – Página 1 de 1")

render("par2_adenda.png", "ADENDA N° 1 AL ACUERDO DE CONFIDENCIALIDAD", [
    ("p", "Entre INNOVATECH ARGENTINA S.A. (\"la Parte Divulgante\") y CONSULTORA ANDINA S.R.L. "
          "(\"la Parte Receptora\"), las partes acuerdan modificar el Acuerdo de Confidencialidad firmado el "
          "12 de junio de 2025, en los siguientes términos:"),
    ("h", "PRIMERA"),
    ("p", "Se modifica la cláusula TERCERA (Alcance territorial). La obligación de confidencialidad regirá en el "
          "territorio de la República Argentina, la República Oriental del Uruguay y la República de Chile."),
    ("h", "SEGUNDA"),
    ("p", "Se elimina el inciso b) de la cláusula CUARTA (Restricciones de uso), referido a la prohibición de "
          "realizar copias o reproducciones de la Información Confidencial. Los incisos a) y c) se mantienen."),
    ("h", "TERCERA"),
    ("p", "Se incorpora la nueva cláusula OCTAVA – Protección de datos personales: \"La Parte Receptora tratará los "
          "datos personales contenidos en la Información Confidencial conforme a la Ley 25.326 y notificará a la "
          "Parte Divulgante, dentro de las setenta y dos (72) horas, cualquier incidente de seguridad que los afecte.\""),
    ("h", "CUARTA"),
    ("p", "Las restantes cláusulas del acuerdo original continúan vigentes sin modificación."),
    ("p", "Firmado en Rosario, a los 10 días del mes de marzo de 2026."),
    ("sig", "Parte Divulgante|Parte Receptora"),
], "Adenda N° 1 – Página 1 de 1")
