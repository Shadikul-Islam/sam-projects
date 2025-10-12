# Use lightweight Python 3.10 image
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl bash && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /srv/pytorch/data/raw
VOLUME ["/srv/pytorch/data/raw"]
EXPOSE 8088
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]
