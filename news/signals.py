from .models import Post, User, CategorySubscriber, PostCategory, Category;
from allauth.account.models import EmailAddress;
from django.contrib.auth.models import Group;
from django.db.models.signals import post_save;
from django.db.models import Q;
from datetime import datetime;

from .templatetags.custom_filters import d_normal, censor, html_cnv;
from NewsPaper.settings import DEFAULT_FROM_EMAIL;

from django.core.mail import send_mail, EmailMultiAlternatives;         # для отправки писем
from django.template.loader import render_to_string;

from django.dispatch import receiver;

import smtplib;                                                         # будем ловить эти исключения (и, временно, игнорировать их, чтобы не портить рендер)
from .threads import SubsMailThread;                                    # уберём подтормаживание, послав процедуру отправки почты в отдельный поток






@receiver(post_save, sender=User)
def add_to_authors(sender, instance, created, **kwargs):            # занесение в группу авторов всех вновь зарегистрировавшихся пользователей (в т.ч. из соцсетей)
    if created:
        gauthors = Group.objects.get(name="Authors");               # найдем группу по имени
        instance.groups.add(gauthors);                              # и занесём наш источник возникновения события в неё



@receiver(post_save, sender=Post)
def alert_subscribers_news(sender, instance, created, **kwargs):
    if created:                                                                                 # обработчик события - создание публикации

        category_list = [int(cat) for cat in instance.n_category];                              # преобразуем список id категорий в числовой тип
        mail_list = [];                                                                         # подготовим пакет данных для вывода в поток

        if instance.type in [1]:                                            # ТАК, тут меняем (в последнем задании тип-НОВОСТЬ отменяется - только тип СТАТЬЯ)
            pub_name = "новость" if instance.type == 0 else "статья";               # но заготовки всё же оставим
            pub_path = "news" if instance.type == 0 else "news";                    # тут тоже немного поменяем для тестов, временно
            recip_set = CategorySubscriber.objects.filter(~Q(user_id=instance.author.user.id),
            category_id__in=category_list).order_by('user_id').values('user').distinct();       # возьмём список всех подписчиков, кроме самого автора

            for rid in recip_set:
                recip = User.objects.get(id=rid['user'], is_active=1);                          # возьмём данные очередного получателя письма
                cats = [];                                                                      # список категорий, на которые он подписан
                if recip.email != "":                                               # Заполнено поле e-mail? Всякое возможно, подстрахуемся
                    category_names=[];
                    for i in range(0, len(category_list)):                          # заполним список названиями категорий текущей публикации
                        category_names.append(Category.objects.get(id=category_list[i]).cat_name);
                    name = recip.username if recip.username != "" else recip.email; # ** сейчас в БД небольшой бардак, есть тестовые - поэтому потом убрать
                    cats_set = CategorySubscriber.objects.filter(user_id=recip.id);

                    for cat in cats_set:
                        if str(cat.category.id) in instance.n_category:             # если категории его подписок совпадают с категориями публикации -
                            cats.append(cat.category.cat_name);                     # занесем их в список, чтобы не дезинформировать человека в теме письма

                    mail_list.append([recip.email, name, cats, instance.author.user.username,
                    instance.author.user.email, pub_name, pub_path, instance.id, instance.header,
                    instance.text, instance.type, category_names]);                 # запишем собранные данные в виде списка в список всех получателей

            if (len(mail_list)) > 0:                                                # если в списке что то есть (ошибок набора не было) -
                SubsMailThread(mail_list).start();                                  # - то отправим его в поток а заодно и сразу запустим этот поток



@receiver(post_save, sender=EmailAddress)
def send_greetings(sender, instance, created, **kwargs):                            # пошлем приветственное письмо после подтверждения email
    if not created:
        if instance.verified == 1:
            rec_email = instance.email;
            html_par = {'email': rec_email};
            html_out = render_to_string("mail/welcome.html", html_par);
            msg = EmailMultiAlternatives(
                subject = f'Новостной портал: добро пожаловать!',
                body = f"Здравствуйте, {rec_email}!\r\nВы успешно зарегистрировались на сайте 'Новостной портал'.\r\nТеперь можете идти на сайт и читать статьи.",
                from_email = DEFAULT_FROM_EMAIL,
                to = [rec_email]
            );
            msg.attach_alternative(html_out, "text/html");
            try:
                msg.send();
            except smtplib.SMTPDataError:
                pass;