"""Construit docs/Rapport_TP_Kubernetes_Beloucif_Morice.pdf à partir de docs/RAPPORT.md.

Usage : python scripts/build_rapport_pdf.py
Gère le sous-ensemble de Markdown utilisé par le rapport : titres, paragraphes,
listes, tableaux, blocs de code, images et gras.
"""
import os
import re

from fpdf import FPDF
from fpdf.fonts import FontFace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "docs", "RAPPORT.md")
OUT = os.path.join(ROOT, "docs", "Rapport_TP_Kubernetes_Beloucif_Morice.pdf")
WIN = "C:/Windows/Fonts/"
GILROY = os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts/")
# Charte EFREI : Gilroy (police de l'école, installée sur le poste, non versionnée), sinon Segoe UI.
_LIGHT, _BOLD = GILROY + "Gilroy-Light.otf", GILROY + "Gilroy-ExtraBold.otf"
HAS_GILROY = os.path.exists(_LIGHT) and os.path.exists(_BOLD)
FONTS = {
    "text": (_LIGHT, _BOLD) if HAS_GILROY else (WIN + "segoeui.ttf", WIN + "segoeuib.ttf"),
    "mono": WIN + "consola.ttf",
}


def as_truetype(path: str) -> str:
    """Convertit une police OTF à contours CFF en TTF (cache temporaire).

    fpdf2 incruste les OTF CFF sous le type TrueType, ce que certains lecteurs PDF
    affichent mal ; une conversion préalable des contours en quadratiques évite le souci.
    """
    if not path.lower().endswith(".otf"):
        return path
    import tempfile
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont, newTable

    out = os.path.join(tempfile.gettempdir(), os.path.basename(path)[:-4] + ".ttf")
    if os.path.exists(out):
        return out
    font = TTFont(path)
    glyph_set = font.getGlyphSet()
    glyf, loca = newTable("glyf"), newTable("loca")
    glyf.glyphOrder = font.getGlyphOrder()
    glyf.glyphs = {}
    for name in glyf.glyphOrder:
        pen = TTGlyphPen(glyph_set)
        glyph_set[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
        glyf.glyphs[name] = pen.glyph()
    font["glyf"], font["loca"] = glyf, loca
    for tag in ("CFF ", "VORG"):
        if tag in font:
            del font[tag]
    font["maxp"] = newTable("maxp")
    maxp = font["maxp"]
    maxp.tableVersion = 0x00010000
    for attr in ("maxZones", "maxTwilightPoints", "maxStorage", "maxFunctionDefs",
                 "maxInstructionDefs", "maxStackElements", "maxSizeOfInstructions",
                 "maxComponentElements", "maxPoints", "maxContours",
                 "maxCompositePoints", "maxCompositeContours", "maxComponentDepth"):
        setattr(maxp, attr, 0)
    maxp.maxZones = 1
    maxp.numGlyphs = len(glyf.glyphOrder)
    font["head"].glyphDataFormat = 0
    font["post"].formatType = 2.0
    font["post"].extraNames = []
    font["post"].mapping = {}
    font.sfntVersion = "\x00\x01\x00\x00"
    font.save(out)
    return out


LOGO_BLANC = os.path.join(ROOT, "docs", "assets", "Logo-Efrei-Blanc.png")
LOGO_COULEUR = os.path.join(ROOT, "docs", "assets", "Logo-Efrei-CMJN.png")
NAVY = (5, 24, 50)
BLEU = (22, 55, 103)
ROSE = (255, 67, 184)
TEXTE = (33, 33, 33)
MUTED = (90, 107, 130)


class Report(FPDF):
    # fpdf2 lit "--" comme du souligné, ce qui casse les options de commande (--driver...).
    MARKDOWN_UNDERLINE_MARKER = "^^^"

    def header(self):
        if self.page_no() > 1:
            self.image(LOGO_COULEUR, x=self.l_margin, y=8, h=6)
            self.set_font("text", size=8)
            self.set_text_color(*MUTED)
            self.set_xy(self.l_margin, 8)
            self.cell(0, 6, "TP Kubernetes - Adam Beloucif et Emilien Morice", align="R")
            self.set_draw_color(*ROSE)
            self.set_line_width(0.4)
            self.line(self.l_margin, 16, self.w - self.r_margin, 16)
            self.set_y(20)

    def footer(self):
        self.set_y(-12)
        self.set_font("text", size=8)
        self.set_text_color(*MUTED)
        self.cell(0, 6, f"EFREI - M2 Data Engineering & IA - {self.page_no()}/{{nb}}", align="C")


def inline(text: str) -> str:
    """Convertit le Markdown en ligne vers le balisage accepté par fpdf2 (gras seulement)."""
    return text.replace("`", "")


def build() -> None:
    pdf = Report(format="A4")
    pdf.set_margins(18, 15, 18)
    pdf.set_auto_page_break(True, 16)
    pdf.add_font("text", "", as_truetype(FONTS["text"][0]))
    pdf.add_font("text", "B", as_truetype(FONTS["text"][1]))
    pdf.add_font("mono", "", FONTS["mono"])
    pdf.alias_nb_pages()
    lines = open(SRC, encoding="utf-8").read().split("\n")
    width = pdf.w - pdf.l_margin - pdf.r_margin

    # Page de garde : titre et méta (lignes en gras qui suivent le titre).
    pdf.add_page()
    title = lines[0].lstrip("# ").strip()
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 0, pdf.w, pdf.h, style="F")
    pdf.set_fill_color(*ROSE)
    pdf.rect(0, 0, 6, pdf.h, style="F")
    pdf.image(LOGO_BLANC, x=pdf.l_margin + 4, y=28, h=22)
    pdf.set_xy(pdf.l_margin + 4, 95)
    pdf.set_text_color(*ROSE)
    pdf.set_font("text", "B", 11)
    pdf.cell(0, 6, "M2 DATA ENGINEERING & IA - MODULE DEVOPS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.l_margin + 4)
    pdf.set_text_color(255)
    pdf.set_font("text", "B", 26)
    pdf.multi_cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*ROSE)
    pdf.set_line_width(1.2)
    pdf.line(pdf.l_margin + 4, pdf.get_y() + 6, pdf.l_margin + 50, pdf.get_y() + 6)
    pdf.set_y(pdf.get_y() + 18)
    i = 1
    while i < len(lines) and not lines[i].startswith("## "):
        if lines[i].strip():
            pdf.set_x(pdf.l_margin + 4)
            pdf.set_text_color(230)
            pdf.set_font("text", "", 12.5)
            pdf.multi_cell(0, 8, lines[i].strip(), markdown=True, new_x="LMARGIN", new_y="NEXT")
        i += 1
    pdf.add_page()

    in_code, code, table = False, [], []
    para: list[str] = []

    def flush_para():
        if para:
            pdf.set_font("text", "", 11)
            pdf.set_text_color(*TEXTE)
            pdf.multi_cell(0, 5.8, inline(" ".join(para)), markdown=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2.5)
            para.clear()

    def flush_table():
        if not table:
            return
        rows = [[c.strip() for c in r.strip("|").split("|")] for r in table if not re.match(r"^\|[-| ]+\|$", r)]
        pdf.set_font("text", "", 10)
        pdf.set_text_color(*TEXTE)
        pdf.set_fill_color(255)
        pdf.set_draw_color(*BLEU)
        with pdf.table(headings_style=FontFace(emphasis="BOLD", color=255, fill_color=BLEU),
                       line_height=6.5, text_align="LEFT", col_widths=(1, 2)) as t:
            for r in rows:
                row = t.row()
                for c in r:
                    row.cell(inline(c))
        pdf.ln(3)
        table.clear()

    for line in lines[i:]:
        if line.startswith("```"):
            if in_code:
                pdf.set_font("mono", "", 8.5)
                pdf.set_fill_color(244, 244, 244)
                pdf.set_text_color(30)
                pdf.multi_cell(0, 4.3, "\n".join(code), fill=True, border=0, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)
                code.clear()
            else:
                flush_para()
            in_code = not in_code
            continue
        if in_code:
            code.append(line)
            continue
        if line.startswith("|"):
            flush_para()
            table.append(line)
            continue
        flush_table()
        img = re.match(r"!\[(.*?)\]\((.*?)\)", line)
        if line.startswith("## "):
            flush_para()
            if pdf.get_y() > pdf.h - 60:
                pdf.add_page()
            pdf.ln(3)
            pdf.set_font("text", "B", 15)
            pdf.set_text_color(*BLEU)
            pdf.multi_cell(0, 8, line[3:].strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(*ROSE)
            pdf.set_line_width(0.6)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 30, pdf.get_y())
            pdf.ln(4)
        elif img:
            flush_para()
            path = os.path.normpath(os.path.join(ROOT, "docs", img.group(2)))
            from PIL import Image
            w_px, h_px = Image.open(path).size
            h = width * h_px / w_px
            max_h = pdf.h - 40
            w = width
            if h > max_h:
                w, h = width * max_h / h, max_h
            if pdf.get_y() + h > pdf.h - 16:
                pdf.add_page()
            pdf.image(path, x=pdf.l_margin + (width - w) / 2, w=w, h=h)
            pdf.ln(4)
        elif line.startswith("- "):
            flush_para()
            pdf.set_font("text", "", 11)
            pdf.set_text_color(*TEXTE)
            pdf.set_x(pdf.l_margin + 4)
            pdf.multi_cell(width - 4, 5.6, "\u2022  " + inline(line[2:]), markdown=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(0.8)
        elif not line.strip():
            flush_para()
        else:
            para.append(line.strip())
    flush_para()
    flush_table()
    pdf.output(OUT)
    print(OUT, pdf.page_no(), "pages")


if __name__ == "__main__":
    build()
