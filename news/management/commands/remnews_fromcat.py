from django.core.management.base import BaseCommand, CommandError;
from news.models import Post, Category;



class Command(BaseCommand):                                                                         # команда удаления статей определенной категории
    help = f"Удаляет все публикации типа 'статья' из базы данных в указанной категории (теме)";

    def handle(self, *args, **options):
        self.stdout.readable();
        cat_name_input = input("Введите незвание категории, все статьи в которой следует удалить: ");

        if cat_name_input != "":                                                                    # если была введена категория - начнём

            if Category.objects.filter(cat_name = cat_name_input).exists():                         # существуеи ли категория с таким именем? если да - посчитаем,..
                vi_quantity = Post.objects.filter(category = Category.objects.get(cat_name = cat_name_input).id, type = 1).count(); # сколько в ней статей на сайте
                self.stdout.write("База данных содержит " + vi_quantity + " объект(ов) в этой категории. Удалить их? да/нет");

                confirm = input();
                if confirm not in ("да","Да", "ДА"):                                                # просим разрешение на удаление этих статей
                    self.stdout.write(self.style.ERROR("Отмена команды"));
                else:
                    post_to_rem = Post.objects.filter(category = Category.objects.get(cat_name = cat_name_input).id, type = 1);
                    for p in post_to_rem:                                                           # для эфектности удалим все по одной
                        Comments.objects.filter(post_id = p.id).delete();                           # и комменты на эти статьи тоже
                        Post.objects.filter(id = p.id).delete();
                        self.stdout.write(self.style.SUCCESS("статья с id '%s' удалена" % p.id));
                    self.stdout.write(self.style.SUCCESS("\nВсе статьи в указанной категории удалены. Команда выполнена успешно."));

            else:
                self.stdout.write(self.style.ERROR("Категория с таким названием не зарегистрирована на сайте. Отмена команды."));

        else:
            self.stdout.write(self.style.ERROR("Не указано название категории. Отмена команды."));




