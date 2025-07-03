import csv
from typing import List, Dict, Optional

class ICD10CM:
    def __init__(self, data: Optional[List[Dict[str, str]]] = None):
        # For demo, use a small sample if no data is provided
        if data is None:
            self.data = [
                {"code": "A00", "desc": "Cholera"},
                {"code": "A00.0", "desc": "Cholera due to Vibrio cholerae 01, biovar cholerae", "parent": "A00"},
                {"code": "A00.1", "desc": "Cholera due to Vibrio cholerae 01, biovar eltor", "parent": "A00"},
                {"code": "A01", "desc": "Typhoid and paratyphoid fevers"},
                {"code": "A01.0", "desc": "Typhoid fever", "parent": "A01"},
            ]
        else:
            self.data = data
        self.code_map = {row["code"]: row for row in self.data}

    def is_valid_item(self, code: str) -> bool:
        return code in self.code_map

    def get_description(self, code: str) -> Optional[str]:
        row = self.code_map.get(code)
        return row["desc"] if row else None

    def get_parent(self, code: str) -> Optional[str]:
        row = self.code_map.get(code)
        return row.get("parent") if row and "parent" in row else None

    def get_children(self, code: str) -> List[str]:
        return [row["code"] for row in self.data if row.get("parent") == code]

    def get_all_codes(self) -> List[str]:
        return list(self.code_map.keys()) 