from django.contrib import admin
from .models import Author, Category, Comment, Post, User, PostCategory;

admin.site.register(Author);        # занесем таблицы во встроенную админку
admin.site.register(Category);
admin.site.register(Comment);
admin.site.register(Post);
admin.site.register(PostCategory);