from django.contrib import admin
from django.urls import path, include;
from news.views import ShortSearch, CreateNews, EditNews, RemNews;


urlpatterns = [
    path('admin/', admin.site.urls),
    path('pages/', include('django.contrib.flatpages.urls')),
    path('news/', include('news.urls')),                            # пока что основная страница
    path('articles/', include('news.urls')),
    path('', include('news.urls')),                                 # ВРЕМЕННО - чтобы каждый раз не вбивать news
    path('search/', ShortSearch.as_view()),                         # страница с результатами поиска и формой детального поиска
    path('news/create/', CreateNews.as_view()),                     # создание новости
    path('articles/create/', CreateNews.as_view()),                 # создание статьи
    path('news/<int:pk>/edit/', EditNews.as_view()),                # изменение новости
    path('articles/<int:pk>/edit/', EditNews.as_view()),            # изменение статьи
    path('news/<int:pk>/delete/', RemNews.as_view()),               # удаление новости
    path('articles/<int:pk>/delete/', RemNews.as_view()),           # удаление статьи
#    path('accounts/', include('django.contrib.auth.urls')),         # аккаунты пользователей
#    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
];

