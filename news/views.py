from django.shortcuts import render
from django.views.generic import ListView, DetailView, TemplateView;

from django.http import HttpResponse;

from .models import Post, User, Author, Comment, Category, PostCategory, CategorySubscriber, main_p_per_page;
from datetime import datetime;

import re;                                  # мне нужен поиск и замена по шаблону

from django.contrib.auth.mixins import LoginRequiredMixin;
from django.core.exceptions import PermissionDenied;

from django.utils.decorators import method_decorator;
from django.views.decorators.cache import never_cache;

from django.db.models import Q;                                         # будем использовать логику ИЛИ при запросе к БД

from django.core.mail import send_mail, EmailMultiAlternatives;         # для отправки писем

from django.template.loader import render_to_string;

from .templatetags.custom_filters import d_normal, censor, html_cnv, get_author;

from NewsPaper.settings import SERVER_EMAIL;



class NeverCache(object):                                           # декоратор для запрета кеширования страниц (в случае переходов по истории)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super(NeverCache, self).dispatch(*args, **kwargs);


class PostsPreview(NeverCache, ListView):       # все посты (для главной страницы - список новостей)
    model = Post;                               # имя таблицы
    template_name = 'flatpages/news.html';      # файл, в котором переменная будет доступна
    context_object_name = 'news_all';           # имя "переменной", по которому она будет доступна в шаблоне
    paginate_by = main_p_per_page;              # количество постов, выводимых на одной странице
    sb_set=[];

    def get_queryset(self):                             # обработаем переменные в адресной строке (если они есть)
        w_tags = self.request.GET.get("tags");          # если есть - здесь будет сортировка по тегам (по категориям)
        w_sub = self.request.GET.get("subscribe");      # хочет подписаться?
        w_unsub = self.request.GET.get("unsubscribe");  # хочет отписаться?
        user = self.request.user;
        sb_tags=0;
        if w_tags:
            if w_tags.isdecimal():
                sb_tags=1;
        if (sb_tags==1):
            self.sb_set=Post.objects.filter(category=int(w_tags)).order_by('-m_of_creation');
        else:
            self.sb_set = Post.objects.all().order_by('-m_of_creation');
        """ проверим подписку пользователя, если он вдруг нажал на соответствующую ссылку """
        if (w_sub == "me" and w_unsub != "me" or w_sub != "me" and w_unsub == "me") and sb_tags == 1 and user.email and user.is_active:
            is_subbed = False;
            if Category.objects.filter(id=int(w_tags), subscriber=user.id).exists():
                is_subbed = True;
            if w_sub == "me":
                CategorySubscriber.objects.create(category_id=int(w_tags), user_id=user.id);
            else:
                CategorySubscriber.objects.filter(category_id=int(w_tags), user_id=user.id).delete();

        return self.sb_set;

    @staticmethod
    def list_tags():                        # возвращает queryset всех возможных категорий публикаций
        return Category.objects.all().order_by('cat_name');


class PostView(DetailView):                 # пост (для страницы с конкретной новостью - детальный вид)
    model = Post;
    template_name = 'flatpages/post.html';  # файл шаблона
    context_object_name = 'post_view';
    def get_context_data (self, **kwargs):  # добавим еще доступных переменных
        c = super().get_context_data(**kwargs);     # возьмем набор данных этой новости и забьем объект комментариями к этому посту
        c['comm'] =Comment.objects.filter(post_id=self.object.id).order_by('-m_of_comm');   # запишем набор комментариев и имя переменной
        return c;


""" этот метод работал бы нормально и искал без учета регистра с любой другой SQL. Но с этой только вот так """
""" создавать дополнительные поля либо писать дикие функции не будем. пусть будет как есть """
class ShortSearch(NeverCache, ListView):            # поиск с главной страницы (из шапки) и со страницы поиска (в расширенном варианте)
    template_name = 'flatpages/search.html';        # файл шаблона, куда перенаправит нас поле поиска
    context_object_name = 'main_search';            # название переменной в шаблоне - с нее будим выжимать итоги поиска
    paginate_by = main_p_per_page - 1;
    s_set=[];
    ordering = '-m_of_creation';
    def get_queryset(self):                                     # после перехода на страницу поиска там выполним это:
        s_query = self.request.GET.get("s_string");             # забьем содержимое из запроса в переменную
        s_query = f"{s_query.strip()}";
        s_author = self.request.GET.get("s_a");
        s_type = self.request.GET.get("t");                     # тип - Новость-Статья
        s_category = self.request.GET.getlist('cn');
        s_use_date = self.request.GET.get("exac_date");         # флаг - поиск по дате, так как дата передается почти во всех случаях (но это только пока)
        s_date = self.request.GET.get("date");
        cat, s_author_list, s_authors_id, s_authors_idx = [], [], [], [];
        flag_a = False;                                         # стоит ли выполнять поск в базе данных? вдруг не выбраны нужные поля.

        if s_author:
            s_author = f"{s_author.strip()}";
            if (len(s_author)<2):                               # если запрос на автора короткий - не учитывать его
                s_author=None;                                  # не прошел проверку - отправим переменную в небытие. И так будет со всеми и далее.
        if s_type:                                              # посмотрим, верно ли указан тип публикации
            if s_type not in ['0','1']:
                s_type = [0,1];
        else:
            s_type=[0,1];

        nnn = list(Category.objects.all().values('id'));        # проверим, существует ли категория в запросе в нашей БД
        for i in range(0, len(nnn)):
            cat.append(str(nnn[i]['id']));                      # забьём в массив все id категорий, а затем сравним их с содержимым запроса
        if s_category:
            for f in range(0,len(s_category)):
                if s_category[f] not in cat:
                    s_category=None;
        if not s_category:                                      # если нет выбранных категорий, то забъем в список все существующие категории (ищем везде)
            s_category=cat;
        else:
            flag_a=True;

        if s_use_date:                                          # если есть переменная, указывающая на поиск по дате
            if s_use_date != "1":                               # ..помним, что это строковое значение
                s_use_date=None;                                # ничего, кроме единицы - нас не интересует
        if s_date:                                              # и проверим формат даты. Не будем сверять с БД - просто проверим написание
            date_key, s_date_list = 0, s_date.split("-");
            if (len(s_date_list) == 3):
                if (s_date_list[0].isdecimal() and s_date_list[1].isdecimal() and s_date_list[1].isdecimal()):
                    if (2050 > int(s_date_list[0]) > 2021) and (13 > int(s_date_list[1]) > 0) and (32 > int(s_date_list[2]) > 0):
                        date_key=1;
            if date_key == 0:
                s_date=None;
            else:
                if s_use_date:
                    flag_a=True;
        """ Далее тихий ужас. Необходимо завести дополнительное поле с полным именем автора. Иначе - только такое такое-себе """
        if (s_author):
            s_author_list=s_author.split(" ");                              # а вдруг ввели в поиске и имя и фамилию? - проверим
            for i in range(0,len(s_author_list)):
                s_author_list[i]=f"{s_author_list[i].strip()}";
            s_authors_id = Author.objects.filter(user__first_name__in=s_author_list).values('id').order_by('id') | \
                                Author.objects.filter(user__last_name__in=s_author_list).values('id').order_by('id');
            s_authors_idn=list(s_authors_id);
            for i in range(0,len(s_authors_idn)):
                s_authors_idx.append(s_authors_idn[i]['id'])                # забили сюда ID всех авторов, которых смогли найти по И и Ф.
        else:
            s_author=None;                                                  # - если не нашли автора среди авторов

        if not s_use_date or not s_date:                                    # если флажок даты не стоит - просто сведем поле в ноль
            s_date="";

        """ Далее поступим так: если есть строка запроса, или просто применен фильтр, то делим основной поиск на две части: с автором и без автора """
        """ После чего будем искать основную строку поиска сперва в заголовке поста, а уже после - в тексте """
        if (s_query):
            if len(s_query) > 2:
                flag_a=True;
        if (s_author):
            if len(s_author)>2:
                flag_a=True;

        if flag_a:

            if not s_author:
                self.s_set = Post.objects.filter(Q(header__icontains=s_query) | Q(text__icontains=s_query),type__in=s_type,category__in=s_category,
                m_of_creation__icontains=s_date).values('header','text','type','author','id','m_of_creation').order_by('-m_of_creation').distinct();
            else:
                self.s_set = Post.objects.filter(Q(header__icontains=s_query) | Q(text__icontains=s_query),
                author_id__in=s_authors_idx,type__in=s_type,category__in=s_category,
                m_of_creation__icontains=s_date).values('header','text','type','author','id','m_of_creation').order_by('-m_of_creation').distinct();


        return self.s_set;                          # отправим результат в конечный шаблон

    @staticmethod
    def cat_list():                                 # передадим в модель список всех доступных категорий постов
        return Category.objects.all().order_by('id');


class CreateNews(LoginRequiredMixin, TemplateView):                 # создание новостей и статей. Будем использовать простой тип и напишем много функций
    template_name='flatpages/modify.html';                          # адреса разные, но шаблон у нас боудет один и тот же
    context_object_name = 'modify_news';                            # на всякий. возможно не пригодится
    raise_exception = True;                                         # открывать страницу с ошибкой доступа, если не авторизирован

    def get_context_data(self, **kwargs):                           # определим логин автора
        c = super(CreateNews, self).get_context_data(**kwargs);     # и его группу
        user = self.request.user;                                   # если его нет в нужной группе, либо его учетка отключена, либо он не админ -
        if user.is_active != True:                                  # - вывести страницу код-403
            raise PermissionDenied();
        if not user.groups.filter(name__in=['Authors', 'Moderators']).exists() and not user.is_superuser:       # если пытается создать, не имея на это прав:
            raise PermissionDenied();
        today_begin, today_end = f"{datetime.now().date()} 00:00:00.00001", f"{datetime.now().date()} 23:59:59.99999";
        author_id=get_author(self.request.user.id);                 # посмотрим, создавал ли user хоть одну публикацию и если да - вытащим его io как id автора
        if author_id:
            if (Post.objects.filter(m_of_creation__range=(today_begin, today_end),
                type=0, author_id=author_id).count() > 2 and self.request.META['PATH_INFO'] == "/news/create/"):    # если это уже третья новость за день:
                raise PermissionDenied();
        return c;

    def post(self,request, *args, **kwargs):                        # функция, вызываемая при отправки формы
        context = self.get_context_data();                          # возьмем все дефолтные данные о шаблоне (нас интересует только view)
        n_title = f"{self.request.POST.get('n_title')}";            # заголовок поста
        n_category = self.request.POST.get('cn');                   # категория(рии) поста
        n_text = f"{self.request.POST.get('n_text')}";              # основной текст поста
        n_author = f"{self.request.POST.get('n_author')}";          # автор нового поста
        n_type = f"{self.request.POST.get('n_type')}";              # тип публикации - новость 0 / статья 1

        context["post_error"]="0";                                  # флаг ошибки (установим в ноль и передадим в контексте в шаблон)
        html_out, n_text = "", n_text.strip();
        if len(re.sub("[\n\r\t\f\v]" , "", n_text.replace(" ", ""))) < 50:              # уберем все "непечатки" и проверим длину без них
            context["post_error"] = "<b>Ошибка</b>: Текст публикации должен состоять не менее, чем из 50 символов.";

        n_category = list(n_category);
        if len(n_category)==0:
            context["post_error"] = "<b>Ошибка</b>: Выберите хотя бы одну категорию, характеризующую тему новой публикации.";
        else:                                                                           # проверим, не подменен ли запрос в плане категории
            f_flag=0;
            nlist=list(self.cat_list().values('id'));
            for i in range(0, len(nlist)):
                if str(nlist[i]['id']) in n_category:
                    f_flag=1;
            if f_flag == 0:
                context["post_error"] = "<b>Ошибка</b>: Указана несуществующая категория публикации.";     # такой категории нет в БД. Такой исход маловероятен, но всё же

        n_title=n_title.strip();                                                            # не будем при проверке мин. длины считать спецсимволы
        if len(re.sub("[\n\r\t\f\v]" , "", n_title.replace(" ", ""))) < 10:
            context["post_error"]="<b>Ошибка</b>: Название публикации должно содержать не менее 10 символов.";
        else:
            if Post.objects.filter(header=n_title):
                context["post_error"]="<b>Ошибка</b>: Публикация с таким названием уже существует.";
        context["n_title"], context["n_text"] = n_title, n_text;        # запишем в возвращаемый контекст новые ключи, чтобы если вдруг в форме ошибка..
                                                                        # .. то нам не пришлось набирать текст публикации заново
        if not n_type:                                                  # на случай подмены формы:
            context["post_error"]="<b>Ошибка</b>: Неисправность на сервере. Повторите процедуру добавления публикации.";
        else:
            if n_type.isdecimal():
                n_type=int(n_type);
                if n_type not in [0,1]:
                    context["post_error"] = "<b>Ошибка</b>: Неисправность на сервере. Повторите процедуру добавления публикации.";

        if (context["post_error"]=="0"):                                    # ошибок нет - пишем в БД
            if (str(self.request.user) == n_author):                        # если автор с формы соответствует текущей авторизации..
                u_id=User.objects.get(username=n_author).id;                # - возьмем его id
                a_id=Author.objects.filter(user_id=u_id).values('id');      # и проверим - числится ли он среди авторов:
                if not a_id:                                                # - если нет, то создадим нового автора и возьмем его id
                    new_id=Author.objects.create(user_id=u_id);
                    a_id=new_id.id;
                else:                                                       # - а если да - выжмем id из результата поиска
                    a_id=list(a_id)[0]['id'];
                today_begin, today_end =f"{datetime.now().date()} 00:00:00.00001", f"{datetime.now().date()} 23:59:59.99999";

                if (Post.objects.filter(m_of_creation__range=(today_begin, today_end), type=0, author_id=a_id).count() < 3 and int(n_type) == 0) or int(n_type) != 0:
                    Post.n_category = n_category;                               # передадим перечень будущих категорий в instance для обработчика событий
                    post_id = Post.objects.create(type=n_type, header=n_title, text=n_text, author_id=a_id);    # здесь нас должен услышать обработчик событий
                    category_names=[];
                    for i in range(0,len(n_category)):                          # заодно пополним связь с категориями публикаций
                        PostCategory.objects.create(post_id=post_id.id, category_id=int(n_category[i]));
                        category_names.append(Category.objects.get(id=int(n_category[i])).cat_name);
                    context["post_form"]="ACCEPTED";
                    context["post_error"]="<br><br><center><b>НОВОСТЬ СОХРАНЕНА</b></center>" if n_type==0 else "<br><br><center><b>СТАТЬЯ СОХРАНЕНА</b></center>";

                else:
                    context["post_error"] = "<b>Ошибка</b>: Вы можете опубликовать не более трех новостей в сутки.";
            else:                                                                               # если форма не совпала с авторизацией:
                context["post_error"] = "<b>Ошибка</b>: Неисправность на сервере. Повторите процедуру добавления публикации.";

        return HttpResponse(context['post_error']);

    @staticmethod
    def cat_list():                                                     # создадим список всех тегов постов для шаблона
        return Category.objects.all().order_by('id');



class EditNews(LoginRequiredMixin, DetailView):                               # редактирование публикации
    template_name='flatpages/postedit.html';
    context_object_name = 'edit_post';
    model = Post;
    raise_exception = True;

    def get_context_data(self, **kwargs):
        c = super(EditNews, self).get_context_data(**kwargs);
        user = self.request.user;
        post_author_id=self.object.author_id;

        author_id=Author.objects.filter(user_id=user.id).values('id');
        a_flag=0;
        if author_id:
            if author_id[0]['id'] == post_author_id and user.is_active:     # проверим, есть ли у пользователя право доступа к этой публикации
                a_flag=1;
        if user.is_superuser:
            a_flag = 1;
        if a_flag != 1:                                                     # если нет - вызовем ошибку 403
            raise PermissionDenied();
        if not user.groups.filter(name__in=['Authors', 'Moderators']).exists() and not user.is_superuser:
            raise PermissionDenied();
        return c;

    def post(self, request, *args, **kwargs):                               # процедура отправки формы
        self.object = self.get_object();                                    # получим нашу запись текущую запись как объект контекста
        context = self.get_context_data();                                  # получим объект view (DetailView) и будем добавлять в него наши новые ключи
        context["post_error"] = "0";                                        # новый ключ - это флаг-текст ошибки либо сообщения об успехе выполнения процедуры
        context["post_header"] = f"{self.request.POST.get('p_header')}";    # получим значения полей и создадим новые ключи context
        context["post_text"]=f"{self.request.POST.get('p_text')}";
        context["post_id"]=f"{self.request.POST.get('p_id')}";              # ID изменяемой публикации
        n_category = self.request.POST.get('cn');
        n_category=list(n_category);

        if len(n_category)==0:
            context["post_error"] = "<b>Ошибка:</b> Выберите хотя бы одну категорию, характеризующую тему публикации.";
        else:
            f_flag=0;
            nlist=list(self.cat_list().values('id'));
            for i in range(0, len(nlist)):
                if str(nlist[i]['id']) in n_category:
                    f_flag=1;
            if f_flag == 0:
                context["post_error"] = "<b>Ошибка:</b> Указана несуществующая категория публикации.";

        context["post_header"] = context["post_header"].strip();
        if len(re.sub("[\n\r\t\f\v]", "", context["post_header"].replace(" ", ""))) < 10:
            context["post_error"] = "<b>Ошибка:</b> Название публикации должно содержать не менее 10 символов.";
        else:
            if Post.objects.filter(header=context["post_header"]).exclude(id=int(context["post_id"])):      # совпадение названий (исключая объект, разумеется)
                context["post_error"] = f"<b>Ошибка:</b> Публикация с таким названием уже существует.";

        if (context["post_error"] == "0"):                                                                  # если ошибок не было - сохраним пост:
            succ_f=0;
            author_id = Author.objects.filter(user_id=self.request.user).values('id');
            if (author_id):
                if (author_id[0]['id'] == self.object.author_id) and (self.object.id == int(context["post_id"]) and self.request.user.is_active):
                    succ_f=1;
                    Post.objects.filter(id=int(context["post_id"])).update(header=context["post_header"], text=context["post_text"]);
                    PostCategory.objects.filter(post_id=int(context["post_id"])).delete();                          # удалим прошлые категории
                    for i in range(0,len(n_category)):                                                              # добавим новые категории поста в БД
                        PostCategory.objects.create(post_id=int(context["post_id"]), category_id=int(n_category[i]));
                    context["post_error"] = "<b>*** ПУБЛИКАЦИЯ УСПЕШНО СОХРАНЕНА ***</b>";
            if succ_f == 0:
                context["post_error"] = f"<b>Ошибка</b>: Неисправность на сервере. Повторите процедуру изменения публикации.";

        return HttpResponse(context['post_error']);                                                         # новый только с текстом, без отрисовки

    @staticmethod
    def cat_list():
        return Category.objects.all().order_by('id');


class RemNews(DetailView):                                                              # удаление публикации
    template_name='flatpages/rempost.html';
    context_object_name = 'rem_post';
    model = Post;

    def get_context_data(self, **kwargs):                                               # проверка права собственности на публикацию
        c = super(RemNews, self).get_context_data(**kwargs);
        user = self.request.user;
        post_author_id=self.object.author_id;
        author_id=Author.objects.filter(user_id=user.id).values('id');
        a_flag=0;
        if author_id:
            if (author_id[0]['id'] == post_author_id and user.is_active) or user.is_superuser:
                a_flag=1;
        if user.is_superuser:
            a_flag = 1;                                                                 # админу можно удалять любую публикацию
        if a_flag != 1:
            raise PermissionDenied();                                                   # лично тебе сюда нельзя
        if not user.groups.filter(name__in=['Authors', 'Moderators']).exists() and not user.is_superuser:
            raise PermissionDenied();
        return c;

    def post(self, request, *args, **kwargs):                                                   # отправили сюда форму? тогда -
        self.object = self.get_object();
        context = self.get_context_data();
        context["post_message"] = "0";
        context["post_id"]=f"{self.request.POST.get('p_id')}";
        context["history_back"] = f"{self.request.POST.get('h_back')}";

        succ_f = 0;
        author_id = Author.objects.filter(user_id=self.request.user).values('id');              # ещё раз проверим право собственности автора
        if (not author_id and self.request.user.is_superuser):
            author_id=[{'id':self.object.author_id}];

        # удаление позволено только либо автору данной публикации, либо главному администратору, либо модератору ...
        if (author_id):
            if (author_id[0]['id'] == self.object.author_id and self.object.id == int(context["post_id"]) and self.request.user.is_active
             and self.request.user.groups.filter(name__in=['Authors','Moderators']).exists())\
             or (self.request.user.is_superuser and self.object.id == int(context["post_id"]))\
             or (self.request.user.groups.filter(name='Moderators').exists() and self.object.id == int(context["post_id"])):
                succ_f = 1;
                PostCategory.objects.filter(post_id=int(context["post_id"])).delete();          # удаляем связанные категории..
                Comment.objects.filter(post_id=int(context["post_id"])).delete();               # ..связанные комментарии
                Post.objects.filter(id=int(context["post_id"])).delete();                       # .. и саму публикацию
                context["post_message"] = "<br><br><br><center><b>*** ПУБЛИКАЦИЯ УДАЛЕНА ***</b></center>";
        if succ_f == 0:
            context["post_message"] = f"<br><br><b>Ошибка</b>: Неисправность на сервере. Повторите процедуру удаления публикации.";

        return HttpResponse(context['post_message']);






