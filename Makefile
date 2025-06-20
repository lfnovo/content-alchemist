
.PHONY: tag build-docs ui

tag:
	@version=$$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'); \
	echo "Creating tag v$$version"; \
	git tag "v$$version"; \
	git push origin "v$$version"



build-docs:
	repomix . --include "**/*.py,**/*.yaml" --compress --style xml -o ai_docs/core.xml

ui:
	uv run streamlit run src/content_composer/app.py