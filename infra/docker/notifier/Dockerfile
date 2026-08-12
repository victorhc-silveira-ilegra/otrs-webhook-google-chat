FROM python:3.13-slim

WORKDIR /app
COPY app/pyproject.toml app/README.md app/requirements.txt ./
COPY app/src ./src
RUN pip install --no-cache-dir .

ENV WEBHOOK_URL=http://mock-webhook:8080/v1/spaces/POC/messages
ENV HTTP_TIMEOUT_SECONDS=10

CMD ["tail", "-f", "/dev/null"]
