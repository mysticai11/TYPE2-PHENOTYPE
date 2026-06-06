FROM python:3.11-slim

WORKDIR /app

# Copy the entire project context to maintain absolute imports (src_code is outside backend)
COPY ./backend /app/backend
COPY ./src_code /app/src_code
COPY ./models /app/models
COPY ./data /app/data

WORKDIR /app/backend

# Install dependencies
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 8000

# Command to run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
