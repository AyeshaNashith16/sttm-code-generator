import streamlit as st
import tempfile
import pandas as pd

from parser.excel_reader import STTMExcelParser
from agent.sttm_reasoning_agent import STTMReasoningAgent
from generator.databricks_notebook_generator import DatabricksNotebookGenerator


st.set_page_config(page_title="STTM Code Generator", layout="centered")

st.title("🚀 STTM → Databricks Notebook Generator")
st.markdown("Upload your STTM Excel file to generate a Databricks notebook.")

# ============================
# FILE UPLOAD
# ============================
uploaded_file = st.file_uploader("📂 Upload Excel File", type=["xlsx"])

sheet_name = None

if uploaded_file is not None:

    st.success("✅ File uploaded successfully")

    # ✅ Save temp file FIRST (safe approach)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded_file.read())
        temp_file_path = tmp.name

    try:
        # ✅ Use FILE PATH (not bytes) → fixes your error
        excel_file = pd.ExcelFile(temp_file_path)
        sheet_list = excel_file.sheet_names

        # ✅ Dropdown
        sheet_name = st.selectbox("📄 Select Sheet", sheet_list)

        # ============================
        # GENERATE BUTTON
        # ============================
        if st.button("⚡ Generate Notebook"):

            try:
                # ✅ Use selected sheet
                parser = STTMExcelParser(temp_file_path, sheet_name=sheet_name)
                sttm_metadata = parser.read()

                agent = STTMReasoningAgent(sttm_metadata)
                final_output = agent.analyze()

                generator = DatabricksNotebookGenerator(final_output)
                notebook_code = generator.generate()

                st.success("✅ Notebook generated successfully!")

                # ✅ Preview
                with st.expander("🔍 Preview Notebook Code"):
                    st.code(notebook_code[:3000], language="python")

                # ✅ Download
                table_name = final_output["target"]["table"]
                file_name = f"{table_name}.py"

                st.download_button(
                    label="📥 Download Notebook",
                    data=notebook_code,
                    file_name=file_name,
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"❌ Error during generation:\n{str(e)}")

    except Exception as e:
        st.error(f"❌ Error reading Excel file:\n{str(e)}")