import threading;
from django.core.mail import send_mail, EmailMultiAlternatives;
from django.template.loader import render_to_string;
from .templatetags.custom_filters import d_normal, censor, html_cnv;
from NewsPaper.settings import DEFAULT_FROM_EMAIL;
from datetime import datetime;
#from time import sleep;
import smtplib;



class SubsMailThread(threading.Thread):             # поток для отправки рассылки по созданию публикации
    def __init__(self, mail_set):
        self.mail_set = mail_set;
        threading.Thread.__init__(self);

    def run(self):
        for rcp in range(0, len(self.mail_set)):    # один элемент списка - это ещё один список с данными получателя рассылки
            recip_email = self.mail_set[rcp][0];    # разберем этого получателя в цикле на отдельные переменные
            name = self.mail_set[rcp][1];
            cats = self.mail_set[rcp][2];
            in_username = self.mail_set[rcp][3];
            in_email = self.mail_set[rcp][4];
            pub_name = self.mail_set[rcp][5];
            pub_path = self.mail_set[rcp][6];
            in_id = self.mail_set[rcp][7];
            in_header = self.mail_set[rcp][8];
            in_text = self.mail_set[rcp][9];
            in_type = self.mail_set[rcp][10];
            category_names = self.mail_set[rcp][11];

            str_text = f"твоём любимом разделе ({html_cnv(cats[0])})" if len(cats) == 1 else f"твоих любимых разделах ({html_cnv(', '.join(cats))})";
            text_head = f'Здравствуй, <b>{html_cnv(name)}</b>. Новая {pub_name} в {str_text}!';
            str_text_i = f"твоём любимом разделе ({cats[0]})" if len(cats) == 1 else f"твоих любимых разделах ({', '.join(cats)})";     # без html-тегов
            text_head_i = f'Здравствуй, {name}. Новая {pub_name} в {str_text}!';    # то же, что и text_head, только без html-тегов (для текстового варианта)
            author = in_username if in_username else in_email;
            n_text = f"{in_text[0:50]} ...";
            s_link = f"http://127.0.0.1:8000/{pub_path}/{in_id}/";
            n_title, n_text = censor(in_header), censor(n_text);                    # применим матофильтр

            text_ins = {                                                            # подготовим переменные для шаблона ...
                'header_title': 'Document',
                'name': html_cnv(name),                                             # ... и преобразуем потенциально опасные символы в них в безопасные
                'title': html_cnv(n_title),
                'tags': html_cnv(", ".join(category_names)),
                'text_header': text_head,
                'text': html_cnv(n_text),
                'author': html_cnv(author),
                'email': html_cnv(recip_email),
                'link': s_link,
                'type': pub_name
            };

            html_out = render_to_string("mail/mailsubs.html", text_ins);            # наполним содержимое страницы шаблона нашими переменными
            pub_what = "новости" if in_type == 0 else "статьи";
            text_out = f"\r\nНовостной портал\r\n\r\n{text_head_i}\r\n\r\nДата: {str(datetime.now().strftime('%d.%m.%Y %H:%M:%S'))}" \
                       f"\r\n\r\n{n_title}\r\n\r\n{n_text}\r\n\r\nПолный текст {pub_what} можно прочитать, перейдя по ссылкае: " \
                       f"http://127.0.0.1:8000/{pub_path}/{in_id}/";                # делаем текстовый вариант письма (не html)

            msg = EmailMultiAlternatives(
                subject=f'Новая {pub_name} на Новостном портале: {n_title}',    # ** масло масляное (если новая новость) - подумать, позже исправить
                body=text_out,
                from_email=DEFAULT_FROM_EMAIL,
                to=[recip_email]                                        # список, но адрес только один, чтобы получатели не видели адреса друг-друга
            );
            msg.attach_alternative(html_out, "text/html");              # прикрепляем html-вариант письма
            try:
                msg.send();                                             # пытаемся отправить письмо
            except smtplib.SMTPDataError:
                pass;                                                   # ... пойдет для тестов. иначе форма в шаблоне не сработает и повиснет JS
            except KeyboardInterrupt:                                   # если надоело ждать
                return;




