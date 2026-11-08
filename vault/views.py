from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models import Q
from django.http import FileResponse
from django.views.decorators.http import require_POST

from .models import (
    Document,
    DocumentPermission,
    UserProfile,
    ActivityLog
)

from .forms import DocumentForm, DocumentPermissionForm


# Activity Logging Function
def log_activity(user, document, action):
    ActivityLog.objects.create(
        user=user,
        document=document,
        action=action
    )


# Home Page
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    return render(request, 'vault/login.html')


# User Registration
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            UserProfile.objects.get_or_create(
                user=user,
                defaults={'role': 'VIEWER'}
            )

            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, 'vault/register.html', {'form': form})


# User Login
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('dashboard')

        messages.error(request, 'Invalid username or password.')

    return render(request, 'vault/login.html')


# Dashboard and Search
@login_required
def dashboard(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'role': 'VIEWER'}
    )

    search_query = request.GET.get('q', '').strip()

    documents = Document.objects.filter(owner=request.user)

    shared_documents = Document.objects.filter(
        documentpermission__user=request.user,
        documentpermission__can_view=True
    ).exclude(owner=request.user).distinct()

    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )

        shared_documents = shared_documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query)
        )

    return render(request, 'vault/dashboard.html', {
        'profile': profile,
        'role': profile.role,
        'documents': documents,
        'shared_documents': shared_documents,
        'search_query': search_query
    })


# User Logout
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# Upload Document
@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)

        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            document.save()

            log_activity(
                request.user,
                document,
                "Document uploaded"
            )

            messages.success(
                request,
                'Document uploaded successfully!'
            )

            return redirect('dashboard')
    else:
        form = DocumentForm()

    return render(request, 'vault/upload.html', {'form': form})


# Share Document
@login_required
def share_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    if document.owner != request.user:
        messages.error(request, "Permission denied!")
        return redirect('dashboard')

    if request.method == 'POST':
        form = DocumentPermissionForm(request.POST)

        if form.is_valid():
            user = form.cleaned_data['user']

            if user == request.user:
                messages.error(
                    request,
                    "You cannot share a document with yourself."
                )
            else:
                DocumentPermission.objects.update_or_create(
                    document=document,
                    user=user,
                    defaults={
                        'can_view': form.cleaned_data['can_view'],
                        'can_edit': form.cleaned_data['can_edit']
                    }
                )

                log_activity(
                    request.user,
                    document,
                    "Document shared or permissions updated"
                )

                messages.success(
                    request,
                    "Permissions updated successfully!"
                )

                return redirect('dashboard')
    else:
        form = DocumentPermissionForm()

    return render(request, 'vault/share_document.html', {
        'form': form,
        'document': document
    })


# View Document
@login_required
def view_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    is_owner = document.owner == request.user

    has_permission = DocumentPermission.objects.filter(
        document=document,
        user=request.user,
        can_view=True
    ).exists()

    if not is_owner and not has_permission:
        messages.error(
            request,
            "You don't have permission to view this document."
        )
        return redirect('dashboard')

    log_activity(
        request.user,
        document,
        "Document viewed"
    )

    return render(request, 'vault/view_document.html', {
        'document': document
    })


# Edit Document
@login_required
def edit_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    is_owner = document.owner == request.user

    has_permission = DocumentPermission.objects.filter(
        document=document,
        user=request.user,
        can_edit=True
    ).exists()

    if not is_owner and not has_permission:
        messages.error(
            request,
            "You don't have edit permission."
        )
        return redirect('dashboard')

    if request.method == 'POST':
        form = DocumentForm(
            request.POST,
            request.FILES,
            instance=document
        )

        if form.is_valid():
            form.save()

            log_activity(
                request.user,
                document,
                "Document edited"
            )

            messages.success(
                request,
                "Document updated successfully!"
            )

            return redirect('dashboard')
    else:
        form = DocumentForm(instance=document)

    return render(request, 'vault/edit_document.html', {
        'form': form,
        'document': document
    })


# Revoke Document Access
@login_required
@require_POST
def revoke_access(request, document_id, user_id):
    document = get_object_or_404(
        Document,
        id=document_id,
        owner=request.user
    )

    permission = get_object_or_404(
        DocumentPermission,
        document=document,
        user_id=user_id
    )

    permission.delete()

    log_activity(
        request.user,
        document,
        "Document access revoked"
    )

    messages.success(
        request,
        "Access revoked successfully!"
    )

    return redirect('dashboard')


# Download Document
@login_required
def download_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    is_owner = document.owner == request.user

    has_permission = DocumentPermission.objects.filter(
        document=document,
        user=request.user,
        can_view=True
    ).exists()

    if not is_owner and not has_permission:
        messages.error(
            request,
            "You don't have permission to download this document."
        )
        return redirect('dashboard')

    log_activity(
        request.user,
        document,
        "Document downloaded"
    )

    return FileResponse(
        document.file.open('rb'),
        as_attachment=True,
        filename=document.file.name.split('/')[-1]
    )
@login_required
def activity_history(request):
    activities = ActivityLog.objects.filter(
        document__owner=request.user
    ).order_by('-timestamp')

    return render(request, 'vault/activity_history.html', {
        'activities': activities
    })    