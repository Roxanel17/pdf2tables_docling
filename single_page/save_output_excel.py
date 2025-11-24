import pandas as pd
import re
from io import StringIO

# input_file = "output.txt"          # ← your markdown/txt file here
# output_excel = "tables_from_txt.xlsx"

input_file = "output.md"          # ← your markdown/txt file here
output_excel = "tables_from_md.xlsx"

# Read file
with open(input_file, "r", encoding="utf-8") as f:
    text = f.read()

lines = text.splitlines()

tables = []
table_titles = []

current_title = "Table"
collecting = False
current_block = []

def flush_block(block_lines, title):
    block = "\n".join(block_lines).strip()
    if not block:
        return
    # Remove markdown separator line (----|----)
    blines = block.splitlines()
    if len(blines) >= 2:
        sep_candidate = blines[1].replace("|", "").strip().replace("-", "")
        if sep_candidate == "":
            blines.pop(1)

    cleaned = "\n".join(blines)

    try:
        df = pd.read_csv(StringIO(cleaned), sep="|", engine="python")
        df = df.dropna(axis=1, how="all")               # remove empty columns
        df.columns = [c.strip() for c in df.columns]    # clean column names

        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        tables.append(df)
        table_titles.append(title)
    except Exception as e:
        print("Failed to parse table:", e)

# Detect titles & tables in text
for line in lines:
    # Section title
    if line.startswith("#"):
        current_title = line.lstrip("#").strip() or "Table"
        if collecting and current_block:
            flush_block(current_block, current_title)
            collecting = False
            current_block = []
        continue

    # Table row
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

# End of file flush
if collecting and current_block:
    flush_block(current_block, current_title)

# Save to Excel
with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
    sheet_name_counts = {}
    for idx, (df, title) in enumerate(zip(tables, table_titles), start=1):

        # Make safe sheet name
        base = re.sub(r'[^0-9A-Za-z]+', '_', title).strip('_')[:28]
        if not base:
            base = f"Table_{idx}"

        sheet_name_counts[base] = sheet_name_counts.get(base, 0) + 1
        name = base if sheet_name_counts[base] == 1 else f"{base}_{sheet_name_counts[base]}"

        df.to_excel(writer, sheet_name=name, index=False)

print(f"Saved Excel file with {len(tables)} tables → {output_excel}")