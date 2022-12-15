from django.apps import AppConfig;
import os;

class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField';
    name = 'news';

    def ready(self):
        import news.signals;
        if os.environ.get('RUN_MAIN'):                          # сохраним перезагрузку, но запускать распиание рассылки будем только после теста
            from news.shedmail import send_articles;
            send_articles();