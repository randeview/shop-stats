# app/catalog/importer.py
import os
import tempfile
from typing import Optional

from django.db import transaction
from openpyxl import load_workbook
from slugify import slugify

from .models import Category


def _norm(val) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip()
    return s or None


def import_categories_from_xlsx(file_obj, sheet_name: Optional[str] = None) -> int:
    """
    Simplest importer:
      - expects headers: PARENT_CATEGORY, CATEGORY_2LVL, CATEGORY_3LVL
      - for each row, does get_or_create for level1 -> level2 -> level3
      - returns number of categories created
    """
    created = 0

    # Save upload to a temp file (openpyxl needs a path-like)
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

        # Parse header
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

        # Import rows
        with transaction.atomic():
            for row in ws.iter_rows(values_only=True):
                lvl1 = _norm(row[p_idx])
                if not lvl1:
                    continue
                lvl2 = _norm(row[c2_idx])
                lvl3 = _norm(row[c3_idx])

                # Level 1
                c1, was_created = Category.objects.get_or_create(
                    parent=None,
                    slug=slugify(lvl1),
                    defaults={"name": lvl1},
                )
                if was_created:
                    created += 1

                # Level 2 (optional)
                if lvl2:
                    c2, was_created = Category.objects.get_or_create(
                        parent=c1,
                        slug=slugify(lvl2),
                        defaults={"name": lvl2},
                    )
                    if was_created:
                        created += 1
                else:
                    c2 = None

                # Level 3 (optional; only if level 2 exists)
                if lvl3 and c2:
                    _, was_created = Category.objects.get_or_create(
                        parent=c2,
                        slug=slugify(lvl3),
                        defaults={"name": lvl3},
                    )
                    if was_created:
                        created += 1

        wb.close()
        return created

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
