import argparse
import pandas as pd
from io import StringIO
import re


parser = argparse.ArgumentParser(description="Convert markdown tables to Excel.")
parser.add_argument("input_md", help="Path to markdown or txt file containing tables")
parser.add_argument(
    "--output-xlsx",
    default="tables_from_md.xlsx",
    help="Output Excel file name",
)
args = parser.parse_args()

with open(args.input_md, "r", encoding="utf-8") as f:
    text = f.read()

lines = text.splitlines()

tables = []
titles = []

current_block = []
current_title = "Table"
collecting = False


def flush_block(block_lines, title):
    block = "\n".join(block_lines).strip()
    if not block:
        return
    blines = block.splitlines()
    # Remove markdown separator line if present
    if len(blines) >= 2:
        sep_candidate = blines[1].replace("|", "").strip().replace("-", "")
        if sep_candidate == "":
            blines.pop(1)
    cleaned = "\n".join(blines)

    try:
        df = pd.read_csv(StringIO(cleaned), sep="|", engine="python")
        df = df.dropna(axis=1, how="all")
        df.columns = [str(c).strip() for c in df.columns]
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        tables.append(df)
        titles.append(title)
    except Exception as e:
        print("Failed to parse a table block:", e)


for line in lines:
    if line.startswith("#"):
        # heading → use as title
        current_title = line.lstrip("#").strip() or "Table"
        if collecting and current_block:
            flush_block(current_block, current_title)
            collecting = False
            current_block = []
        continue

    if line.strip().startswith("|"):
        if not collecting:
            collecting = True
            current_block = []
        current_block.append(line)
    else:
        if collecting:
            flush_block(current_block, current_title)
            collecting = False
            current_block = []

# Last block
if collecting and current_block:
    flush_block(current_block, current_title)

print(f"Parsed {len(tables)} tables from {args.input_md}")

if not tables:
    print("No tables found in markdown; NOT creating Excel.")
else:
    output_excel = args.output_xlsx
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        sheet_name_counts = {}
        for i, (df, title) in enumerate(zip(tables, titles), start=1):
            base_name = re.sub(r"[^0-9A-Za-z]+", "_", title).strip("_")[:28]
            if not base_name:
                base_name = f"Table_{i}"
            sheet_name_counts[base_name] = sheet_name_counts.get(base_name, 0) + 1
            sheet_name = (
                base_name
                if sheet_name_counts[base_name] == 1
                else f"{base_name}_{sheet_name_counts[base_name]}"
            )
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Saved Excel with {len(tables)} sheets to {output_excel}")