from django.urls import path
from . import views

urlpatterns = [
    path('', views.court_list, name='court_list'),
    path('<int:pk>/', views.court_detail, name='court_detail'),
    path('create/', views.court_create, name='court_create'),
    path('<int:pk>/edit/', views.court_edit, name='court_edit'),
    path('<int:pk>/delete/', views.court_delete, name='court_delete'),
    path('<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('<int:pk>/report/', views.report_court, name='report_court'),
    path('favorites/', views.favorite_list, name='favorite_list'),
]
