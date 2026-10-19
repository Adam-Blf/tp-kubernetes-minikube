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
FONTS = {
    "text": (WIN + "segoeui.ttf", WIN + "segoeuib.ttf", WIN + "segoeuii.ttf"),
    "mono": WIN + "consola.ttf",
}
NAVY = (0, 19, 41)
BRASS = (212, 164, 55)


class Report(FPDF):
    # fpdf2 lit "--" comme du souligné, ce qui casse les options de commande (--driver...).
    MARKDOWN_UNDERLINE_MARKER = "^^^"

    def header(self):
        if self.page_no() > 1:
            self.set_font("text", size=8)
            self.set_text_color(120)
            self.cell(0, 6, "TP Kubernetes - Adam Beloucif et Emilien Morice", align="L")
            self.ln(8)

    def footer(self):
        self.set_y(-12)
        self.set_font("text", size=8)
        self.set_text_color(120)
        self.cell(0, 6, f"{self.page_no()}/{{nb}}", align="C")


def inline(text: str) -> str:
    """Convertit le Markdown en ligne vers le balisage accepté par fpdf2 (gras seulement)."""
    return text.replace("`", "")


def build() -> None:
    pdf = Report(format="A4")
    pdf.set_margins(18, 15, 18)
    pdf.set_auto_page_break(True, 16)
    pdf.add_font("text", "", FONTS["text"][0])
    pdf.add_font("text", "B", FONTS["text"][1])
    pdf.add_font("text", "I", FONTS["text"][2])
    pdf.add_font("mono", "", FONTS["mono"])
    pdf.alias_nb_pages()
    lines = open(SRC, encoding="utf-8").read().split("\n")
    width = pdf.w - pdf.l_margin - pdf.r_margin

    # Page de garde : titre et méta (lignes en gras qui suivent le titre).
    pdf.add_page()
    title = lines[0].lstrip("# ").strip()
    pdf.set_y(80)
    pdf.set_fill_color(*NAVY)
    pdf.rect(0, 70, pdf.w, 70, style="F")
    pdf.set_text_color(255)
    pdf.set_font("text", "B", 22)
    pdf.multi_cell(0, 11, title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*BRASS)
    pdf.set_line_width(1)
    pdf.line(70, 128, pdf.w - 70, 128)
    pdf.set_y(160)
    pdf.set_text_color(30)
    i = 1
    while i < len(lines) and not lines[i].startswith("## "):
        if lines[i].strip():
            pdf.set_font("text", "", 12)
            pdf.multi_cell(0, 8, lines[i].strip(), align="C", markdown=True, new_x="LMARGIN", new_y="NEXT")
        i += 1
    pdf.add_page()

    in_code, code, table = False, [], []
    para: list[str] = []

    def flush_para():
        if para:
            pdf.set_font("text", "", 10.5)
            pdf.set_text_color(30)
            pdf.multi_cell(0, 5.6, inline(" ".join(para)), markdown=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2.5)
            para.clear()

    def flush_table():
        if not table:
            return
        rows = [[c.strip() for c in r.strip("|").split("|")] for r in table if not re.match(r"^\|[-| ]+\|$", r)]
        pdf.set_font("text", "", 10)
        pdf.set_text_color(30)
        pdf.set_fill_color(255)
        with pdf.table(headings_style=FontFace(emphasis="BOLD", color=255, fill_color=NAVY),
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
                pdf.set_fill_color(244, 246, 248)
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
            pdf.set_text_color(*NAVY)
            pdf.multi_cell(0, 8, line[3:].strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(*BRASS)
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
            pdf.set_font("text", "", 10.5)
            pdf.set_text_color(30)
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
