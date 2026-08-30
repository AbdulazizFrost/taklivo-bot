#!/usr/bin/env bash
# Скрипт быстрого деплоя бота TAKLIVO на сервер Linux (Ubuntu / Debian)

set -e

echo "🚀 Начинаем установку TAKLIVO Bot на сервере..."

# Проверка Docker
if command -v docker &> /dev/null && command -v docker compose &> /dev/null; then
    echo "🐳 Запуск через Docker Compose..."
    mkdir -p data/backups
    docker compose down || true
    docker compose up -d --build
    echo "✅ Бот успешно запущен в фоновом режиме через Docker Compose!"
    docker compose ps
    exit 0
fi

# Если Docker не установлен — стандартная установка Python venv + Systemd
echo "🐍 Настройка через Python venv..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv sqlite3

mkdir -p data/backups

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Установка и запуск systemd службы
CURRENT_DIR=$(pwd)
sed -i "s|/var/www/taklivo_bot|$CURRENT_DIR|g" taklivo.service
sudo cp taklivo.service /etc/systemd/system/taklivo.service
sudo systemctl daemon-reload
sudo systemctl enable taklivo
sudo systemctl restart taklivo

echo "✅ Бот успешно установлен и запущен как служба systemd (taklivo)!"
sudo systemctl status taklivo --no-pager
