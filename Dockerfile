FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

RUN mkdir -p data/uploads data/backups data/cv data/logs reports outputs/tailored_cvs outputs/applications

EXPOSE 8501 8081

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8081/health')" || exit 1

CMD ["bash", "-lc", "python -m src.healthcheck 8081 & streamlit run app/Home.py --server.port=8501 --server.address=0.0.0.0"]
