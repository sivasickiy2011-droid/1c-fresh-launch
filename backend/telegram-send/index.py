import json
import os
import urllib.request
import urllib.parse
from typing import Dict, Any
from datetime import datetime

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Business: Универсальная отправка уведомлений в Telegram
    Args: event с httpMethod, body (name, phone, message, user_id, action, message_type)
          context с request_id
    Returns: HTTP response с результатом отправки
    '''
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
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '7547487408:AAFQnLgkanxSA0Fe5cXZW6x64YImH_sU-gA')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '500136108')
    
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
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
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
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            telegram_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('ok'):
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': True, 'message': 'Notification sent'}),
                    'isBase64Encoded': False
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Telegram API error', 'details': result}),
                    'isBase64Encoded': False
                }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
