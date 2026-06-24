FROM python:3.12-slim

# ຕັ້ງ working directory
WORKDIR /app

# ຕິດຕັ້ງ system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ຕິດຕັ້ງ Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# ສ້າງ folders ທີ່ຈຳເປັນ
RUN mkdir -p uploads static templates

# Expose port
EXPOSE 8000

# Run server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
