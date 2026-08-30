# Использование легковесного официального образа Python 3.11
FROM python:3.11-slim

# Установка переменных окружения для Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Tashkent

WORKDIR /app

# Установка системных зависимостей и часового пояса
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    sqlite3 \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка Python-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода бота
COPY . .

# Создание директории для базы данных с гарантией персистентности
RUN mkdir -p data/backups

# Запуск бота
CMD ["python", "main.py"]
