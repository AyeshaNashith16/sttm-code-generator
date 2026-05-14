class STTMReasoningAgent:

    def __init__(self, sttm_metadata: dict):
        self.sttm = sttm_metadata

    def analyze(self) -> dict:
        audit_columns = []
        business_columns = []
        all_columns = []

        # ✅ SINGLE SOURCE OF TRUTH
        source_tables = set()

        for col in self.sttm["columns"]:

            name = col["target_column"]
            dtype = col["data_type"]
            raw_transform = col.get("transform", "")

            # ✅ Split transform
            transform_sql, filter_sql, join_sql = self._split_transform(raw_transform)

            # ✅ ✅ ✅ CRITICAL FIX
            # Bronze table comes from STTM 2nd column
            # Change key ONLY if your column name differs
            bronze_table = (
                col.get("Bronze Table Name") or
                col.get("Bronze Table") or
                col.get("Source Table") or
                col.get("source_table")
            )

            if bronze_table:
                source_tables.add(bronze_table.strip())

            entry = {
                "name": name,
                "type": dtype,
                "transform_sql": transform_sql,
                "filter_sql": filter_sql,
                "join_sql": join_sql
            }

            all_columns.append(entry)

            # ✅ classify columns
            if name.lower().startswith("xtndf") or name.lower() in (
                "createdtime", "createdbyid", "updatedtime", "updatedbyid"
            ):
                audit_columns.append(entry)
            else:
                business_columns.append(entry)

        if not source_tables:
            raise ValueError(
                "Bronze table not found. Check STTM column header for Bronze Table Name."
            )

        return {
            "target": self.sttm["target"],
            "audit_columns": audit_columns,
            "business_columns": business_columns,
            "all_columns": all_columns,
            "source_tables": list(source_tables)   # ✅ CORRECT VALUE
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
``
