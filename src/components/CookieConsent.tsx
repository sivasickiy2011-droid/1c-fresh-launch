import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

export default function CookieConsent() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('cookieConsent');
    if (!consent) {
      setIsVisible(true);
    }
  }, []);

  const handleAccept = async () => {
    const userId = localStorage.getItem('userId') || `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem('userId', userId);
    localStorage.setItem('cookieConsent', 'accepted');
    
    try {
      await fetch('https://functions.poehali.dev/09d20db6-66dc-4441-860c-48bebddba56c', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message_type: 'consent',
          user_id: userId,
          action: 'accepted'
        })
      });
    } catch (error) {
      console.error('Failed to send consent notification:', error);
    }
    
    setIsVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem('cookieConsent', 'declined');
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 animate-in slide-in-from-bottom duration-300">
      <Card className="max-w-4xl mx-auto p-6 bg-white shadow-2xl border-2 border-orange-200">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
          <div className="flex-shrink-0">
            <div className="bg-orange-100 rounded-full p-3">
              <Icon name="Cookie" className="text-orange-500" size={24} />
            </div>
          </div>
          
          <div className="flex-1">
            <h3 className="font-display font-bold text-lg text-gray-900 mb-2">
              Использование файлов cookie
            </h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              Мы используем файлы cookie для улучшения работы сайта и анализа посещаемости.
              Продолжая использовать сайт, вы соглашаетесь с нашей{' '}
              <a href="https://disk.360.yandex.ru/i/0I6mvCXKNWPNwg" target="_blank" rel="noopener noreferrer" className="text-orange-500 hover:text-orange-600 underline">
                Политикой конфиденциальности
              </a>.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
            <Button
              onClick={handleAccept}
              className="bg-orange-500 hover:bg-orange-600 text-white rounded-[30px] px-6"
            >
              Принять
            </Button>
            <Button
              onClick={handleDecline}
              variant="outline"
              className="border-gray-300 text-gray-700 hover:bg-gray-50 rounded-[30px] px-6"
            >
              Отклонить
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}