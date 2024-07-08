"""Streamlit code for extraction."""

import json

import requests
import streamlit as st

st.set_page_config(
    page_title="OSC Text to JSON Extractor",
    page_icon=":file_folder:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.header("This is the OSC Text to JSON Extractor")
st.subheader(
    "For more details see: \n  https://github.com/os-climate/osc-transformer-presteps"
)
input_file = st.file_uploader(
    "Upload a PDF file", type="pdf", accept_multiple_files=False
)

if input_file is None:
    st.session_state.output = None
else:
    st.info("File uploaded successfully")
    if st.button("Extract data"):
        st.info("Extraction started")
        file_bytes = input_file.getvalue()
        liveness = requests.get(
            url="http://localhost:8000/liveness", proxies={"http": "", "https": ""}
        )
        st.info(f"Liveness Check: {liveness.status_code}")
        file_upload = requests.post(
            url="http://localhost:8000/extract",
            files={"file": (input_file.name, file_bytes)},
            proxies={"http": "", "https": ""},
        )
        if file_upload.status_code == 200:
            result_json = file_upload.json()
            st.json(result_json)
            st.session_state.output = result_json
        else:
            st.error("API request failed")

if st.session_state.output is not None:
    if st.button("Enable download"):
        json_data = json.dumps(st.session_state.output, indent=4)
        st.download_button(
            label="Click here to download",
            data=json_data,
            file_name="result.json",
            mime="text/json",
        )
