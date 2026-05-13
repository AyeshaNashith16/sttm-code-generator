from parser.excel_reader import STTMExcelParser
from agent.sttm_reasoning_agent import STTMReasoningAgent
from generator.databricks_notebook_generator import DatabricksNotebookGenerator


if __name__ == "__main__":

    # ============================
    # STEP 1 — Parse Excel
    # ============================
    parser = STTMExcelParser(
        "input/work_3.xlsx",   # ✅ make sure filename is correct
        sheet_name="Ayesha"
    )

    sttm_metadata = parser.read()

    print("\n===== PARSER OUTPUT =====\n")
    print(sttm_metadata)


    # ============================
    # STEP 2 — Agent Processing
    # ============================
    agent = STTMReasoningAgent(sttm_metadata)
    final_output = agent.analyze()

    print("\n===== AGENT OUTPUT =====\n")
    for col in final_output["all_columns"]:
        print(f"{col['name']} → {col.get('transform_sql')}")


    # ============================
    # STEP 3 — Notebook Generator
    # ============================
    generator = DatabricksNotebookGenerator(final_output)
    notebook_code = generator.generate()

    print("\n===== GENERATED NOTEBOOK =====\n")
    print(notebook_code)
