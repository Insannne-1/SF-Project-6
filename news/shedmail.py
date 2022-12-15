from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from NewsPaper.settings import TIME_ZONE;
from .models import Author, Post, User, CategorySubscriber, PostCategory, Category;
from datetime import datetime, timedelta;
from .templatetags.custom_filters import d_normal, censor, html_cnv;
from django.template.loader import render_to_string;
from NewsPaper.settings import DEFAULT_FROM_EMAIL;
from django.core.mail import send_mail, EmailMultiAlternatives;



def send_mail_subs():
    try:
        pub_name, pub_name_a, pub_name_b = "статья", "статьи", "статей";
        days_now = datetime.now();
        days_then = days_now - timedelta(7);                                                                        # дата неделю назад
        rec_set = CategorySubscriber.objects.all().values('user').order_by('user_id').distinct();   # сперва возьмем набор всех подписчиков, какие есть
        for rec in rec_set:                                                                                         # обрабатываем одного подписчика, поехали:
            user_data = User.objects.get(id=rec['user']);
            rec_name = user_data.username if user_data.username != "" else user_data.email;                         # имя получателя
            rec_email = user_data.email;                                                                            # e-mail получателя
            if rec_email != "":                                                                                     # адрес почты заполнет? тогда продолжим
                inter_set_id = [];                                                                                  # набор id категорий получателя
                inter_set_name = [];                                                                                # набор названий категорий получателя
                cats_set = CategorySubscriber.objects.filter(user=rec['user']).values('category').order_by('category');
                for n in cats_set:
                    inter_set_id.append(n['category']);
                    inter_set_name.append(Category.objects.get(id=n['category']).cat_name);
                middle_content = f"Здравствуйте, <b>{rec_name}</b>! Вы подписались на разделы {', '.join(inter_set_name)}.<br>" \
                f"Вот подборка статей по Вашим интересам за прошедшую неделю:<br><br>";
                text_out = f"Здравствуйте, {rec_name}! Вы подписались на разделы {', '.join(inter_set_name)}.\r\n" \
                f"Вот подборка статей по Вашим интересам за прошедшую неделю:\r\n\r\n";
                post_set = Post.objects.filter(category__in=inter_set_id, type=1,
                m_of_creation__range=(days_then,days_now)).values('header','m_of_creation','id','author').order_by('id').distinct();
                for p in post_set:                                                                              # набираем все публикации для получателя
                    author = User.objects.get(id=Author.objects.get(id=p['author']).user_id).username;
                    middle_content += f"<b>{str(p['m_of_creation'].strftime('%d.%m.%Y %H:%M:%S'))}</b>&nbsp;&nbsp;Автор <b>{html_cnv(author)}</b><br>" \
                    f"&laquo;{html_cnv(censor(p['header']))}&raquo;<br><a href='http://127.0.0.1:8000/news/{p['id']}/'>полный текст</a><br><br>";
                    text_out += f"{str(p['m_of_creation'].strftime('%d.%m.%Y %H:%M:%S'))} Автор {html_cnv(author)}\r\n" \
                    f"{censor(p['header'])}\r\nполный текст статьи можно почитать по ссылке: http://127.0.0.1:8000/news/{p['id']}/\r\n\r\n";
                html_par = {'text':middle_content};
                html_out = render_to_string("mail/mweekly.html", html_par);
                msg = EmailMultiAlternatives(
                    subject=f'Новостной портал: список статей по избранным темам за неделю',
                    body=text_out,
                    from_email=DEFAULT_FROM_EMAIL,
                    to=[rec_email]
                );
                msg.attach_alternative(html_out, "text/html");
                try:
                    msg.send();
                except smtplib.SMTPDataError:
                    pass;
        print("- - - цикл еженедельной рассылки статей по подписке завершен.");
    except KeyboardInterrupt:                                                                       # для тестов - если повиснем
        return;



def send_articles():                                                            # "ярлык" для подцепки из apps
    print("- - - служба отправки почты по расписанию запущена - в ожидании ...")
    scheduler = BackgroundScheduler(timezone=TIME_ZONE);                        # ** с этим нужно что то делать (а можно и не делать)
    trigger = CronTrigger(day_of_week="mon", hour="00", minute="10");           # в течение минуты будем пытаться выполнить задачу
    scheduler.add_job(send_mail_subs, trigger, id="subscribers_weekly_routine", max_instances=1, replace_existing=True);
    scheduler.start();


