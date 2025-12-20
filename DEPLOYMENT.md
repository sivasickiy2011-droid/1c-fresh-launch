# Инструкция по развертыванию проекта на CentOS 9 Stream

## Подготовка сервера

### 1. Обновление системы
```bash
sudo dnf update -y
sudo dnf install -y git curl wget
```

### 2. Установка Docker
```bash
# Удаление старых версий (если есть)
sudo dnf remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine

# Установка необходимых пакетов
sudo dnf install -y dnf-plugins-core

# Добавление репозитория Docker
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# Установка Docker
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Запуск Docker
sudo systemctl start docker
sudo systemctl enable docker

# Проверка установки
sudo docker --version
sudo docker compose version
```

### 3. Настройка пользователя для Docker (опционально)
```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Подготовка проекта

### 1. Клонирование репозитория
```bash
cd /opt
sudo git clone <URL_ВАШЕГО_РЕПОЗИТОРИЯ> webapp
cd webapp
```

### 2. Создание Dockerfile
Создайте файл `Dockerfile` в корне проекта:

```dockerfile
# Этап сборки
FROM node:20-alpine AS builder

WORKDIR /app

# Копирование файлов зависимостей
COPY package.json package-lock.json* ./

# Установка зависимостей
RUN npm ci

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Продакшен этап
FROM nginx:alpine

# Копирование собранных файлов
COPY --from=builder /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 3. Создание конфигурации Nginx
Создайте файл `nginx.conf`:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;

    # SPA роутинг
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Кэширование статических файлов
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Безопасность
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

### 4. Создание docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: webapp
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./logs:/var/log/nginx
    environment:
      - NODE_ENV=production
```

### 5. Создание .dockerignore
```
node_modules
.git
.gitignore
*.md
.env*
dist
backend
db_migrations
```

## Развертывание

### 1. Сборка и запуск контейнера
```bash
cd /opt/webapp

# Сборка образа
sudo docker compose build

# Запуск контейнера
sudo docker compose up -d

# Проверка статуса
sudo docker compose ps
sudo docker compose logs -f
```

### 2. Проверка работы
```bash
curl http://localhost
```

## Настройка HTTPS (опционально)

### Использование Let's Encrypt с Certbot

1. Установите Certbot:
```bash
sudo dnf install -y certbot python3-certbot-nginx
```

2. Обновите `docker-compose.yml`:
```yaml
version: '3.8'

services:
  web:
    build: .
    container_name: webapp
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./logs:/var/log/nginx
      - ./certs:/etc/nginx/certs
      - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf
```

3. Создайте `nginx-ssl.conf` с поддержкой SSL (после получения сертификата).

## Управление контейнером

```bash
# Остановка
sudo docker compose down

# Перезапуск
sudo docker compose restart

# Обновление (после изменений в коде)
git pull
sudo docker compose down
sudo docker compose build
sudo docker compose up -d

# Просмотр логов
sudo docker compose logs -f

# Очистка старых образов
sudo docker system prune -a
```

## Автоматическое обновление

Создайте скрипт `/opt/webapp/update.sh`:

```bash
#!/bin/bash
cd /opt/webapp
git pull
docker compose down
docker compose build
docker compose up -d
```

Сделайте его исполняемым:
```bash
chmod +x /opt/webapp/update.sh
```

## Настройка файрвола

```bash
# Разрешение HTTP/HTTPS
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Мониторинг

```bash
# Использование ресурсов
sudo docker stats

# Логи в реальном времени
sudo docker compose logs -f web

# Проверка состояния контейнера
sudo docker inspect webapp
```

## Резервное копирование

```bash
# Создание backup скрипта
cat > /opt/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/webapp_$DATE.tar.gz /opt/webapp --exclude=node_modules --exclude=.git
# Удаление backup'ов старше 7 дней
find $BACKUP_DIR -name "webapp_*.tar.gz" -mtime +7 -delete
EOF

chmod +x /opt/backup.sh

# Добавление в cron (ежедневно в 3:00)
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/backup.sh") | crontab -
```

## Важные замечания

1. **Backend функции**: Этот проект использует облачные функции из poehali.dev. Они останутся на нашей инфраструктуре и будут доступны по URL из `backend/func2url.json`.

2. **База данных**: PostgreSQL база находится на серверах poehali.dev. Если нужна локальная БД, добавьте PostgreSQL в `docker-compose.yml`.

3. **Секреты**: Переменные окружения (Telegram Bot Token, Bitrix Webhook) используются backend-функциями на poehali.dev. Для фронтенда дополнительные секреты не требуются.

4. **Домен**: После настройки DNS запустите Certbot для получения SSL сертификата:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

## Устранение неполадок

### Контейнер не запускается
```bash
sudo docker compose logs web
sudo docker inspect webapp
```

### Порт уже занят
```bash
sudo netstat -tulpn | grep :80
sudo systemctl stop httpd  # Если установлен Apache
```

### Недостаточно места
```bash
df -h
sudo docker system prune -a --volumes
```

## Поддержка

Если возникли вопросы по развертыванию, обращайтесь в Telegram: https://t.me/+QgiLIa1gFRY4Y2Iy
