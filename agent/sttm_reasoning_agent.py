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

            transform_sql, filter_sql, join_sql = self._split_transform(raw_transform)

            # ✅ ✅ ✅ EXACT MATCH TO EXCEL HEADER
            bronze_table = col.get("Bronze Table name")   # ✅ FIX HERE

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

            if name.lower().startswith("xtndf") or name.lower() in (
                "createdtime", "createdbyid", "updatedtime", "updatedbyid"
            ):
                audit_columns.append(entry)
            else:
                business_columns.append(entry)

        if not source_tables:
            raise ValueError(
                "Bronze Table name not found. "
                "Check STTM column header spelling exactly."
            )

        return {
            "target": self.sttm["target"],
            "audit_columns": audit_columns,
            "business_columns": business_columns,
            "all_columns": all_columns,
            "source_tables": list(source_tables)   # ✅ CORRECT NOW
        }

    def _split_transform(self, text):

        if not text:
            return None, None, None

        transform = None
        filter_ = None
        join = None

        for part in str(text).split("#"):
            part = part.strip()
            if part.startswith("Transform"):
                transform = part.replace("Transform", "").strip()
            elif part.startswith("Filter"):
                filter_ = part.replace("Filter", "").strip()
            elif part.startswith("JOIN"):
                join = part.replace("JOIN", "").strip()

        return transform, filter_, join
