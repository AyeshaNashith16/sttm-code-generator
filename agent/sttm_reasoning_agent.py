class STTMReasoningAgent:

    def __init__(self, sttm_metadata: dict):
        self.sttm = sttm_metadata

    def analyze(self) -> dict:
        audit_columns = []
        business_columns = []
        all_columns = []

        source_tables = set()   # ✅ NEW (correct place)

        for col in self.sttm["columns"]:

            name = col["target_column"]
            dtype = col["data_type"]
            raw_transform = col.get("transform", "")

            # ✅ Split transform correctly
            transform_sql, filter_sql, join_sql = self._split_transform(raw_transform)

            entry = {
                "name": name,
                "type": dtype,
                "transform_sql": transform_sql,
                "filter_sql": filter_sql,
                "join_sql": join_sql
            }

            all_columns.append(entry)

            # ✅ Extract source tables HERE (correct place)
            if raw_transform and "tbl_" in raw_transform:
                lines = raw_transform.split("\n")
                for line in lines:
                    if "tbl_" in line:
                        source_tables.add(line.strip())

            # ✅ classify columns
            if name.lower().startswith("xtndf") or name.lower() in (
                "createdtime", "createdbyid", "updatedtime", "updatedbyid"
            ):
                audit_columns.append(entry)
            else:
                business_columns.append(entry)

        return {
            "target": self.sttm["target"],
            "audit_columns": audit_columns,
            "business_columns": business_columns,
            "all_columns": all_columns,
            "source_tables": list(source_tables)   # ✅ now correct
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

        # ✅ RETURN ONLY THESE
        return transform, filter_, join