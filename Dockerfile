# Gunakan base image Python yang ringan
FROM python:3.10-slim

# Set working directory di dalam container
WORKDIR /app

# Atur environment variables untuk Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Port default Hugging Face Spaces adalah 7860
ENV APP_PORT=7860 

# Install dependensi sistem yang mungkin dibutuhkan oleh PyTorch dll
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Salin file requirements terlebih dahulu untuk caching docker
COPY requirements.txt .

# Install dependensi Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode proyek ke dalam container
COPY . .

# Buat direktori yang dibutuhkan agar tidak error
RUN mkdir -p artifacts/reports artifacts/predictions artifacts/evaluations artifacts/logs models data/raw data/processed data/sample

# Expose port yang akan digunakan
EXPOSE 7860

# Jalankan server FastAPI menggunakan uvicorn
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "7860"]
