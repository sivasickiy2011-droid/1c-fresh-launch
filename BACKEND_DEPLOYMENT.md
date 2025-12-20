# Инструкция по переносу Backend-функций

## Обзор архитектуры

В вашем проекте есть 2 backend-функции:
1. **telegram-send** - отправка уведомлений в Telegram
2. **bitrix-create-deal** - создание сделок в Bitrix24 CRM

Эти функции можно развернуть несколькими способами:

## Вариант 1: Docker контейнер с Flask API (Рекомендуется)

Этот вариант создает единый API сервер для всех функций.

### 1. Создание структуры проекта

```bash
cd /opt/webapp
mkdir -p backend-api
cd backend-api
```

### 2. Создание Flask приложения

Создайте файл `app.py`:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any

app = Flask(__name__)
CORS(app)

class Context:
    def __init__(self, request_id: str):
        self.request_id = request_id

def telegram_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''Универсальная отправка уведомлений в Telegram'''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    body_data = json.loads(event.get('body', '{}'))
    message_type: str = body_data.get('message_type', 'form')
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Telegram credentials not configured'}),
            'isBase64Encoded': False
        }
    
    if message_type == 'consent':
        user_id = body_data.get('user_id', 'unknown')
        action = body_data.get('action', 'accepted')
        
        text = f"🔔 Новое событие: Согласие на обработку данных\n\n"
        text += f"👤 ID пользователя: {user_id}\n"
        text += f"✅ Действие: {action}\n"
        text += f"🕐 Запрос ID: {context.request_id}"
    else:
        name: str = body_data.get('name', '')
        phone: str = body_data.get('phone', '')
        message: str = body_data.get('message', '')
        source: str = body_data.get('source', 'Веб-сайт')
        
        if not name or not phone:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'Имя и телефон обязательны'}),
                'isBase64Encoded': False
            }
        
        text = f"""🔔 <b>Новая заявка с сайта</b>

👤 <b>Имя:</b> {name}
📞 <b>Телефон:</b> {phone}"""
        
        if message:
            text += f"\n💬 <b>Сообщение:</b> {message}"
        
        text += f"""
📍 <b>Источник:</b> {source}
📅 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"""
    
    telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(telegram_url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('ok'):
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True, 'message': 'Notification sent'}),
                    'isBase64Encoded': False
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Telegram API error', 'details': result}),
                    'isBase64Encoded': False
                }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }

def bitrix_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''Create deal in Bitrix24 CRM from website forms'''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    body_data = json.loads(event.get('body', '{}'))
    
    name = body_data.get('name', '')
    phone = body_data.get('phone', '')
    email = body_data.get('email', '')
    company = body_data.get('company', '')
    message = body_data.get('message', '')
    service = body_data.get('service', 'Не указано')
    source = body_data.get('source', 'Сайт')
    price = body_data.get('price', '')
    
    if not name or not phone:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Name and phone are required'}),
            'isBase64Encoded': False
        }
    
    bitrix_webhook = os.environ.get('BITRIX_WEBHOOK_URL')
    if not bitrix_webhook:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Bitrix webhook not configured'}),
            'isBase64Encoded': False
        }
    
    deal_title = f"Заявка: {service} - {name}"
    deal_data = {
        'fields': {
            'TITLE': deal_title,
            'SOURCE_ID': 'WEB',
            'SOURCE_DESCRIPTION': '1С-FRESH-Lending',
            'COMMENTS': message,
            'CONTACT_ID': None,
        }
    }
    
    if price:
        price_clean = price.replace('₽', '').replace('руб', '').replace('от', '').replace('/месяц', '').strip()
        price_clean = price_clean.replace(',', '').replace(' ', '')
        try:
            price_numeric = float(price_clean)
            deal_data['fields']['OPPORTUNITY'] = price_numeric
            deal_data['fields']['CURRENCY_ID'] = 'RUB'
        except ValueError:
            pass
    
    contact_data = {
        'fields': {
            'NAME': name,
            'TYPE_ID': 'CLIENT',
            'SOURCE_ID': 'WEB',
        }
    }
    
    if phone:
        contact_data['fields']['PHONE'] = [{'VALUE': phone, 'VALUE_TYPE': 'WORK'}]
    if email:
        contact_data['fields']['EMAIL'] = [{'VALUE': email, 'VALUE_TYPE': 'WORK'}]
    if company:
        contact_data['fields']['COMPANY_TITLE'] = company
    
    try:
        contact_url = f"{bitrix_webhook}crm.contact.add.json"
        contact_json = json.dumps(contact_data).encode('utf-8')
        contact_req = urllib.request.Request(contact_url, data=contact_json, 
                                             headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(contact_req) as response:
            contact_result = json.loads(response.read().decode('utf-8'))
            if 'result' in contact_result:
                contact_id = contact_result['result']
                deal_data['fields']['CONTACT_ID'] = contact_id
        
        deal_url = f"{bitrix_webhook}crm.deal.add.json"
        deal_json = json.dumps(deal_data).encode('utf-8')
        deal_req = urllib.request.Request(deal_url, data=deal_json, 
                                         headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(deal_req) as response:
            deal_result = json.loads(response.read().decode('utf-8'))
            
            if 'result' in deal_result:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({
                        'success': True,
                        'dealId': deal_result['result'],
                        'contactId': contact_id if 'contact_id' in locals() else None
                    }),
                    'isBase64Encoded': False
                }
            else:
                error_msg = deal_result.get('error_description', 'Unknown error')
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': f'Bitrix error: {error_msg}'}),
                    'isBase64Encoded': False
                }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }

@app.route('/telegram-send', methods=['GET', 'POST', 'OPTIONS'])
def telegram_send():
    if request.method == 'OPTIONS':
        return '', 200
    
    event = {
        'httpMethod': request.method,
        'body': request.get_data(as_text=True),
        'headers': dict(request.headers),
        'queryStringParameters': dict(request.args)
    }
    
    context = Context(request_id=request.headers.get('X-Request-ID', 'local'))
    result = telegram_handler(event, context)
    
    response = jsonify(json.loads(result['body']))
    response.status_code = result['statusCode']
    for key, value in result['headers'].items():
        response.headers[key] = value
    
    return response

@app.route('/bitrix-create-deal', methods=['GET', 'POST', 'OPTIONS'])
def bitrix_create_deal():
    if request.method == 'OPTIONS':
        return '', 200
    
    event = {
        'httpMethod': request.method,
        'body': request.get_data(as_text=True),
        'headers': dict(request.headers),
        'queryStringParameters': dict(request.args)
    }
    
    context = Context(request_id=request.headers.get('X-Request-ID', 'local'))
    result = bitrix_handler(event, context)
    
    response = jsonify(json.loads(result['body']))
    response.status_code = result['statusCode']
    for key, value in result['headers'].items():
        response.headers[key] = value
    
    return response

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'backend-api'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### 3. Создание requirements.txt

```txt
flask==3.0.0
flask-cors==4.0.0
gunicorn==21.2.0
```

### 4. Создание Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

### 5. Создание docker-compose.yml

```yaml
version: '3.8'

services:
  backend-api:
    build: .
    container_name: backend-api
    restart: unless-stopped
    ports:
      - "5000:5000"
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - BITRIX_WEBHOOK_URL=${BITRIX_WEBHOOK_URL}
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 6. Создание .env файла

```bash
# Создайте файл .env с вашими настройками
cat > .env << 'EOF'
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.ru/rest/1/xxxxx/
EOF

# Защита файла с секретами
chmod 600 .env
```

### 7. Запуск backend API

```bash
# Сборка и запуск
sudo docker compose up -d

# Проверка статуса
sudo docker compose ps
sudo docker compose logs -f

# Тест API
curl http://localhost:5000/health
```

### 8. Настройка Nginx reverse proxy

Добавьте в основной `nginx.conf` (на хосте):

```nginx
# Backend API proxy
location /api/ {
    proxy_pass http://localhost:5000/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_cache_bypass $http_upgrade;
    proxy_read_timeout 120s;
}
```

Перезапустите Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Обновление frontend

Измените файл `backend/func2url.json`:

```json
{
  "bitrix-create-deal": "https://your-domain.com/api/bitrix-create-deal",
  "telegram-send": "https://your-domain.com/api/telegram-send"
}
```

Пересоберите frontend:
```bash
cd /opt/webapp
npm run build
sudo docker compose restart web
```

## Вариант 2: Serverless на собственной инфраструктуре

Если хотите использовать serverless подход на своем сервере, можно использовать:

### OpenFaaS

1. Установка OpenFaaS:
```bash
# Установка arkade
curl -sLS https://get.arkade.dev | sudo sh

# Установка OpenFaaS CLI
arkade get faas-cli

# Развертывание OpenFaaS (требует Kubernetes)
arkade install openfaas
```

2. Создание функций для OpenFaaS (структура аналогична текущей)

## Вариант 3: AWS Lambda / Yandex Cloud Functions

Можно развернуть на облачных провайдерах:

### Yandex Cloud Functions

```bash
# Установка CLI
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Создание функции
yc serverless function create --name=telegram-send

# Загрузка кода
yc serverless function version create \
  --function-name=telegram-send \
  --runtime python311 \
  --entrypoint index.handler \
  --memory 128m \
  --execution-timeout 30s \
  --source-path ./backend/telegram-send
```

## Тестирование функций

### Тест telegram-send

```bash
curl -X POST http://localhost:5000/telegram-send \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовый клиент",
    "phone": "+79001234567",
    "message": "Тестовое сообщение",
    "source": "Веб-сайт"
  }'
```

### Тест bitrix-create-deal

```bash
curl -X POST http://localhost:5000/bitrix-create-deal \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Иван Иванов",
    "phone": "+79001234567",
    "email": "test@example.com",
    "service": "1С:Предприятие 8",
    "price": "от 10000₽/месяц",
    "message": "Интересует внедрение"
  }'
```

## Мониторинг и логирование

### Просмотр логов

```bash
# Логи API
sudo docker compose logs -f backend-api

# Последние 100 строк
sudo docker compose logs --tail=100 backend-api
```

### Метрики

Добавьте Prometheus endpoint в `app.py`:

```python
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)
```

## Резервное копирование

```bash
# Backup скрипт для backend
cat > /opt/backup-backend.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/backend"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Бэкап кода
tar -czf $BACKUP_DIR/backend_$DATE.tar.gz /opt/webapp/backend-api

# Бэкап .env (с секретами)
cp /opt/webapp/backend-api/.env $BACKUP_DIR/env_$DATE.backup

# Удаление старых backup'ов (>30 дней)
find $BACKUP_DIR -name "backend_*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "env_*.backup" -mtime +30 -delete
EOF

chmod +x /opt/backup-backend.sh
```

## Безопасность

### 1. Ограничение доступа к API

Добавьте rate limiting в Nginx:

```nginx
# В http блоке
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# В location /api/
location /api/ {
    limit_req zone=api_limit burst=20 nodelay;
    proxy_pass http://localhost:5000/;
}
```

### 2. Firewall правила

```bash
# Разрешить только локальный доступ к порту 5000
sudo firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="127.0.0.1" port protocol="tcp" port="5000" accept'
sudo firewall-cmd --reload
```

### 3. Защита секретов

```bash
# Права доступа к .env
chmod 600 /opt/webapp/backend-api/.env
chown root:root /opt/webapp/backend-api/.env
```

## Обновление функций

```bash
cd /opt/webapp/backend-api

# Остановка
sudo docker compose down

# Обновление кода
# (внесите изменения в app.py)

# Пересборка и запуск
sudo docker compose build
sudo docker compose up -d

# Проверка
curl http://localhost:5000/health
```

## Устранение неполадок

### API не отвечает

```bash
# Проверка статуса контейнера
sudo docker compose ps

# Проверка логов
sudo docker compose logs backend-api

# Проверка портов
sudo netstat -tulpn | grep 5000
```

### Telegram не отправляет сообщения

```bash
# Проверка переменных окружения
sudo docker exec backend-api env | grep TELEGRAM

# Тест Telegram API вручную
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### Bitrix возвращает ошибки

```bash
# Проверка webhook URL
sudo docker exec backend-api env | grep BITRIX

# Тест webhook вручную
curl "https://your-domain.bitrix24.ru/rest/1/xxxxx/crm.deal.list.json"
```

## Рекомендации

1. **Используйте Вариант 1 (Flask API)** - это самый простой и надежный способ
2. **Настройте HTTPS** на Nginx для защиты передачи данных
3. **Регулярно делайте backup** файла .env с секретами
4. **Настройте мониторинг** через Prometheus + Grafana
5. **Используйте CDN** для статических файлов фронтенда

## Итоговая структура проекта

```
/opt/webapp/
├── backend-api/              # Backend функции
│   ├── app.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── .env                  # Секреты
│   └── logs/
├── frontend/                 # Фронтенд (из основного DEPLOYMENT.md)
│   ├── Dockerfile
│   ├── nginx.conf
│   └── ...
└── nginx-proxy.conf          # Главный Nginx конфиг
```

## Поддержка

Telegram сообщество: https://t.me/+QgiLIa1gFRY4Y2Iy
