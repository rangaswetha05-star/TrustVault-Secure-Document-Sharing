from django import forms
from .models import Document, DocumentPermission


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'file']


class DocumentPermissionForm(forms.ModelForm):
    class Meta:
        model = DocumentPermission
        fields = ['user', 'can_view', 'can_edit']