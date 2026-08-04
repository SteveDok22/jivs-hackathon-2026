FROM python:3.12-slim

WORKDIR /code

# Install dependencies first — this layer is cached until pyproject.toml changes,
# so rebuilds after code edits take seconds, not minutes.
COPY pyproject.toml .
RUN pip install --no-cache-dir .
# Presidio needs a spaCy model for name detection. Pin the small model
# (~12 MB) — installed as a wheel so no network download at runtime.
RUN python -m spacy download en_core_web_sm

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
