import argparse
import os
import pandas as pd
import re
from io import StringIO

# ------------- CLI arguments ------------------------
def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Extract markdown tables from a file and save them to an Excel workbook."
    )
    parser.add_argument(
        "input_md",
        help="Path to the markdown/txt file containing pipe-formatted tables",
    )
    parser.add_argument(
        "--output-xlsx",
        default="tables_from_md.xlsx",
        help="Excel filename to create (will be placed under outputs/outputs_excel/)",
    )

    args = parser.parse_args(argv)

    input_file = args.input_md
    output_name = args.output_xlsx

    # --- Output folder: outputs/outputs_excel ---
    OUTPUT_DIR = "outputs"
    EXCEL_DIR = os.path.join(OUTPUT_DIR, "outputs_excel")
    os.makedirs(EXCEL_DIR, exist_ok=True)

    output_excel = os.path.join(EXCEL_DIR, output_name)

    print(f"Reading markdown tables from: {input_file}")
    print(f"Will write Excel to: {output_excel}")

    # --- Read file ---
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

        blines = block.splitlines()
        # Remove markdown separator line if present (----|----)
        if len(blines) >= 2:
            sep_candidate = blines[1].replace("|", "").strip().replace("-", "")
            if sep_candidate == "":
                blines.pop(1)

        cleaned = "\n".join(blines)

        try:
            df = pd.read_csv(StringIO(cleaned), sep="|", engine="python")
            # remove empty columns (from leading/trailing pipes)
            df = df.dropna(axis=1, how="all")
            # clean column names
            df.columns = [c.strip() for c in df.columns]
            # strip string cells
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            tables.append(df)
            table_titles.append(title)
        except Exception as e:
            print("Failed to parse table:", e)

    # --- Detect titles & tables in text ---
    for line in lines:
        # Heading as title
        if line.startswith("#"):
            # use heading text as title
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

    # Flush last block
    if collecting and current_block:
        flush_block(current_block, current_title)

    print(f"Parsed {len(tables)} tables from {input_file}")

    # --- Handle 'no tables' case safely ---
    if not tables:
        print("No tables found in markdown; NOT creating Excel file.")
        return 0

    # --- Write Excel workbook ---
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        sheet_name_counts = {}
        for idx, (df, title) in enumerate(zip(tables, table_titles), start=1):
            # Make safe sheet name
            base = re.sub(r"[^0-9A-Za-z]+", "_", title).strip("_")[:28]
            if not base:
                base = f"Table_{idx}"

            sheet_name_counts[base] = sheet_name_counts.get(base, 0) + 1
            name = base if sheet_name_counts[base] == 1 else f"{base}_{sheet_name_counts[base]}"

            df.to_excel(writer, sheet_name=name, index=False)

    print(f"Saved Excel file with {len(tables)} tables → {output_excel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())