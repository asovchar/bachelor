FROM python:3.8.0 as builder

RUN pip install poetry
RUN poetry config virtualenvs.in-project true

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-root --no-interaction

COPY recommender/ ./recommender/
COPY README.md ./
RUN poetry install --no-dev --no-interaction

FROM python:3.8.0-slim

COPY --from=builder /app/ /app/

RUN ln -snf /app/.venv/bin/recommender-* /usr/local/bin/
