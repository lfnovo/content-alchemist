import asyncio
import glob
import os

import nest_asyncio
import streamlit as st
from loguru import logger

from content_composer.langgraph_workflow import execute_workflow
from content_composer.recipe_parser import RecipeParseError, parse_recipe

nest_asyncio.apply()
st.title("Content Composer")

# Scan recipes directory for yaml files and create dropdown


def render_output(content, key=None):
    if key:
        st.markdown(f"### {key}")
    if isinstance(content, list):
        for item in content:
            render_output(item)
    elif isinstance(content, dict):
        st.json(content)
    elif isinstance(content, str):
        # Check if it looks like a file path and if the file exists
        if os.path.exists(content):
            _, ext = os.path.splitext(content)
            ext = ext.lower()
            is_audio = False
            if ext in [".wav", ".mp3", ".ogg", ".aac", ".flac", ".opus"]:
                is_audio = True
                try:
                    with open(content, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    st.audio(audio_bytes, format=f'audio/{ext.strip(".")}')
                except Exception as e:
                    st.error(f"Error playing audio file {content}: {e}")
                    logger.error(f"Error playing audio file {content}: {e}")

            # Always offer download button for files
            try:
                with open(content, "rb") as fp:
                    btn_label = (
                        f"Download {os.path.basename(content)} ({ext.strip('.')})"
                    )
                    st.download_button(
                        label=btn_label,
                        data=fp,
                        file_name=os.path.basename(content),
                        # mime will be inferred or can be set if known
                    )
            except Exception as e:
                st.error(f"Error providing download for file {content}: {e}")
                logger.error(f"Error providing download for file {content}: {e}")

        else:
            # If it's a string but not an existing file path, treat as markdown
            st.markdown(content)
    else:
        # Fallback for other data types (e.g., lists, numbers)
        st.markdown(f"```\n{str(content)}\n```")


recipe_files = glob.glob("recipes/*.yaml")
recipe_files.extend(glob.glob("recipes/*.json"))
recipe_names = sorted([os.path.basename(path) for path in recipe_files])
selected_recipe = st.selectbox("Select a recipe", recipe_names, index=0)
recipe_path = os.path.join("recipes", selected_recipe)

# Global overrides for model configuration
st.sidebar.subheader("Global Model Overrides (Optional)")
override_provider = st.sidebar.text_input("Override Model Provider")
override_model_name = st.sidebar.text_input("Override Model Name")

if recipe_path:
    try:
        recipe = parse_recipe(recipe_path)
    except RecipeParseError as e:
        st.error(f"Failed to load recipe: {e}")
        st.stop()
    st.subheader(recipe.name)
    inputs = {}
    if recipe.user_inputs:
        assert recipe.user_inputs is not None
        for ui in recipe.user_inputs:
            if ui.type == "text":
                inputs[ui.id] = st.text_area(ui.label, value=ui.default, key=ui.id)
            elif ui.type == "string":
                inputs[ui.id] = st.text_input(ui.label, value=ui.default, key=ui.id)
            elif ui.type == "int":
                inputs[ui.id] = st.number_input(
                    ui.label,
                    value=ui.default,
                    key=ui.id,
                    step=1,
                )
            elif ui.type == "float":
                inputs[ui.id] = st.number_input(ui.label, value=ui.default, key=ui.id)
            elif ui.type == "bool":
                inputs[ui.id] = st.checkbox(ui.label, value=ui.default, key=ui.id)
            elif ui.type == "file":
                # Check if recipe name suggests multiple files
                if "multi" in recipe.name.lower() or "multiple" in recipe.name.lower():
                    uploaded_files = st.file_uploader(
                        ui.label, key=ui.id, accept_multiple_files=True
                    )
                    if uploaded_files:
                        inputs[ui.id] = uploaded_files
                    else:
                        inputs[ui.id] = []
                else:
                    uploaded_file = st.file_uploader(ui.label, key=ui.id)
                    if uploaded_file is not None:
                        inputs[ui.id] = uploaded_file
                    else:
                        inputs[ui.id] = None
            elif ui.type == "literal":
                inputs[ui.id] = st.selectbox(
                    ui.label,
                    options=ui.literal_values,
                    key=ui.id,
                    index=ui.literal_values.index(ui.default)
                    if ui.default
                    and ui.literal_values
                    and ui.default in ui.literal_values
                    else 0,
                )
            elif ui.type == "url":
                inputs[ui.id] = st.text_input(
                    ui.label, value=ui.default, key=ui.id + "_url"
                )
    if st.button("Generate"):
        with st.spinner("Generating..."):
            try:
                effective_override_provider = (
                    override_provider if override_provider else None
                )
                effective_override_model_name = (
                    override_model_name if override_model_name else None
                )

                outputs = asyncio.run(
                    execute_workflow(
                        recipe,
                        inputs,
                        override_provider=effective_override_provider,
                        override_model_name=effective_override_model_name,
                    )
                )
                st.subheader("Results")
                for key, content in outputs.items():
                    render_output(content, key)
            except Exception as e:
                st.error(f"Execution error: {e}")
                st.exception(e)
