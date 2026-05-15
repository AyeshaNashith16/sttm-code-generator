class STTMReasoningAgent:

    def __init__(self, = None    def __init__(self, sttm_metadata: dict):

        # ✅ Extract Bronze Schema + Table ONCE
        for col in self.sttm["columns"]:
            bronze_schema = col.get("Bronze Schema Name")
            bronze_table = col.get("Bronze Table name")

            if bronze_schema and bronze_table:
                source_db = bronze_schema.strip()
                source_tables.add(
                    f"{bronze_schema.strip()}.{bronze_table.strip()}"
                )
                break

        if not source_tables:
            raise ValueError(
                "Bronze Schema/Table not found in STTM columns. "
                "Parser must include 'Bronze Schema Name' and 'Bronze Table name'."
            )

        for col in self.sttm["columns"]:
            name = col["target_column"]
            dtype = col["data_type"]
            raw_transform = col.get("transform", "")

            transform_sql, filter_sql, join_sql = self._split_transform(raw_transform)

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

        return {
            "target": self.sttm["target"],
            "audit_columns": audit_columns,
            "business_columns": business_columns,
            "all_columns": all_columns,
            "source_tables": list(source_tables),
            "source_db": source_db
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
``
        self.sttm = sttm_metadata

    def analyze(self) -> dict:
        audit_columns = []
        business_columns = []
        all_columns = []

        source_tables = set()
