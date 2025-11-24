import argparse
import sys

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption


def parse_pages(page_args):
    """
    Convert ["71-75", "80", "100-105"] into a set of page numbers (int, 1-based).
    """
    pages = set()
    for arg in page_args:
        if "-" in arg:
            start, end = arg.split("-", 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(arg))
    return pages


parser = argparse.ArgumentParser(
    description=(
        "Convert a PDF with Docling.\n"
        "Without --pages: export full document markdown (like docling_test.py).\n"
        "With --pages: export ONLY those pages' markdown (page-based, not table-based)."
    )
)
parser.add_argument("pdf_path", help="Path to the PDF file")
parser.add_argument(
    "--pages",
    nargs="+",
    help="Optional: pages or ranges, 1-based, e.g. 71-75 or 10 12 20-25",
)
parser.add_argument(
    "--output-prefix",
    default="output",
    help="Base name for output files (default: output -> output.md / output.txt)",
)

args = parser.parse_args()

pdf_path = args.pdf_path
output_prefix = args.output_prefix

if args.pages:
    # User-facing pages are 1-based
    user_pages = sorted(parse_pages(args.pages))
    print(f"Requested pages (1-based): {user_pages}")
else:
    user_pages = None
    print("No pages specified; exporting full document markdown.")


# ------------------- Docling setup (same as docling_test.py) ----------------------
pipeline_options = PdfPipelineOptions()
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

converter_enhanced = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result_enhanced = converter_enhanced.convert(pdf_path)
doc_enhanced = result_enhanced.document

# ------------------- Mode 1: no pages -> full doc markdown ------------------------
if user_pages is None:
    markdown_text = doc_enhanced.export_to_markdown()

    md_path = f"{output_prefix}.md"
    txt_path = f"{output_prefix}.txt"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    print(f"Saved full document markdown to: {md_path} and {txt_path}")
    sys.exit(0)


# ------------------- Mode 2: specific pages -> per-page export --------------------
# We assume Docling uses 0-based page_no
chunks = []
errors = []

for p in user_pages:
    # page_index = p - 1  # convert 1-based -> 0-based for Docling
    page_index = p # to test
    try:
        page_md = doc_enhanced.export_to_markdown(page_no=page_index)
        chunks.append(f"### Page {p}\n")
        chunks.append(page_md.strip())
        chunks.append("")  # blank line between pages
        print(f"Exported page {p} (page_no={page_index})")
    except Exception as e:
        msg = f"Failed to export page {p} (page_no={page_index}): {e}"
        print(msg)
        errors.append(msg)

if not chunks:
    markdown_text = "# No pages exported\n\n"
    if errors:
        markdown_text += "Errors:\n\n" + "\n".join(f"- {e}" for e in errors)
else:
    markdown_text = "\n".join(chunks).strip()

md_path = f"{output_prefix}_pages.md"
txt_path = f"{output_prefix}_pages.txt"

with open(md_path, "w", encoding="utf-8") as f:
    f.write(markdown_text)

with open(txt_path, "w", encoding="utf-8") as f:
    f.write(markdown_text)

print(f"Saved page-based markdown to: {md_path} and {txt_path}")