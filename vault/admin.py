from django.contrib import admin
from .models import UserProfile, Document, DocumentPermission

admin.site.register(UserProfile)
admin.site.register(Document)
admin.site.register(DocumentPermission)