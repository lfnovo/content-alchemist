import streamlit as st
from dotenv import load_dotenv
import asyncio
import content_core as cc
import os
import tempfile

load_dotenv()

st.title("Composer")

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

uploaded_files = st.file_uploader(
    "Choose a CSV file", accept_multiple_files=True
)

engine = st.radio("Engine", ["legacy", "docling"])
output_format = "markdown"

with tempfile.TemporaryDirectory() as tmp_dir:
    for uploaded_file in uploaded_files if uploaded_files else []:
        if uploaded_file.name not in st.session_state.processed_files:
            tmp_file_path = os.path.join(tmp_dir, uploaded_file.name)
            with open(tmp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            result = asyncio.run(cc.extract(dict(file_path=tmp_file_path, output_format=output_format, engine=engine)))
            st.session_state.uploaded_files.append(result)
            st.session_state.processed_files.add(uploaded_file.name)

for file in st.session_state.uploaded_files:
    with st.expander(file.title):
        st.json(file.metadata)
        st.markdown(file.content)