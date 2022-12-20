from .models import Post, User, CategorySubscriber, PostCategory, Category;
from celery import shared_task;
from django.db.models import Q;
from django.core.mail import send_mail, EmailMultiAlternatives;
from django.template.loader import render_to_string;
from .templatetags.custom_filters import d_normal, censor, html_cnv, post_author;
from NewsPaper.settings import DEFAULT_FROM_EMAIL;
from datetime import datetime;
import smtplib;
#import time;


@shared_task
def send_news_announcement(id, cat, user):                      # отправка анонса при создании публикации типа НОВОСТЬ
    if type(id) == int and type(cat) == list:                   # подстрахуемся от фальшстартов, дальше - как обычно
        if id > 0:

            category_list = [int(c) for c in cat];
            pub_name, pub_path = "новость", "news";
            recip_set = CategorySubscriber.objects.filter(~Q(user_id=user),
            category_id__in=category_list).order_by('user_id').values('user').distinct();
            post_set = Post.objects.get(id = id);
            author = post_author(post_set.author_id);
            pubdate = str(datetime.now().strftime('%d.%m.%Y %H:%M:%S'));

            for rid in recip_set:
                recip = User.objects.get(id=rid['user'], is_active=1);
                cats = [];
                mail_list = [];
                if recip.email != "":
                    category_names=[];
                    for i in range(0, len(category_list)):
                        category_names.append(Category.objects.get(id=category_list[i]).cat_name);
                    name = recip.username if recip.username != "" else recip.email; # **
                    cats_set = CategorySubscriber.objects.filter(user_id=recip.id);

                    for cat in cats_set:
                        if int(cat.category.id) in category_list:
                            cats.append(cat.category.cat_name);

                    str_text = f"твоём любимом разделе ({html_cnv(cats[0])})" if len(cats) == 1 else f"твоих любимых разделах ({html_cnv(', '.join(cats))})";
                    text_head = f'Здравствуй, <b>{html_cnv(name)}</b>. Новая {pub_name} в {str_text}!';
                    str_text_i = f"твоём любимом разделе ({cats[0]})" if len(cats) == 1 else f"твоих любимых разделах ({', '.join(cats)})";
                    text_head_i = f'Здравствуй, {name}. Новая {pub_name} в {str_text}!';
                    n_text = f"{post_set.text[0:50]} ...";
                    s_link = f"http://127.0.0.1:8000/{pub_path}/{id}/";
                    n_title, n_text = censor(post_set.header), censor(n_text);

                    text_ins = {
                        'header_title': 'Document',
                        'name': html_cnv(name),
                        'title': html_cnv(n_title),
                        'tags': html_cnv(", ".join(category_names)),
                        'text_header': text_head,
                        'text': html_cnv(n_text),
                        'author': html_cnv(author),
                        'email': html_cnv(recip.email),
                        'link': s_link,
                        'type': pub_name
                    };

                    html_out = render_to_string("mail/mailsubs.html", text_ins);
                    pub_what = "новости";
                    text_out = f"\r\nНовостной портал\r\n\r\n{text_head_i}\r\n\r\nДата: {pubdate}" \
                               f"\r\n\r\n{n_title}\r\n\r\n{n_text}\r\n\r\nПолный текст {pub_what} можно прочитать, перейдя по ссылкае: " \
                               f"http://127.0.0.1:8000/{pub_path}/{id}/";

                    msg = EmailMultiAlternatives(
                        subject=f'Новая {pub_name} на Новостном портале: {n_title}',
                        body=text_out,
                        from_email=DEFAULT_FROM_EMAIL,
                        to=[recip.email]
                    );
                    msg.attach_alternative(html_out, "text/html");
                    try:
                        msg.send();
                    except smtplib.SMTPDataError or smtplib.SMTPConnectError:           # часто стали добавлять в спам. лучше этого не видеть (и так всё ясно)
                        pass;




@shared_task
def send_spam():                                                                    # отправка подписчикам еженедельной рассылки новостей
    pub_name, pub_name_a, pub_name_b = "новость", "новости", "новостей";
    days_now = datetime.now();
    days_then = days_now - timedelta(7);
    rec_set = CategorySubscriber.objects.all().values('user').order_by('user_id').distinct();
    for rec in rec_set:
        user_data = User.objects.get(id=rec['user']);
        rec_name = user_data.username if user_data.username != "" else user_data.email;
        rec_email = user_data.email;
        if rec_email != "":
            inter_set_id = [];
            inter_set_name = [];
            cats_set = CategorySubscriber.objects.filter(user=rec['user']).values('category').order_by('category');
            for n in cats_set:
                inter_set_id.append(n['category']);
                inter_set_name.append(Category.objects.get(id=n['category']).cat_name);
            middle_content = f"Здравствуйте, <b>{rec_name}</b>! Вы подписались на разделы {', '.join(inter_set_name)}.<br>" \
            f"Вот подборка {pub_name_b} по Вашим интересам за прошедшую неделю:<br><br>";
            text_out = f"Здравствуйте, {rec_name}! Вы подписались на разделы {', '.join(inter_set_name)}.\r\n" \
            f"Вот подборка {pub_name_b} по Вашим интересам за прошедшую неделю:\r\n\r\n";
            post_set = Post.objects.filter(category__in=inter_set_id, type=0,
            m_of_creation__range=(days_then,days_now)).values('header','m_of_creation','id','author').order_by('id').distinct();
            for p in post_set:
                author = User.objects.get(id=Author.objects.get(id=p['author']).user_id).username;
                middle_content += f"<b>{str(p['m_of_creation'].strftime('%d.%m.%Y %H:%M:%S'))}</b>&nbsp;&nbsp;Автор <b>{html_cnv(author)}</b><br>" \
                f"&laquo;{html_cnv(censor(p['header']))}&raquo;<br><a href='http://127.0.0.1:8000/news/{p['id']}/'>полный текст</a><br><br>";
                text_out += f"{str(p['m_of_creation'].strftime('%d.%m.%Y %H:%M:%S'))} Автор {html_cnv(author)}\r\n" \
                f"{censor(p['header'])}\r\nполный текст {pub_name_a} можно почитать по ссылке: http://127.0.0.1:8000/news/{p['id']}/\r\n\r\n";
            html_par = {'text':middle_content};
            html_out = render_to_string("mail/mweekly.html", html_par);
            msg = EmailMultiAlternatives(
                subject=f'Новостной портал: список {pub_name_b} по избранным темам за неделю',
                body=text_out,
                from_email=DEFAULT_FROM_EMAIL,
                to=[rec_email]
            );
            msg.attach_alternative(html_out, "text/html");
            try:
                msg.send();
            except smtplib.SMTPDataError or smtplib.SMTPConnectError:
                pass;

