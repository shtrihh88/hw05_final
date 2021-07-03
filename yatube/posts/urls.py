from django.urls import path

from . import views

app_name = 'posts'


urlpatterns = [
    path('', views.index, name='index'),
    path('404/', views.page_not_found, name='error_404'),
    path('500/', views.server_error, name='error_500'),
    path('group/<slug:slug>/', views.group_posts, name='group_posts'),
    path('new/', views.new_post, name='new_post'),
    path('follow/', views.follow_index, name='follow_index'),
    path('<str:username>/', views.profile, name='profile'),
    path('<str:username>/<int:post_id>/', views.post_view, name='post'),
    path('<str:username>/<int:post_id>/edit/', views.post_edit, name='edit'),
    path(
        '<str:username>/<int:post_id>/comment/',
        views.add_comment,
        name='add_comment'
    ),

    path(
        '<str:username>/follow/',
        views.profile_follow,
        name='profile_follow'
    ),
    path(
        '<str:username>/unfollow/',
        views.profile_unfollow,
        name='profile_unfollow'
    )
]
