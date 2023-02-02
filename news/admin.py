from django.contrib import admin;
from .models import Author, Category, Comment, Post, User, PostCategory;



class AuthorAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'user', 'rating'];
    search_fields = ('user',);



class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'cat_name'];
    search_fields = ('cat_name',);



class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'post_id', 'm_of_comm', 'user'];
    list_filter = ('user',);
    search_fields = ('text',);



class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'm_of_creation', 'author', 'header'];
    list_filter = ('type', 'author');
    search_fields = ('header', 'text');



class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'post_id'];



admin.site.register(Author, AuthorAdmin);               # занесем таблицы во встроенную админку
admin.site.register(Category, CategoryAdmin);
admin.site.register(Comment, CommentAdmin);
admin.site.register(Post, PostAdmin);
admin.site.register(PostCategory, PostCategoryAdmin);