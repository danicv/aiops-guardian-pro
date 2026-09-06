FROM python:3.11-slim
WORKDIR /app
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY mcp-server .
EXPOSE 8001
CMD ["uvicorn", "http_bridge:app", "--host", "0.0.0.0", "--port", "8001"]
