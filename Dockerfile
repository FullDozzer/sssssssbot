FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY silxnce ./silxnce

ENV DB_PATH=/data/silxnce.db
RUN mkdir -p /data
VOLUME /data

CMD ["python", "-m", "silxnce"]
