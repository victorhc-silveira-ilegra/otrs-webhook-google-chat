FROM python:3.13-slim

WORKDIR /app
COPY app/pyproject.toml app/README.md app/requirements.txt ./
COPY app/src ./src
RUN pip install --no-cache-dir .

ENV GCHAT_WEBHOOK_URL=http://mock-webhook:8080/v1/spaces/POC/messages
ENV HTTP_TIMEOUT_SECONDS=10

CMD ["sh", "-c", "echo 'notifier ready: otrs-gchat-alert disponivel'; exec tail -f /dev/null"]
