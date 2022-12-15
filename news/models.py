from django.db import models
from datetime import datetime

from django.contrib.auth.models import User;        # импортируем встроенную будущую таблицу, чтобы хранить в ней данные пользователей

main_p_per_page=4;                                  # количество постов на одну страницу (заглавную и поиска)

class Author(models.Model):                                                             # Таблица с авторами
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Логин");  # - только логин, изначально созданный в таблице User
    rating = models.IntegerField(default=0, verbose_name="Рейтинг автора");             # Рейтинг автора
    class Meta:
        verbose_name="Автор публикаций | Author";
        verbose_name_plural="Авторы публикаций | Author";
    def __str__(self):
        return f"ID={self.id}, Автор {self.user.username} ({self.user.first_name} {self.user.last_name} - id(user)={self.user.id})";
    def update_rating(self):                                                            # Посчитаем рейтинг
        rt=0;
        r_p=Post.objects.filter(author_id=self.id).values('rating');                    # Возьмем набор из Post принадлежащий автору, только поле рейтинг
        for i in range(0,len(r_p)):                                                     # .. и проходя циклом
            rt+=r_p[i]['rating'];                                                       # .. сложим все значения в словарях из набора
        rt*=3;                                                                          # .. и умножим на три.
        r_c=Comment.objects.filter(user_id=Author.objects.get(id=self.id).user_id).values('rating');
        for i in range(0,len(r_c)):                                                     # То же проделаем с написанными им (Автором) комментариями
            rt+=r_c[i]['rating'];                                                       # (но на три уже не умножаем)
        r_s=Post.objects.filter(author_id=self.id).values('id');                        # Теперь посчитаем рейтинг комментариев на все статьи за авторством Автора
        for i in range(0, len(r_s)):                                                    # - сперва получим ID всех статей автора и прогоним через цикл..
            n_s=Comment.objects.filter(post_id=r_s[i]['id']).values('rating');          #..где выберем рейтинг комментов на эту статью
            for p in range(0, len(n_s)):                                                # прогоним набор через цикл и просто сложим все рейтинги
                rt += n_s[p]['rating'];
        self.rating=rt;                                                                 # присвоим новый рейтинг автору
        self.save();                                                                    # сохраним
        return self.rating;                                                             # и вернем ответ запрашивающему сценарию (пока его нет, но будет)

class Category(models.Model):                                                                   # Таблица с категориями новостей
    cat_name = models.CharField(max_length=50, unique=True, verbose_name="Название категории"); # Имя категории (название темы новости) - чтобы без дубликатов
    subscriber = models.ManyToManyField(User, through="CategorySubscriber");                    # Подписчик. Cсылается на пользователя через CategorySubscriber
    class Meta:
        verbose_name="Категория постов | Category";
        verbose_name_plural="Категории постов | Category";
    def __str__(self):
        return f"ID={self.id} | Категория {self.cat_name}";

class Post(models.Model):                                                   # Таблица с новостями (сам пост)
    header = models.CharField(max_length=255);                              # Заголовок
    text = models.TextField();                                              # Тело новости
    rating = models.IntegerField(default=0);                                # рейтинг новости
    type = models.IntegerField(default=0);                                  # Тип: новость или статья. По умолчанию - новость (0)
    m_of_creation = models.DateTimeField(auto_now_add=True);                # Дата и время создания (авто - в момент внесения в базу данных)
    author = models.ForeignKey(Author, on_delete=models.CASCADE);           # Автор. Сотрут автора - все новости под его пером тоже удалятся
    category = models.ManyToManyField(Category, through="PostCategory");    # Категория. Cсылается на Category через PostCategory
    class Meta:
        verbose_name="Публикация (пост) | Post";
        verbose_name_plural="Публикации (посты) | Post";
    def __str__(self):
        return f"ID={self.id}, Пост {self.header[0:20]} | {self.author}";
    def like(self):                                                         # Лайк / дизлайк
        self.rating = self.rating + 1;                                      # Если лайк - лайк +1
        self.save();                                                        # Сохраним его
        return self.rating;                                                 # И сразу вернем новый рейтинг (вдруг в будущем пригодится)
    def dislike(self):                                                      # А если дизлайк -
        self.rating = self.rating - 1;                                      # то вычтем 1. Рейтинг может быть и отрицательным
        self.save();
        return self.rating;                                                 # И тоже покажем обновленный рейтинг

class PostCategory(models.Model):                                                                                   # Помежуточная таблица:
    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name="Публикация");                            # Сотрут пост - запись из этой таблицы исчезнет
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Относится к кат. (в т.ч.)");     # Сотрут тему - исчезнет и здесь и в постах
    class Meta:
        verbose_name="<Пост-категория> | PostCategory";
        verbose_name_plural="<Пост-категория> | PostCategory";
    def __str__(self):
        return f"ID={self.id} | пост id={self.post.id}, категория ID={self.category.id}, - {self.category.cat_name}";

class Comment(models.Model):                                                                    # Таблица с комментариями к статье
    post = models.ForeignKey(Post, on_delete=models.CASCADE);                                   # Ссылка на статью - если последняя удалится, то и коммент тоже
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Логин");             # Автор коммента. Комментатора сотрут - коммент сотрется сам
    text = models.TextField(verbose_name="Текст комментария");                                  # Текст комментария
    m_of_comm = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время создания");  # Авто-дата и время публикации комментария
    rating = models.IntegerField(default=0, verbose_name="Рейтинг комментария");                # рейтинг комментария
    class Meta:
        verbose_name="Комментарий | Comment";
        verbose_name_plural="Комментарии | Comment";
    def __str__(self):
        return f"ID={self.id}, комментарий на пост ID={self.post.id}, автор комментария - {self.user.username}";
    def like(self):                                                 # Лайк / Дизлайк
        self.rating = self.rating + 1;
        self.save();
        return self.rating;
    def dislike(self):
        self.rating = self.rating - 1;
        self.save();
        return self.rating;

class CategorySubscriber(models.Model):                                                                     # Помежуточная таблица с подписчиками:
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name="Категория публикаций");
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Подписчик");
    class Meta:
        verbose_name = "<Подписчик> | CategorySubscriber";
        verbose_name_plural = "<Подписчики> | CategorySubscriber";
    def __str__(self):
        return f"ID={self.id} | категория ID={self.category.id} ({self.category.cat_name}), пользователь ID={self.user.id}";