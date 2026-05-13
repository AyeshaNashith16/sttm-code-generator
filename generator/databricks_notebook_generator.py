import re


class DatabricksNotebookGenerator:
    """
    ✅ ENTERPRISE GENERATOR
    - Dynamic source detection ✅
    - Temp view-based ETL ✅
    - Multi-table support ✅
    - Gold-like structure ✅
    """

    def __init__(self, sttm_output: dict):
        self.sttm = sttm_output
        self.base_tables, self.join_tables = self._extract_source_tables()

    # ✅ SOURCE TABLE EXTRACTION
    def _extract_source_tables(self):
        base_tables = set()
        join_tables = set()

        for col in self.sttm["all_columns"]:
            transform = col.get("transform_sql")
            join = col.get("join_sql")

            # JOIN tables
            if join and str(join).lower() != "none":
                tables = re.findall(r"uc_[\w\.]+\.tbl_[\w]+", join)
                join_tables.update([t.strip() for t in tables])

            # BASE tables
            if transform:
                tables = re.findall(r"uc_[\w\.]+\.tbl_[\w]+", transform)
                base_tables.update([t.strip() for t in tables])

        # remove overlap
        base_tables = base_tables - join_tables

        # fallback
        if not base_tables:
            base_tables.add(
                "uc_dev_snt_fdn_01.fdn_material_bronze_view.tbl_SNT_SUPP_DDHPIRTEURMARA"
            )

        return list(base_tables), list(join_tables)

    # ✅ BUILD SELECT SQL
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
            if join and join_clause == "":
                j = re.sub(r"\s+", " ", join.strip())

                if j.startswith("INNER") and not j.startswith("INNER JOIN"):
                    j = j.replace("INNER", "INNER JOIN", 1)

                join_clause = j.replace(" ON ", "\n    ON ").replace(" AND ", "\n    AND ")

        return ",\n".join(select_lines), join_clause

    # ✅ MAIN GENERATOR
    def generate(self) -> str:

        database = self.sttm["target"]["database"]
        table = self.sttm["target"]["table"]

        main_table = self.base_tables[0]
        table_name_only = main_table.split(".")[-1]

        select_sql, join_clause = self.build_transformation_sql()

        # ✅ HEADER
        header = f"""# Databricks notebook source
# MAGIC %md
# MAGIC ## Overview
# MAGIC Enterprise STTM Generated Notebook
# MAGIC
# MAGIC ### Source & Target
# MAGIC | Source Table | Target Table |
# MAGIC |--------------|--------------|
# MAGIC | {table_name_only} | {table} |
"""

        # ✅ IMPORTS (closer to Gold)
        imports = """
# COMMAND ----------

from pyspark.sql.window import Window
from datetime import datetime
import json
"""

        # ✅ PARAMS
        config = """
# COMMAND ----------

dbutils.widgets.text("task_name","","")
task_name = dbutils.widgets.get("task_name")

env = "dev"
"""

        # ✅ ETL PIPELINE (GOLD STYLE)
        transform = f"""
# COMMAND ----------

# MAGIC %md ## ETL Code Section

# STEP 1: Load Source Table
{table_name_only}_df = spark.sql(f\"\"\"
SELECT *
FROM {main_table}
\"\"\")
{table_name_only}_df.createOrReplaceTempView("temp_vw_{table_name_only}")


# COMMAND ----------

# STEP 2: Apply Transformation
transformed_df = spark.sql(f\"\"\"
SELECT
{select_sql}
FROM temp_vw_{table_name_only} S
{join_clause}
\"\"\")
transformed_df.createOrReplaceTempView("temp_vw_transformed")


# COMMAND ----------

# STEP 3: Final Selection
gold_final_df = spark.sql(f\"\"\"
SELECT *
FROM temp_vw_transformed
\"\"\")
"""

        # ✅ LOAD (simple version)
        load = f"""
# COMMAND ----------

# MAGIC %md ## Load to Target

gold_final_df.write \\
    .format("delta") \\
    .mode("append") \\
    .saveAsTable("{database}.{table}")

print("✅ Load completed for {database}.{table}")
"""

        return header + imports + config + transform + load