from docling.document_converter import DocumentConverter
import pandas as pd
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.datamodel.base_models import InputFormat
from docling.document_converter import PdfFormatOption

# ------------------- Documentation Test ----------------------
# converter = DocumentConverter()

# # Convert any document format - we'll use the Docling technical report itself
# source = "https://arxiv.org/pdf/2408.09869"

# # Initialize converter with default settings
# converter = DocumentConverter()
# doc = converter.convert(source).document

# print(doc.export_to_markdown())  # output: "### Docling Technical Report[...]"


# ------------------- PDF Table Extraction Test ----------------------
# Enhanced table processing for complex layouts
pipeline_options = PdfPipelineOptions()
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

# Create converter with enhanced table processing
converter_enhanced = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

result_enhanced = converter_enhanced.convert("page_71.pdf")
doc_enhanced = result_enhanced.document
print(doc_enhanced.export_to_markdown())  # output: "### Docling Technical Report[...]"


markdown_text = doc_enhanced.export_to_markdown()

# Save as Markdown (.md)
with open("output.md", "w", encoding="utf-8") as f:
    f.write(markdown_text)

# Save as plain text (.txt)
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(markdown_text)