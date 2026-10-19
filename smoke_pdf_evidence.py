"""Exercise real CPU extraction without discovery, LLM calls or inventory writes."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle

from pdf_evidence import extract_pdf, save_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-pdf", type=Path)
    args = parser.parse_args()
    folder = Path(".research-cache/pdf-smoke")
    folder.mkdir(parents=True, exist_ok=True)
    plain = folder / "plain.pdf"
    doc = canvas.Canvas(str(plain))
    doc.drawString(50, 760, "A reusable English benchmark contains twelve tasks and one hundred examples.")
    doc.save()
    table = folder / "merged-table.pdf"
    doc = canvas.Canvas(str(table))
    doc.drawString(50, 760, "Table 1: Benchmark dataset splits")
    cells = Table([["Benchmark", "Examples", ""], ["", "Train", "Test"],
                   ["Alpha", "120", "30"], ["Beta", "240", "60"]], colWidths=[150, 100, 100], rowHeights=35)
    cells.setStyle(TableStyle([("SPAN", (1, 0), (2, 0)), ("SPAN", (0, 0), (0, 1)),
                              ("GRID", (0, 0), (-1, -1), 1, "black"), ("FONTSIZE", (0, 0), (-1, -1), 14)]))
    cells.wrapOn(doc, 450, 600)
    cells.drawOn(doc, 50, 550)
    doc.showPage()
    doc.drawString(50, 760, "Physical page two: the evaluation uses held-out test examples.")
    doc.save()
    scan = folder / "scan.pdf"
    image = Image.new("RGB", (1200, 1600), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=30)
    draw.text((80, 150), "Scanned benchmark evidence", fill="black", font=font)
    draw.text((80, 230), "The dataset contains 240 examples.", fill="black", font=font)
    image.save(scan, "PDF", resolution=150)
    paths = [plain, table, scan]
    if args.real_pdf:
        from pypdf import PdfReader, PdfWriter
        writer = PdfWriter()
        for page in PdfReader(args.real_pdf).pages[:2]:
            writer.add_page(page)
        subset = folder / "real-paper-first-two-pages.pdf"
        writer.write(str(subset))
        paths.append(subset)
    reports = []
    for path in paths:
        result = extract_pdf(path)
        if path == plain:
            assert result["extraction"]["backend"] == "poppler"
        elif path == table:
            assert result["extraction"]["backend"] == "mineru"
            assert result["page_numbers"] == [1, 2]
            assert "Physical page two" in result["pages"][1]
            saved = json.loads(path.with_suffix(".pages.json").read_text())
            tables = [b["table_body"] for b in saved["pages"][0]["blocks"] if b["type"] == "table"]
            assert tables and all(value in " ".join(tables) for value in ("120", "240", "Train", "Test"))
        elif path == scan:
            assert result["extraction"]["backend"] == "mineru"
            assert "240" in result["pages"][0]
        reports.append({"fixture": path.name, **result["extraction"]})
        save_json(folder / "smoke-report.json", reports)
    print(json.dumps(reports, indent=2))


if __name__ == "__main__":
    main()
