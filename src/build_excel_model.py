"""Build excel/discount_policy_model.xlsx: a live-formula version of the discount-cap model.

Run from anywhere:  python src/build_excel_model.py
Change the inputs (blue cells on the Inputs sheet) in Excel and every number updates.
"""
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "excel" / "discount_policy_model.xlsx"

FONT = "Arial"
BLUE_INPUT = Font(name=FONT, color="0000FF", bold=True)
GREEN_LINK = Font(name=FONT, color="008000")
BOLD = Font(name=FONT, bold=True)
BASE = Font(name=FONT)
TITLE = Font(name=FONT, bold=True, size=14)
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
HEADER_FONT = Font(name=FONT, bold=True, color="FFFFFF")
INPUT_FILL = PatternFill("solid", fgColor="FFFF00")
TOTAL_BORDER = Border(top=Side(style="thin"), bottom=Side(style="double"))
USD = '$#,##0;($#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'


def load_orders():
    raw = pd.read_csv(ROOT / "data" / "raw" / "superstore.csv", encoding="latin-1")
    return raw.rename(columns={
        "Order ID": "order_id", "Product Category": "category", "Product Sub-Category": "sub_category",
        "Sales": "sales", "Discount": "discount", "Profit": "profit",
    })[["order_id", "category", "sub_category", "sales", "discount", "profit"]]


def header(ws, row, labels, widths=None):
    for j, lab in enumerate(labels, start=1):
        c = ws.cell(row=row, column=j, value=lab)
        c.font, c.fill = HEADER_FONT, HEADER_FILL
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if widths:
        for j, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(j)].width = w


def build():
    orders = load_orders()
    subs = (orders.groupby(["category", "sub_category"]).size().reset_index()
            .sort_values(["category", "sub_category"])[["category", "sub_category"]])
    n_subs, n = len(subs), len(orders)
    wb = Workbook()

    # ---------------- Inputs ----------------
    ws = wb.active
    ws.title = "Inputs"
    ws["A1"] = "Discount-Cap Policy Model: Inputs"; ws["A1"].font = TITLE
    ws["A2"] = "Edit only the blue cells on yellow. Everything else is calculated."; ws["A2"].font = BASE
    ws["A4"], ws["A5"] = "Maximum discount allowed (cap)", "Price elasticity of demand"
    ws["B4"], ws["B5"] = 0.05, -2
    ws["C4"] = "Recommended policy: 5%. Lines already at or below the cap are unchanged."
    ws["C5"] = "Assumption: -2 means a 1% price rise loses 2% of units. Test -1 to -4."
    for r, fmt in [(4, PCT), (5, "0.0")]:
        ws.cell(row=r, column=2).font, ws.cell(row=r, column=2).fill = BLUE_INPUT, INPUT_FILL
        ws.cell(row=r, column=2).number_format = fmt
        ws.cell(row=r, column=1).font = BASE
        ws.cell(row=r, column=3).font = Font(name=FONT, italic=True, color="595959")
    ws["A7"] = "Apply the cap to each sub-category? (Y/N)"; ws["A7"].font = BOLD
    header(ws, 8, ["Sub-category", "Apply cap? (Y/N)", "Category"], [38, 18, 70])
    first_sub = 9
    for i, (_, r) in enumerate(subs.iterrows()):
        row = first_sub + i
        ws.cell(row=row, column=1, value=r["sub_category"]).font = BASE
        c = ws.cell(row=row, column=2, value="Y")
        c.font, c.fill, c.alignment = BLUE_INPUT, INPUT_FILL, Alignment(horizontal="center")
        ws.cell(row=row, column=3, value=r["category"]).font = BASE
    last_sub = first_sub + n_subs - 1
    sub_rng = f"Inputs!$A${first_sub}:$A${last_sub}"
    flag_rng = f"Inputs!$B${first_sub}:$B${last_sub}"
    ws.cell(row=last_sub + 2, column=1, value="Source: Tableau 'Superstore Sales' sample data, 8,399 order lines, 2009-2012.").font = Font(name=FONT, italic=True, color="595959")

    # ---------------- Order Lines ----------------
    wl = wb.create_sheet("Order Lines")
    header(wl, 1, ["Order ID", "Category", "Sub-category", "Sales ($)", "Discount", "Profit ($)",
                   "In scope (1/0)", "New discount", "Price ratio", "Volume factor", "New sales ($)", "New profit ($)"],
           [10, 16, 30, 12, 10, 12, 10, 12, 10, 10, 13, 13])
    for i, r in enumerate(orders.itertuples(index=False), start=2):
        wl.cell(row=i, column=1, value=int(r.order_id))
        wl.cell(row=i, column=2, value=r.category)
        wl.cell(row=i, column=3, value=r.sub_category)
        wl.cell(row=i, column=4, value=float(r.sales)).number_format = '#,##0.00'
        wl.cell(row=i, column=5, value=float(r.discount)).number_format = '0%'
        wl.cell(row=i, column=6, value=float(r.profit)).number_format = '#,##0.00;(#,##0.00)'
        wl.cell(row=i, column=7, value=f'=IF(INDEX({flag_rng},MATCH(C{i},{sub_rng},0))="Y",1,0)')
        wl.cell(row=i, column=8, value=f"=IF(G{i}=1,MIN(E{i},Inputs!$B$4),E{i})").number_format = '0%'
        wl.cell(row=i, column=9, value=f"=(1-H{i})/(1-E{i})").number_format = '0.0000'
        wl.cell(row=i, column=10, value=f"=MAX(0,1+Inputs!$B$5*(I{i}-1))").number_format = '0.0000'
        wl.cell(row=i, column=11, value=f"=D{i}*I{i}*J{i}").number_format = '#,##0.00'
        wl.cell(row=i, column=12, value=f"=(F{i}+D{i}*(I{i}-1))*J{i}").number_format = '#,##0.00;(#,##0.00)'
    wl.freeze_panes = "A2"
    last = n + 1
    rng = lambda col: f"'Order Lines'!${col}$2:${col}${last}"

    # ---------------- Summary ----------------
    sm = wb.create_sheet("Summary", 0)
    sm["A1"] = "Discount-Cap Policy Model: Summary"; sm["A1"].font = TITLE
    sm["A2"] = "Current results vs results with the discount cap set on the Inputs sheet."; sm["A2"].font = BASE
    kpis = [
        ("Discount cap", "=Inputs!B4", PCT, GREEN_LINK),
        ("Price elasticity", "=Inputs!B5", "0.0", GREEN_LINK),
        ("Current profit ($)", f"=SUM({rng('F')})", USD, BASE),
        ("Profit with cap ($)", f"=SUM({rng('L')})", USD, BASE),
        ("Profit uplift ($)", "=B7-B6", USD, BOLD),
        ("Profit uplift (%)", "=IF(B6=0,0,B8/B6)", PCT, BOLD),
        ("Sales change (%)", f"=IF(SUM({rng('D')})=0,0,SUM({rng('K')})/SUM({rng('D')})-1)", PCT, BOLD),
    ]
    for i, (lab, f, fmt, font) in enumerate(kpis, start=4):
        sm.cell(row=i, column=1, value=lab).font = BASE
        c = sm.cell(row=i, column=2, value=f)
        c.number_format, c.font = fmt, font
    top = 13
    header(sm, top, ["Sub-category", "Category", "Current sales ($)", "Current profit ($)", "Current margin",
                     "New sales ($)", "New profit ($)", "New margin", "Profit change ($)"],
           [34, 16, 16, 16, 13, 16, 16, 13, 16])
    for i, (_, r) in enumerate(subs.iterrows()):
        row = top + 1 + i
        sm.cell(row=row, column=1, value=r["sub_category"]).font = BASE
        sm.cell(row=row, column=2, value=r["category"]).font = BASE
        crit = f"{rng('C')},$A{row}"
        sm.cell(row=row, column=3, value=f"=SUMIFS({rng('D')},{crit})").number_format = USD
        sm.cell(row=row, column=4, value=f"=SUMIFS({rng('F')},{crit})").number_format = USD
        sm.cell(row=row, column=5, value=f"=IF(C{row}=0,0,D{row}/C{row})").number_format = PCT
        sm.cell(row=row, column=6, value=f"=SUMIFS({rng('K')},{crit})").number_format = USD
        sm.cell(row=row, column=7, value=f"=SUMIFS({rng('L')},{crit})").number_format = USD
        sm.cell(row=row, column=8, value=f"=IF(F{row}=0,0,G{row}/F{row})").number_format = PCT
        sm.cell(row=row, column=9, value=f"=G{row}-D{row}").number_format = USD
    tot = top + 1 + n_subs
    first, lastrow = top + 1, tot - 1
    sm.cell(row=tot, column=1, value="Total").font = BOLD
    for col, fmt in [(3, USD), (4, USD), (6, USD), (7, USD), (9, USD)]:
        L = get_column_letter(col)
        c = sm.cell(row=tot, column=col, value=f"=SUM({L}{first}:{L}{lastrow})")
        c.number_format, c.font, c.border = fmt, BOLD, TOTAL_BORDER
    for col, num, den in [(5, "D", "C"), (8, "G", "F")]:
        c = sm.cell(row=tot, column=col, value=f"=IF({den}{tot}=0,0,{num}{tot}/{den}{tot})")
        c.number_format, c.font, c.border = PCT, BOLD, TOTAL_BORDER
    sm.cell(row=tot + 2, column=1, value="Model: new price ratio = (1 - new discount)/(1 - old discount); volume factor = 1 + elasticity x (ratio - 1); "
            "new profit = (old profit + sales x (ratio - 1)) x volume factor. Unit cost is held constant.").font = Font(name=FONT, italic=True, color="595959")
    sm.freeze_panes = f"A{top + 1}"

    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)
    return OUT, n, n_subs


if __name__ == "__main__":
    path, n, n_subs = build()
    print(f"Wrote {path.relative_to(ROOT)}: {n:,} order lines with live formulas, {n_subs} sub-category switches.")
