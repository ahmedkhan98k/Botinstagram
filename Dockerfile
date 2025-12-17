# استخدام Python slim image أصلية
FROM python:3.11-slim-bookworm

WORKDIR /app

# تحديث النظام وتثبيت أدوات بناء ضرورية
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ الملفات
COPY requirements.txt .
COPY . .

# تثبيت المكتبات
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "bot.py"]
