import pandas as pd


class STTMExcelParser:
    """
    Canonical STTM Model
    """

    def __init__(self, file_path: str, sheet_name: str):
        self.file_path = file_path
        self.sheet_name = sheet_name

    def read(self) -> dict:
        df = pd.read_excel(
            self.file_path,
            sheet_name=self.sheet_name,
            header=None
        )

        header_row_idx = None
        target_col_idx = None
        target_type_idx = None
        transform_col_idx = None
        bronze_schema_idx = None
        bronze_table_idx = None

        target_db = None
        target_table = None
        columns = []
        common_join = None

        # ✅ Find header row
        for i in range(len(df)):
            row = df.iloc[i].astype(str).str.strip().tolist()

            if "Target Column*" in row and "Target Data Type*" in row:
                header_row_idx = i
                target_col_idx = row.index("Target Column*")
                target_type_idx = row.index("Target Data Type*")

                if "Data Transformation Rules*" in row:
                    transform_col_idx = row.index("Data Transformation Rules*")
                if "Bronze Schema Name" in row:
                    bronze_schema_idx = row.index("Bronze Schema Name")
                if "Bronze Table name" in row:
                    bronze_table_idx = row.index("Bronze Table name")
                break

        if header_row_idx is None:
            raise ValueError("Header row not found")

        # ✅ Extract Common Join Logic
        for i in range(len(df)):
            row = df.iloc[i].astype(str).str.strip().tolist()
            if "Common Join Logic:" in row:
                common_join = df.iloc[i + 1].astype(str).str.strip().tolist()[0]
                break

        # ✅ Parse data rows
        for i in range(header_row_idx + 1, len(df)):
            row = df.iloc[i]
            row_values = row.astype(str).str.strip().tolist()

            for cell in row_values:
                if cell.startswith("mdm_"):
                    target_db = cell
                if cell.startswith("scd_"):
                    target_table = cell

            target_col = row[target_col_idx]
            target_type = row[target_type_idx]

            transform_text = None
            if transform_col_idx is not None:
                transform_cell = row[transform_col_idx]
                if isinstance(transform_cell, str):
                    transform_text = transform_cell.strip()

            bronze_schema = row[bronze_schema_idx] if bronze_schema_idx is not None else None
            bronze_table = row[bronze_table_idx] if bronze_table_idx is not None else None

            if isinstance(target_col, str) and isinstance(target_type, str):
                target_col = target_col.strip()
                target_type = target_type.strip().lower()

                if target_col and target_type:
                    columns.append({
                        "Bronze Schema Name": bronze_schema.strip() if isinstance(bronze_schema, str) else None,
                        "Bronze Table name": bronze_table.strip() if isinstance(bronze_table, str) else None,
                        "target_column": target_col,
                        "data_type": target_type,
                        "transform": transform_text
                    })

        if not target_db or not target_table:
            raise ValueError("Target not detected")

        return {
            "target": {
                "database": target_db,
                "table": target_table,
            },
            "columns": columns,
            "common_join": common_join
        }
