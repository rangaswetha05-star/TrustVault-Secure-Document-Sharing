from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('upload/', views.upload_document, name='upload'),
    path('share/<int:document_id>/', views.share_document, name='share_document'),
    path('view/<int:document_id>/', views.view_document, name='view_document'),
    path('edit/<int:document_id>/', views.edit_document, name='edit_document'),
    path(
    'revoke/<int:document_id>/<int:user_id>/',
    views.revoke_access,
    name='revoke_access'
),
    path(
    'download/<int:document_id>/',
    views.download_document,
    name='download_document'
),
    path(
    'activity-history/',
    views.activity_history,
    name='activity_history'
),
]