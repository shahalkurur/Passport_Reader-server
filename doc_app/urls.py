
from django.urls import path
from .views import ExtractInfoView

urlpatterns = [
    path('api/extract-info', ExtractInfoView.as_view(), name='extract-info')
]
