FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir influxdb-client==1.48.0
COPY notifier.py telegram_test.py ./
CMD ["python", "-u", "notifier.py"]
