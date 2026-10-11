# Small official Python image; "slim" leaves out compilers and docs we don't need.
FROM python:3.13-slim

# Don't write .pyc files, and print logs immediately instead of buffering them.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /code

# Install dependencies first so Docker can cache this layer: it only reruns
# when requirements.txt changes, not on every code change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Run as a non-root user so a bug in the app can't modify the container.
RUN useradd --create-home appuser && chown -R appuser /code
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
