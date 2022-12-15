# файл с переменными, доступными во всех шаблонах (после подключения)

from datetime import datetime
from django import template;
from news.models import Post;

register = template.Library()

@register.simple_tag()
def date_now():                                         # читабельнаые текущие день недели, дата и время
    a_d = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"];
    return f"{a_d[int(datetime.now().strftime('%w')) - 1]}, {str(datetime.now().strftime('%d.%m.%Y %H:%M:%S'))}";

@register.simple_tag()
def p_quantity():                                       # общее количество постов
    return f"{Post.objects.all().count()}";

@register.simple_tag()
def date_begin():                                       # дата самого древнего поста
    return Post.objects.values('m_of_creation').order_by('m_of_creation').first()['m_of_creation'].strftime('%Y-%m-%d');

@register.simple_tag()
def date_end():                                         # дата самого свежего поста
    return Post.objects.values('m_of_creation').order_by('m_of_creation').last()['m_of_creation'].strftime('%Y-%m-%d');

