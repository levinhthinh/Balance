from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('account/create/', views.create_account, name='create_account'),
    path('account/<int:account_id>/', views.account_detail, name='account_detail'),
    path('account/<int:account_id>/transaction/', views.make_transaction, name='make_transaction'),
    path('account/<int:account_id>/transfer/', views.make_transfer, name='make_transfer'),
    path('account/<int:account_id>/goal/', views.create_goal, name='create_goal'),
]
