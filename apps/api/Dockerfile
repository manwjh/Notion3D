FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends openscad \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY app ./app
RUN pip install --no-cache-dir -e .

ENV NOTION3D_DATA_DIR=/app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
