from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption
import pandas as pd
import re

# ------------------- PDF Table Extraction (pages 71–75 only) ----------------------

# 1. Set up pipeline with accurate table mode
pipeline_options = PdfPipelineOptions()
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

converter_enhanced = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# 2. Convert the FULL PDF (not just one page)
result_enhanced = converter_enhanced.convert("BRD_IFRS_December 2024 EN.pdf")
doc_enhanced = result_enhanced.document

# 3. Select only tables whose page_no is between 71 and 75
target_pages = set(range(71, 76))  # {71, 72, 73, 74, 75}

selected_tables = [
    t for t in doc_enhanced.tables
    if getattr(t, "page_no", None) in target_pages
]

print(f"Found {len(selected_tables)} tables on pages 71–75")

# 4. Build markdown from just those tables
tables_md = []
for t in selected_tables:
    page = getattr(t, "page_no", "?")
    title = getattr(t, "title", "") or f"Table on page {page}"
    tables_md.append(f"### {title} (page {page})\n")
    tables_md.append(t.export_to_markdown())
    tables_md.append("")  # blank line between tables

markdown_text = "\n".join(tables_md).strip()

# 5. Save as Markdown (.md)
with open("output_selected.md", "w", encoding="utf-8") as f:
    f.write(markdown_text)

# 6. Save as plain text (.txt)
with open("output_selected.txt", "w", encoding="utf-8") as f:
    f.write(markdown_text)

print("Saved tables from pages 71–75 to output_selected.md and output_selected.txt")