from django.urls import path
from .import views
urlpatterns =[
    path('register/',views.register,name='register'),
    path('login/',views.login_view,name='login'),
    path('logout/',views.logout_view,name='logout'),
    path('',views.index,name='index'),
    path('log-food/',views.log_food,name='log_food'),
    path('history/',views.history,name='history'),
    path('profile/',views.profile,name='profile'),
    path('delete/<int:id>/',views.delete_consume,name='delete'),
]