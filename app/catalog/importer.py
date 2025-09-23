# app/catalog/importer.py
import os
import tempfile
from typing import Optional

from openpyxl import load_workbook


def _norm(val) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s or None


def import_categories_from_xlsx(file_obj, sheet_name: Optional[str] = None) -> int:
    fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    try:
        with os.fdopen(fd, "wb") as tmp:
            if hasattr(file_obj, "chunks"):
                for chunk in file_obj.chunks():
                    tmp.write(chunk)
            else:
                tmp.write(file_obj.read())

        wb = load_workbook(tmp_path, read_only=True, data_only=True)
        ws = wb[sheet_name] if sheet_name else wb.active
        header = next(ws.iter_rows(values_only=True))
        header = [str(x).strip() if x else "" for x in header]
        try:
            p_idx = header.index("PARENT_CATEGORY")
            c2_idx = header.index("CATEGORY_2LVL")
            c3_idx = header.index("CATEGORY_3LVL")
        except ValueError:
            wb.close()
            raise ValueError(
                "Header must contain PARENT_CATEGORY, CATEGORY_2LVL, CATEGORY_3LVL"
            )
        counter = 0
        for row in ws.iter_rows(values_only=True):
            counter += 1
            if counter > 8000:
                break
            cat_1 = str(row[p_idx]).strip() if row[p_idx] else None
            cat_2 = str(row[c2_idx]).strip() if row[c2_idx] else None
            cat_3 = str(row[c3_idx]).strip() if row[c3_idx] else None
            if cat_1 == "PARENT_CATEGORY":
                continue
            print(f"1:{cat_1}- 2:{cat_2} - 3:{cat_3}")
            print()

        wb.close()

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
