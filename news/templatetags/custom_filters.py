# фильтры для преобразования значений переменных

from django import template;
from django.utils.html import format_html;

from news.models import Category, PostCategory, Post, User, Author;           # пополним набор видимых моделей, т.к. будем с ними здесь работать

import re;

from datetime import datetime;

register = template.Library();

@register.filter()
def d_normal(value):    # фильтр для нормализации представления даты и времени
   a_d=["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"];
   return f"{a_d[int(value.strftime('%w'))-1]}, {str(value.strftime('%d.%m.%Y %H:%M:%S'))}";

@register.filter()
def censor(text):                                               # фильтр нецензурных слов, с сохранением оригинального регистра
    if type(text) != str:
        print(f"Только для разработчика: получен неверный тип данных в фильтре CENSOR - {type(text)}");
        return text;
    bw = [["бляд", [1]], ["хуй", [1]], ["пизд", [1]], ["ёбан", [1]],
          ["ебан", [1]], ["ебат", [1]], ["ебло", [1]], ["ебал", [1]],
          ["ахуе", [1, 2]], ["хуе", [1]], ["ебуч", [1]], ["пидар", [1, 2]],
          ["пидор", [1, 2]], ["еблан", [1, 2]]];                            # слова и места для звезд. Тут фантазия закончилась
    text_tolow=text.lower();                            # для поиска без огляда на регистр, переведем его вниз
    text_list=list(text);                               # создадим список, чтобы звездочки можно было менять по индексу
    for i in range(0, len(bw)):                         # пройдемся циклом по всем плохим словам
        beg_inx=0;
        keep=1;                                         # просто вспомогательный флаг, чтобы найти все вхождения (можно и inx, но так нагляднее)
        while keep==1:                                  # теперь циклом пройдемся по всему тексту для того, чтобы найти все вхождения слова
            inx = text_tolow.find(bw[i][0], beg_inx+1); # ищем слово, начиная с того места, где мы остановились в прошлой итерации плюс 1..
            if (inx != -1):                             # .. и если нашли вхождение слова - перепишем место, с которого продолжим поиск
                beg_inx=inx;                            # .. иначе снова напоремся на этот паттерн при следующей итерации
                for x in (bw[i][1]):                    # поставим звездочки - куда ставить указано в шаблоне плохих слов (индексы) -
                    text_list[inx + x]="*";             # - заменим сперва в списке по индексу
            else:
                keep=0;                                 # всё, поиск больше не может найти это слово - переходим к следующему слову
    text = "".join(text_list);                          # теперь вновь сливаем список в строку..
    return f"{text}";                                   # ..и возвращаем переменную в шаблон, отправивший нам этот текст

@register.filter()
def post_type(numm):                                    # просто преобразуем наш код из БД в надпись, обозначающую тип публикации
    t_type="Новости";
    if int(numm)==1:
        t_type="Статьи";
    return f"{t_type}";

@register.filter()
def post_tags(pid):                                                             # вернем теги новости
    tags="";
    p_tags=PostCategory.objects.filter(post_id=pid).order_by('category_id');    # получим набор строк из смежной таблицы...
    for i in p_tags:                                                            #.. и переберем его
        tag=Category.objects.get(id=i.category_id);
        tags+=f"<a href='/news/?tags={tag.id}'>{tag.cat_name}</a>, ";
    tags=tags[0:-2];                                                            # уберем лишнюю запятую и пробел в конце
    return f"{tags}";

@register.filter()
def post_author(pid):                                                           # вернем автора поста
    who = "";                                                                   # если регистрируемся по email, то логина, имени и фамилии у нас нет..
    author=User.objects.get(id=Author.objects.get(id=int(pid)).user_id);        # .. в этом случае автором будет email
    if author.first_name!="" and author.last_name!="":
        who = f"{author.first_name} {author.last_name}";
    elif author.username!="":
        who = f"{author.username}";
    else:
        who = f"{author.email}";
    return who;

@register.filter()
def post_shortener(text,patt):                                                  # этот ФИЛЬТР будет разбирать паттерн ПОИСКА и возвращать логику И и затем ИЛИ
    patt=patt.strip();                                                          # и сокращать исходник до паттерна плюс хвосты, но сейчас у меня на это нет времени

    return f"{text}";

@register.filter()
def cb_get(x,y):                                                                # возвращает True, если чекбокс в форме поиска поставлен
    a=x.getlist('cn');
    if str(y) in a:
        return True;
    else:
        return False;

@register.filter()
def del_page(x):                                                                # возвращает строку запроса без page
    n=x.find("&page=");
    return x if n == -1 else x[0:n];

@register.filter()
def postedit(x,t):                                                              # возвращает ссылку на страницу редактирования публикации
    x_link=f"../news/{x}/edit/";
    x_tag="новость";
    if (t==1):
        x_link = f"../articles/{x}/edit/";
        x_tag = "статью";
    return f"<a href='{x_link}' style='background-color:olive;color:black;text-decoration:none;'>редактировать {x_tag}</a>";

@register.filter()
def postrem(x,t):                                                                # возвращает ссылку на страницу удаления публикации
    x_link=f"../news/{x}/delete/";
    x_tag="новость";
    if (t==1):
        x_link = f"../articles/{x}/delete/";
        x_tag = "статью";
    return f"<a href='{x_link}' style='background-color:red;color:black;text-decoration:none;'>удалить {x_tag}</a>";

@register.filter()
def postedit_view(x,t):                                                          # возвращает ссылку на страницу редактирования публикации
    x_link=f"../{x}/edit/";
    x_tag="новость";
    if (t==1):
        x_link = f"../{x}/edit/";
        x_tag = "статью";
    return f"<a href='{x_link}' style='background-color:olive;color:black;text-decoration:none;'>редактировать {x_tag}</a>";

@register.filter()
def postrem_view(x,t):                                                             # возвращает ссылку на страницу удаления публикации
    x_link=f"../{x}/delete/";
    x_tag="новость";
    if (t==1):
        x_link = f"../{x}/delete/";
        x_tag = "статью";
    return f"<a href='{x_link}' style='background-color:red;color:black;text-decoration:none;'>удалить {x_tag}</a>";

@register.filter()
def post_tags_id(pid):                                                          # вернем ID теги новости
    tags=[];
    p_tags=PostCategory.objects.filter(post_id=pid).order_by('category_id');
    for i in p_tags:
        tags.append(Category.objects.get(id=i.category_id).id);
    return tags;

@register.filter()
def fresh_header(pid):                                                          # вернём заголовок поста для сброса значения в форме через JS
    hd=Post.objects.get(id=pid).header;
    return hd;

@register.filter()
def fresh_text(pid):                                                            # вернём текст поста для сброса значения в форме через JS
    td=Post.objects.get(id=pid).text;
    return td;

@register.filter()
def check_date(x):                                                              # проверим дату из шаблона на 'корректность': да? - возвращаем ее в значение
    res=False;
    a=x.getlist('date');
    if len(a)>0:
        a_list = a[0].split("-");
        if (len(a_list) == 3):
            if (a_list[0].isdecimal() and a_list[1].isdecimal() and a_list[1].isdecimal()):
                if (2050 > int(a_list[0]) > 2021) and (13 > int(a_list[1]) > 0) and (32 > int(a_list[2]) > 0):
                    res=f"{'-'.join(a)}";
    return res;

@register.filter()
def get_post_id(x):                                                             # возвращает id публикации из значения адресной строки
    out=x;
    if len(x)>0:
        inx=x.rfind("/",0,len(x)-1);
        if x[inx+1:-1:].isdecimal():
            out=int(x[inx+1:-1:]);
    return out;

@register.filter()
def lqs(x,y):                                                                   # определяет, пренадлежит ли user к какой то группе (модераторы, авторы и т.д)
    b=False;                                                                    # если группа Y есть в queryset X - вернём True, иначе False
    n=list(x.values_list('name', flat = True));                                 # вырежем заголовки из queryset и сделаем из оставшихся значений список
    if y in n:
        b=True;
    return b;

@register.filter()
def gt(x,y):                                                                    # возвращает значение нужного поля Y из БД объекта X (id)
    who="";
    ob=User.objects.get(id=Author.objects.get(id=int(x)).user_id);
    if y == "username":
        who=ob.username;
    if y == "email":
        who=ob.email;
    return who;

@register.filter()
def tby_id(x):                                                                  # возвращает название тега по ID
    out="";
    if (x):
        if x.isdecimal():
            cat_set = Category.objects.filter(id=int(x)).values('cat_name');
            if cat_set.exists():
                out=list(cat_set)[0]['cat_name'];
    return out;

@register.filter()
def s_u(x,y):                                                                   # добавляет к строке подстроку, но только если ее ещё там нет (url) ...
    out = "";
    inx = 0;
    if y == "unsubscribe=me":                                                   # ... плюс убирает остатки антонима, если он там есть
        x = x.replace("&subscribe=me","");
    if y == "subscribe=me":
        x = x.replace("&unsubscribe=me","");
    if not y:
        y = "";
    if x:
        inx = x.find(str(y));
    out = x if inx == -1 or inx == 0 else x[0:inx-1];
    return "?"+y if out == "" else "?" + out + "&" + y;

@register.filter()
def is_subscriber(x,y):                                                         # проверяет, подписан ли пользователь id X на категорию id Y или нет
    out = False;
    if x and y:
        if str(x).isdecimal() and str(y).isdecimal():
            if Category.objects.filter(id=int(y), subscriber=int(x)).exists():
                out = True;
    return out;


@register.filter()
def html_cnv(text):                                                 # приобразуем сырой текст в текст, который понятен и безопасен для разметки html
    i_t=["&",'"',"\r","\t","<",">","!","'","/","*","@","`",":","=",
         "?","(",")","[","]","{","}","|","~","_","^","$",
         "#","%","+","-","\n","\\"];                                    # потенциально опасные символы
    o_t=["&amp;",'&quot;',"","","&lt;","&gt;","&excl;","&apos;","&sol;","&ast;","&commat;","&grave;","&colon;","&equals;",
         "&quest;","&lpar;","&rpar;","&lbrack;","&rbrack;","&lbrace;","&rbrace;","&vert;","&tilde;","&lowbar;","&Hat;","&dollar;",
         "&num;","&percnt;","&plus;","&minus;","<br>","&bsol;"];        # и их замена
    for t in range(0,len(i_t)):
        text = text.replace(i_t[t], o_t[t]);
    return f"{text}";

@register.filter()
def get_author(userid):                                                 # возвращает id автора по user-id (если он, конечно, является автором)
    author_id = None;
    try:
        author_id = Author.objects.get(user_id=userid).id;
    except Author.DoesNotExist:
        pass;
    return author_id;

@register.filter
def chk_n_create(userid):                                               # определяет, не создал ли автор уже три новости за сегодня
    bkey = True;
    if userid:
        today_begin, today_end = f"{datetime.now().date()} 00:00:00.00001", f"{datetime.now().date()} 23:59:59.99999";
        author_id = get_author(userid);
        if author_id:
            if (Post.objects.filter(m_of_creation__range=(today_begin, today_end), type=0, author_id=author_id).count() > 2):
                bkey = False;
    return bkey;

@register.filter
def ovrd_mess(mess):                                                    # кастомные сообщеения об ошибках в формах
    mess = str(mess);
    mess = mess.replace('<ul class="errorlist">', '');
    mess = mess.replace('</ul>', '');
    mess = mess.replace('<li>', '');
    mess = mess.replace('</li>', '');
    mess = mess.replace('The password is too similar to the e-mail.', '- пароль слишком похож на e-mail<br>');
    mess = mess.replace('This password is too short. It must contain at least 8 characters.', ' - слишком корокий пароль: нужно не менее 8 символов<br>');
    mess = mess.replace('A user is already registered with this e-mail address.', ' - пользователь с таким e-mail уже существует<br>');
    mess = mess.replace('Enter a valid email address', ' - введите корректный адрес электронной почты<br>');
    mess = mess.replace('The e-mail address and/or password you specified are not correct.', ' - неверно введены почтовый адрес или пароль<br>');
    lastbrake = mess.find("<br>");
    return mess[:lastbrake:];


