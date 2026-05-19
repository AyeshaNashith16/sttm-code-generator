import re


class DatabricksNotebookGenerator:
    """
    FINAL ENTERPRISE GENERATOR
    """

    def __init__(self, sttm_output: dict):
        self.sttm = sttm_output

        self.source_tables = sttm_output.get("source_tables", [])
        if not self.source_tables:
            raise ValueError("Bronze table not provided by Agent")

        self.main_table = self.source_tables[0]

    def build_transformation_sql(self):
        select_lines = []
        join_clause = ""

        # ✅ Main loop
        for col in self.sttm["all_columns"]:
            name = col["name"]
            transform = col.get("transform_sql")
            join = col.get("join_sql")

            # ✅ Transform logic
            if transform:
                t = transform.strip().rstrip(",")
                t = re.sub(r"\s+", " ", t)
                t = t.replace("&amp;lt;&amp;gt;", " <> ")

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

            # ✅ ✅ JOIN LOGIC
            if join and str(join).lower() != "none" and not join_clause:
                j = re.sub(r"\s+", " ", join.strip())

                if j.startswith("INNER") and not j.startswith("INNER JOIN"):
                    j = j.replace("INNER", "INNER JOIN", 1)

                on_part = ""
                table_part = j
                alias = ""

                if " ON " in j:
                    parts = j.split(" ON ")
                    table_part = parts[0]
                    on_part = parts[1]

                # ✅ Extract alias (S1, S2…)
                alias_match = re.search(r"\b(S\d+)\.", on_part)
                if alias_match:
                    alias = alias_match.group(1)

                # ✅ Add alias if missing
                if alias and f" {alias}" not in table_part:
                    j = f"{table_part} {alias} ON {on_part}"

                # ✅ Format JOIN nicely
                join_clause = j.replace(" ON ", "\n    ON ").replace(" AND ", "\n    AND ")

        return ",\n".join(select_lines), join_clause

    def generate(self) -> str:
        database = self.sttm["target"]["database"]
        table = self.sttm["target"]["table"]

        bronze_table = self.main_table
        bronze_short = bronze_table.split(".")[-1]
        source_db = bronze_schema
        

        select_sql, join_clause = self.build_transformation_sql()

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

print("✅ Load completed for {database}.{table}")
"""

        return header + read_section + transform + final_select + load
