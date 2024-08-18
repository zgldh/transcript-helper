FROM python:3.9.19-slim-bullseye

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ffmpeg \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

ADD main.py /app/main.py
ADD funasr_wss_client.py /app/funasr_wss_client.py

ENTRYPOINT ["python", "/app/main.py"]