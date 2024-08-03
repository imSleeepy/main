from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.say_hello),
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('uploaddocument/', views.uploaddocument, name='uploaddocument'),    
    path('proccessedimages/', views.proccessedimages, name='proccessedimages'),
    path('save_extracted_data/', views.save_extracted_data, name='save_extracted_data'),
    path('save_extracted_data2/<int:pk>/', views.save_extracted_data2, name='save_extracted_data2'),
    path('details/<int:pk>/', views.view_details, name='view_details'),
    path('delete/<int:pk>/', views.delete_details, name='delete_details'),
    path('logout/', views.logout, name='logout'), 
]

