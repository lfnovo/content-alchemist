
build-docs:
	repomix . --include "**/*.py,**/*.yaml" --compress --style xml -o ai_docs/core.xml

ui:
	uv run streamlit run src/content_composer/app.py