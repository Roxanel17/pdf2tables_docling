import argparse
import re
import sys

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
import pandas as pd


# ------------- Parse --pages argument ---------------
def parse_pages(page_args):
    """
    Convert ["71-75", "80", "100-105"] into a set of pages.
    """
    pages = set()
    for arg in page_args:
        if "-" in arg:
            start, end = arg.split("-", 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(arg))
    return pages


# ------------- CLI arguments ------------------------
parser = argparse.ArgumentParser(description="Extract tables from specific PDF pages.")
parser.add_argument("pdf_path", help="Path to the PDF file")
parser.add_argument(
    "--pages",
    nargs="+",
    required=True,
    help="Pages or ranges, e.g., 71-75 or 10 12 20-25",
)
args = parser.parse_args()

target_pages = parse_pages(args.pages)
print(f"Extracting tables from pages: {sorted(target_pages)}")

# ------------- Docling configuration ----------------
pipeline_options = PdfPipelineOptions()
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

converter_enhanced = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

# Convert full document
result_enhanced = converter_enhanced.convert(args.pdf_path)
doc_enhanced = result_enhanced.document

# Debug: see which pages actually have tables
all_tables = getattr(doc_enhanced, "tables", [])
available_pages = sorted({getattr(t, "page_no", None) for t in all_tables})
print("Pages that actually contain tables:", available_pages)

# ------------- Filter tables ------------------------
selected_tables = [
    t for t in all_tables
    if getattr(t, "page_no", None) in target_pages
]

print(f"Found {len(selected_tables)} tables on selected pages.")

# If no tables, exit cleanly BEFORE any Excel writer is created
if not selected_tables:
    print("No tables found on the requested pages. Exiting without creating files.")
    sys.exit(0)

# ------------- Markdown / TXT output ----------------
markdown_chunks = []
for t in selected_tables:
    page = getattr(t, "page_no", "?")
    title = getattr(t, "title", f"Table on page {page}")
    markdown_chunks.append(f"### {title} (page {page})\n")
    markdown_chunks.append(t.export_to_markdown())
    markdown_chunks.append("")

markdown_text = "\n".join(markdown_chunks).strip()

with open("selected_tables.md", "w", encoding="utf-8") as f:
    f.write(markdown_text)

with open("selected_tables.txt", "w", encoding="utf-8") as f:
    f.write(markdown_text)

print("Saved selected_tables.md and selected_tables.txt")

# ------------- Excel output ------------------------
output_excel = "selected_tables.xlsx"

with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
    for idx, t in enumerate(selected_tables, start=1):
        df = t.to_pandas()
        page = getattr(t, "page_no", "p")
        title = getattr(t, "title", f"table_{idx}")
        sheet = re.sub(r"[^A-Za-z0-9]+", "_", f"p{page}_{title}")[:28]
        df.to_excel(writer, sheet_name=sheet, index=False)

print(f"Saved Excel: {output_excel}")