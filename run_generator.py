import sys
import os

from parser.excel_reader import STTMExcelParser
from agent.sttm_reasoning_agent import STTMReasoningAgent
from generator.databricks_notebook_generator import DatabricksNotebookGenerator


def generate_notebook(input_file: str, custom_output: str = None):

    print("\n🚀 Starting STTM → Notebook generation...\n")

    # ============================
    # STEP 1 — Parse Excel
    # ============================
    parser = STTMExcelParser(input_file, sheet_name="Ayesha")
    sttm_metadata = parser.read()
    print("✅ Excel parsed successfully")

    # ============================
    # STEP 2 — Agent processing
    # ============================
    agent = STTMReasoningAgent(sttm_metadata)
    final_output = agent.analyze()
    print("✅ Agent processing completed")

    # ============================
    # STEP 3 — Generate notebook
    # ============================
    generator = DatabricksNotebookGenerator(final_output)
    notebook_code = generator.generate()
    print("✅ Notebook generated")

    # ============================
    # STEP 4 — Save file
    # ============================
    table_name = final_output["target"]["table"]

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # ✅ Use custom output if provided
    if custom_output:
        output_path = custom_output
    else:
        output_path = os.path.join(output_dir, f"{table_name}.py")

    # Write file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(notebook_code)

    print(f"\n✅ Notebook saved at: {output_path}")


# ============================
# CLI ENTRY POINT
# ============================
if __name__ == "__main__":

    # ✅ NEW USAGE FORMAT
    if len(sys.argv) < 2:
        print("❌ Usage: python run_generator.py <input_excel_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]

    # ✅ Optional output file
    output_file = None
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]

    # ✅ Validate input file
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        sys.exit(1)

    # ✅ Run generator
    generate_notebook(input_file, output_file)