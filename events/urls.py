# File: events/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('info/', views.info_board_view, name='info_board'),
    path('submit/', views.submit_event_view, name='submit'),
    path('submit/success/<str:token>/', views.submit_success_view, name='submit_success'),
    
    # --- ADD THIS LINE ---
    path('edit/<str:token>/', views.secret_edit_view, name='secret_edit'),
    
    path('event/<slug:slug>/', views.event_detail_view, name='event_detail'),
]