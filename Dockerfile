FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    python3-dev \
    ca-certificates \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY . .

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

RUN if [ -f "requirements.txt" ]; then \
        python -m pip install --no-cache-dir -r requirements.txt; \
    elif [ -f "requirements.txt" ]; then \
        python -m pip install --no-cache-dir -r "requirements.txt"; \
    else \
        echo "ERROR: requirements.txt not found"; \
        exit 1; \
    fi

RUN mkdir -p /app/user_data

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
