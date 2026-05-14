class STTMReasoningAgent:
    """
    ✅ FINAL AGENT
    - Extracts Bronze table name from STTM column ✅
    - Passes it to generator as source_tables ✅
    """

    def __init__(self, sttm_metadata: dict):
        self.sttm = sttm_metadata

    def analyze(self) -> dict:

        all_columns = []
        source_tables = set()

        for col in self.sttm["columns"]:

            # ✅ TARGET DETAILS
            name = col["target_column"]
            dtype = col["data_type"]
            raw_transform = col.get("transform", "")

            # ✅ SPLIT TRANSFORM
            transform_sql, filter_sql, join_sql = self._split_transform(raw_transform)

            # ✅ ✅ BRONZE TABLE EXTRACTION (THIS IS THE KEY FIX)
            # Bronze table name is in SECOND COLUMN of STTM
            # Usually stored as source_table / bronze_table / input_table
            bronze_tbl = (
                col.get("bronze_table")
                or col.get("source_table")
                or col.get("input_table")
            )

            if bronze_tbl:
                source_tables.add(bronze_tbl.strip())

            entry = {
                "name": name,
                "type": dtype,
                "transform_sql": transform_sql,
                "filter_sql": filter_sql,
                "join_sql": join_sql
            }

            all_columns.append(entry)

        return {
            "target": self.sttm["target"],
            "all_columns": all_columns,
            "source_tables": list(source_tables)  # ✅ SENT TO GENERATOR
        }

    def _split_transform(self, text):

        if not text:
            return None, None, None

        text = str(text)

        transform = None
        filter_ = None
        join = None

        parts = text.split("#")

        for part in parts:
            part = part.strip()

            if part.startswith("Transform"):
                transform = part.replace("Transform", "").strip()

            elif part.startswith("Filter"):
                filter_ = part.replace("Filter", "").strip()

            elif part.startswith("JOIN"):
                join = part.replace("JOIN", "").strip()

        return transform, filter_, join
