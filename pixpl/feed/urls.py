from django.urls import path
from .views import *

urlpatterns = [
    path('', FeedView.as_view(), name='feed-create'),
    path('<int:feed_id>/', FeedDetailView.as_view(), name='feed-detail'),
    path('<int:feed_id>/picks', FeedPickToggleView.as_view(), name='feed-pick') 
]