import re


class DatabricksNotebookGenerator:
    """
    FINAL ENTERPRISE GENERATOR
    - Base table from Agent
    - JOIN from Common Join Logic
    """

    def __init__(self, sttm_output: dict):
        self.sttm = sttm_output

        self.source_tables = sttm_output.get("source_tables", [])
        if not self.source_tables:
            raise ValueError("Bronze table not provided by Agent")

        self.main_table = self.source_tables[0]

    def build_transformation_sql(self):
        select_lines = []

        for col in self.sttm["all_columns"]:
            name = col["name"]
            transform = col.get("transform_sql")

            if transform:
                t = transform.strip().rstrip(",")

                # ✅ clean properly
                t = re.sub(r"\s+", " ", t)
                t = t.replace("<>", " <> ")

                if "CASE" in t:
                    t = (
                        t.replace(" CASE", "\n        CASE")
                        .replace(" WHEN", "\n            WHEN")
                        .replace(" ELSE", "\n            ELSE")
                        .replace(" END", "\n        END")
                    )
                    select_lines.append(t)

                elif t.lower() == "direct":
                    select_lines.append(f"        {name}")

                elif "CURRENT_TIMESTAMP" in t:
                    select_lines.append(f"        CURRENT_TIMESTAMP AS {name}")

                elif t.lower() == "default":
                    select_lines.append(f"        NULL AS {name}")

                else:
                    select_lines.append(f"        {t} AS {name}")

            else:
                select_lines.append(f"        {name}")

        # ✅ JOIN FROM TABLE-LEVEL STTM (NO CHANGE)
        join_clause = self.sttm.get("common_join") or ""

        return ",\n".join(select_lines), join_clause

    def generate(self) -> str:
        database = self.sttm["target"]["database"]
        table = self.sttm["target"]["table"]

        bronze_table = self.main_table
        bronze_short = bronze_table.split(".")[-1]

        source_db = self.sttm.get("source_db", "not provided")

        select_sql, join_clause = self.build_transformation_sql()

        # ✅ SAME CORRECT LOGIC (unchanged)
        from_clause = f"{bronze_table} S"
        if join_clause:
            from_clause = f"{bronze_table} S\n{join_clause}"

        header = f"""# Databricks notebook source
# MAGIC %md
# MAGIC ## Overview
# MAGIC Enterprise STTM Generated Notebook
# MAGIC
# MAGIC ### Source and Target Info
# MAGIC | Source DB | Source Table | Target DB | Target Table |
# MAGIC |-----------|--------------|-----------|--------------|
# MAGIC | {source_db} | {bronze_short} | {database} | {table} |
"""

        read_section = f"""
# COMMAND ----------

# MAGIC %md ## Read Source Tables

base_df = spark.sql(f\"\"\"
SELECT *
FROM {bronze_table}
\"\"\")
"""

        transform = f"""
# COMMAND ----------

# MAGIC %md ## Transformation

transformed_df = spark.sql(f\"\"\"
SELECT
{select_sql}
FROM {from_clause}
\"\"\")
"""

        final_select = """
# COMMAND ----------

# MAGIC %md ## Final Selection

gold_final_df = transformed_df.select("*")
"""

        load = f"""
# COMMAND ----------

# MAGIC %md ## Load to Target

gold_final_df.write \\
    .format("delta") \\
    .mode("append") \\
    .saveAsTable("{database}.{table}")

print("Load completed for {database}.{table}")
"""

        return header + read_section + transform + final_select + load
