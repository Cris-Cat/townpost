# File: events/urls.py

from django.urls import path
from . import views

# App-level URL patterns
urlpatterns = [
    # Home page (Root URL)
    path('', views.home_view, name='home'),
    # Submission form
    path('submit/', views.submit_event_view, name='submit'),
    # Event detail page (captures the slug from the URL)
    path('event/<slug:slug>/', views.event_detail_view, name='event_detail'),
]