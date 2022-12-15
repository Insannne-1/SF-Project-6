from django.urls import path;
from .views import PostsPreview, PostView;


urlpatterns = [
    path('', PostsPreview.as_view()),
    path('<int:pk>/', PostView.as_view()),
];