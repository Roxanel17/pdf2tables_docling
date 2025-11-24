import argparse
import sys
import os

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption


def parse_pages(page_args):
    """
    Convert ["71-75", "80", "100-105"] into a sorted set of 1-based page numbers.
    """
    pages = set()
    for arg in page_args:
        if "-" in arg:
            start, end = arg.split("-", 1)
            pages.update(range(int(start), int(end) + 1))
        else:
            pages.add(int(arg))
    return sorted(pages)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Export PDF content with Docling (full document or specific pages)."
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "--pages",
        nargs="+",
        help="Pages or ranges, 1-based (e.g. 71-75 or 71 72 80-85)",
    )
    parser.add_argument(
        "--output-prefix",
        default="output",
        help="Base filename prefix for outputs (without extension)",
    )

    args = parser.parse_args(argv)

    pdf_path = args.pdf_path
    output_prefix = args.output_prefix

    # ---------------- Output folders ----------------
    OUTPUT_DIR = "outputs"
    MD_DIR = os.path.join(OUTPUT_DIR, "outputs_md")
    os.makedirs(MD_DIR, exist_ok=True)

    # ---------------- Pages handling ----------------
    if args.pages:
        user_pages = parse_pages(args.pages)
        print(f"Requested pages (1-based): {user_pages}")
    else:
        user_pages = None
        print("No pages specified → exporting full document markdown.")

    # ---------------- Docling setup ----------------
    pipeline_options = PdfPipelineOptions()
    # For CI / speed, FAST is usually enough. Change to ACCURATE if you prefer.
    pipeline_options.table_structure_options.mode = TableFormerMode.FAST

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    print(f"Processing PDF: {pdf_path}")
    result = converter.convert(pdf_path)
    doc = result.document

    # ---------------- Mode 1: full document ----------------
    if user_pages is None:
        markdown_text = doc.export_to_markdown()

        md_path = os.path.join(MD_DIR, f"{output_prefix}.md")
        txt_path = os.path.join(MD_DIR, f"{output_prefix}.txt")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        print(f"Saved full-document markdown to: {md_path} and {txt_path}")
        return 0

    # ---------------- Mode 2: selected pages ----------------
    chunks = []
    errors = []

    for p in user_pages:
        page_no = p # Docling uses 1-based page indexing
        try:
            page_md = doc.export_to_markdown(page_no=page_no).strip()
            chunks.append(f"### Page {p}\n{page_md}\n")
            print(f"Exported page {p} (page_no={page_no})")
        except Exception as e:
            msg = f"Failed to export page {p} (page_no={page_no}): {e}"
            errors.append(msg)
            print(msg)

    if errors and not chunks:
        markdown_text = "# No pages exported\n\n" + "\n".join(errors)
    else:
        markdown_text = "\n".join(chunks).strip()

    md_path = os.path.join(MD_DIR, f"{output_prefix}_pages.md")
    txt_path = os.path.join(MD_DIR, f"{output_prefix}_pages.txt")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(markdown_text)

    print(f"Saved page-based markdown to: {md_path} and {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())