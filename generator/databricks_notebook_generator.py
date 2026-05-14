import re


class DatabricksNotebookGenerator:

    def __init__(self, sttm_output: dict):
        self.sttm = sttm_output
        self.base_tables, self.join_tables = self._extract_source_tables()

    # ✅ SOURCE TABLE FIX
    def _extract_source_tables(self):

        base_tables = set()
        join_tables = set()

        for col in self.sttm["all_columns"]:
            transform = col.get("transform_sql", "")
            join = col.get("join_sql", "")

            text = f"{transform} {join}"

            # ✅ FULL TABLES
            full_tables = re.findall(r"uc_[\w\.]+\.tbl_[\w]+", text)

            # ✅ SHORT TABLES ✅ IMPORTANT
            short_tables = re.findall(r"\btbl_[\w]+\b", text, flags=re.IGNORECASE)

            all_tables = list(set(full_tables + short_tables))

            if join and str(join).lower() != "none":
                join_tables.update(all_tables)
            else:
                base_tables.update(all_tables)

        base_tables = base_tables - join_tables

        # ✅ FINAL FIX — NO MARA HARD CODE
        if not base_tables:
            base_tables.add("tbl_unknown_source")

        return list(base_tables), list(join_tables)

    # ✅ BUILD SQL
    def build_transformation_sql(self):
        select_lines = []
        join_clause = ""

        for col in self.sttm["all_columns"]:
            name = col["name"]
            transform = col.get("transform_sql")
            join = col.get("join_sql")

            if transform:
                t = transform.strip().rstrip(",")

                t = re.sub(r"\s+", " ", t)
                t = t.replace("&lt;&gt;", " <> ")

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

            # JOIN
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

        # ✅ ✅ SINGLE SOURCE TABLE USED EVERYWHERE
        main_table = self.base_tables[0]

        # ✅ ✅ TABLE NAME (correct)
        table_name_only = main_table.split(".")[-1] if "." in main_table else main_table

        select_sql, join_clause = self.build_transformation_sql()

        # ✅ ✅ HEADER FIXED
        header = f"""# Databricks notebook source
# MAGIC %md
# MAGIC ## Overview
# MAGIC Enterprise STTM Generated Notebook
# MAGIC
# MAGIC ### Source and Target Info
# MAGIC | Source DB | Source Table | Target DB | Target Table |
# MAGIC |-----------|--------------|-----------|--------------|
# MAGIC | uc_dev_snt_fdn_01.fdn_material_bronze_view | {table_name_only} | {database} | {table} |
"""

        # ✅ IMPORTS
        imports = """
# COMMAND ----------

from pyspark.sql.window import Window
from datetime import datetime
import json
"""

        # ✅ CONFIG
        config = """
# COMMAND ----------

dbutils.widgets.text("task_name","","")
task_name = dbutils.widgets.get("task_name")

env = "dev"
"""

        # ✅ ✅ READ SECTION (FIXED)
        read_section = f"""
# COMMAND ----------

# MAGIC %md ## Read Source Tables

base_df = spark.sql(f\"\"\"
SELECT *
FROM {main_table}
\"\"\")
"""

        # ✅ ✅ TRANSFORMATION (FIXED)
        transform = f"""
# COMMAND ----------

# MAGIC %md ## Transformation

transformed_df = spark.sql(f\"\"\"
SELECT
{select_sql}
FROM {main_table} S
{join_clause}
\"\"\")
"""

        # ✅ FINAL
        final_select = f"""
# COMMAND ----------

# MAGIC %md ## Final Selection

gold_final_df = transformed_df.select("*")
"""

        # ✅ LOAD
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
