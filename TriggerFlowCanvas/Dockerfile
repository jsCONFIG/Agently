FROM node:18 AS frontend-builder

WORKDIR /workspace
COPY TriggerFlowCanvas/frontend ./frontend
RUN cd frontend \
    && npm install \
    && npm run build

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .
COPY --from=frontend-builder /workspace/frontend/dist TriggerFlowCanvas/frontend/dist
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

EXPOSE 8000
CMD ["python", "-m", "TriggerFlowCanvas.backend.main"]
