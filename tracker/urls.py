from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('spending/', views.spending, name='spending'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions, name='transactions'),
    path('categories/', views.categories, name='categories'),
    path('account/', views.account, name='account'),
    path('add_expense/', views.add_expense, name='add_expense'),
    path('add_income/', views.add_income, name='add_income'),
]
