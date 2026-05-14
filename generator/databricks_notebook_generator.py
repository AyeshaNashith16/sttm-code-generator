import re


class DatabricksNotebookGenerator:
    """
    ✅ ENTERPRISE GENERATOR (FINAL & FIXED)
    - NO HTML entities ✅
    - Bronze table comes from STTM metadata ✅
    - Same table used in Header, Read, Transform ✅
    """

    def __init__(self, sttm_output: dict):
        self.sttm = sttm_output

        # ✅ SOURCE TABLES COME FROM AGENT (NOT SQL PARSING)
        self.source_tables = sttm_output.get("source_tables", [])

        if not self.source_tables:
            # final safe fallback (never hardcode MARA again)
            self.source_tables = ["tbl_unknown_source"]

        self.main_table = self.source_tables[0]

    # ✅ BUILD SELECT SQL ONLY (no table detection here)
    def build_transformation_sql(self):
        select_lines = []
        join_clause = ""

        for col in self.sttm["all_columns"]:
            name = col["name"]
            transform = col.get("transform_sql")
            join = col.get("join_sql")

            if transform:
                t = transform.strip().rstrip(",")

                # ✅ CLEAN TEXT
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

            # ✅ JOIN (if present)
            if join and not join_clause:
                j = re.sub(r"\s+", " ", join.strip())
                if j.startswith("INNER") and not j.startswith("INNER JOIN"):
                    j = j.replace("INNER", "INNER JOIN", 1)
                join_clause = j.replace(" ON ", "\n    ON ").replace(" AND ", "\n    AND ")

        return ",\n".join(select_lines), join_clause

    # ✅ MAIN GENERATOR
    def generate(self) -> str:

        database = self.sttm["target"]["database"]
        table = self.sttm["target"]["table"]

        # ✅ TABLE NAME (short)
        table_name_only = (
            self.main_table.split(".")[-1]
            if "." in self.main_table
            else self.main_table
        )

        select_sql, join_clause = self.build_transformation_sql()

        # ✅ HEADER (FIXED)
        header = f"""# Databricks notebook source
# MAGIC %md
# MAGIC ## Overview
# MAGIC Enterprise STTM Generated Notebook
# MAGIC
# MAGIC ### Source and Target Info
# MAGIC | Source DB | Source Table | Target DB | Target Table |
# MAGIC |-----------|--------------|-----------|--------------|
# MAGIC | not provided | {table_name_only} | {database} | {table} |
"""

        imports = """
# COMMAND ----------

from pyspark.sql.window import Window
from datetime import datetime
import json
"""

        config = """
# COMMAND ----------

dbutils.widgets.text("task_name","","")
task_name = dbutils.widgets.get("task_name")

env = "dev"
"""

        # ✅ READ SOURCE (FIXED)
        read_section = f"""
# COMMAND ----------

# MAGIC %md ## Read Source Tables

base_df = spark.sql(f\"\"\"
SELECT *
FROM {self.main_table}
\"\"\")
"""

        # ✅ TRANSFORMATION (FIXED)
        transform = f"""
# COMMAND ----------

# MAGIC %md ## Transformation

transformed_df = spark.sql(f\"\"\"
SELECT
{select_sql}
FROM {self.main_table} S
{join_clause}
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

print("✅ Load completed for {database}.{table}")
"""

        return (
            header
            + imports
            + config
            + read_section
            + transform
            + final_select
            + load
        )
