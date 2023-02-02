from django.urls import path;
from .views import PostsPreview, PostView;
from django.views.decorators.cache import cache_page;

urlpatterns = [
    path('', PostsPreview.as_view(), name = 'start_page'),
    path('<int:pk>/', PostView.as_view(), name = 'post_view'),
];