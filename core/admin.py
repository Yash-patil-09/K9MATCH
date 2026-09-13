from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, DogProfile, DogImage, MatchRequest, ChatMessage, VeterinaryClinic

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'is_verified', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('K9Match Custom Fields', {'fields': ('role', 'phone_number', 'is_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('K9Match Custom Fields', {'fields': ('role', 'phone_number', 'is_verified')}),
    )

class DogImageInline(admin.TabularInline):
    model = DogImage
    extra = 1

@admin.register(DogProfile)
class DogProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'breed', 'gender', 'city', 'approval_badge', 'kci_registered', 'kci_doc_link', 'is_available', 'created_at']
    list_filter = ['approval_status', 'is_available', 'kci_registered', 'gender', 'breed', 'mating_terms']
    search_fields = ['name', 'breed', 'city', 'owner__username', 'kci_number']
    inlines = [DogImageInline]
    actions = ['approve_selected_dogs', 'reject_selected_dogs']

    @admin.action(description="✅ Approve selected dog profiles")
    def approve_selected_dogs(self, request, queryset):
        updated = queryset.update(approval_status='approved', admin_rejection_reason='')
        self.message_user(request, f"{updated} dog profile(s) successfully approved!")

    @admin.action(description="❌ Reject selected dog profiles")
    def reject_selected_dogs(self, request, queryset):
        updated = queryset.update(approval_status='rejected', admin_rejection_reason='Rejected via batch admin review.')
        self.message_user(request, f"{updated} dog profile(s) marked as rejected.")

    def approval_badge(self, obj):
        if obj.approval_status == 'approved':
            return format_html('<span style="color: #16a34a; font-weight: 700;">● Approved</span>')
        elif obj.approval_status == 'rejected':
            return format_html('<span style="color: #dc2626; font-weight: 700;">● Rejected</span>')
        return format_html('<span style="color: #ea580c; font-weight: 700;">● Pending Review</span>')
    approval_badge.short_description = 'Approval Status'

    def kci_doc_link(self, obj):
        if obj.kci_document:
            return format_html('<a href="{}" target="_blank" style="color: #2563eb; font-weight: 600;">📄 Certificate</a>', obj.kci_document.url)
        return "-"
    kci_doc_link.short_description = 'KCI File'


@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'sender', 'receiver', 'target_dog', 'sender_dog', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__username', 'receiver__username', 'target_dog__name', 'sender_dog__name']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'match', 'sender', 'message', 'is_edited', 'is_deleted', 'timestamp']
    list_filter = ['is_edited', 'is_deleted', 'timestamp']
    search_fields = ['sender__username', 'message']


@admin.register(VeterinaryClinic)
class VeterinaryClinicAdmin(admin.ModelAdmin):
    list_display = ['name', 'doctor_name', 'city', 'state', 'phone_number', 'is_24x7_emergency', 'rating']
    list_filter = ['is_24x7_emergency', 'state', 'city']
    search_fields = ['name', 'doctor_name', 'city', 'specialization']


admin.site.register(User, CustomUserAdmin)