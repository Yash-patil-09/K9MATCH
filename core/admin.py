from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DogProfile, DogImage

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
    extra = 3  # Provides 3 photo upload slots by default in Admin

@admin.register(DogProfile)
class DogProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'breed', 'gender', 'city', 'kci_registered', 'is_available', 'owner']
    list_filter = ['gender', 'breed', 'kci_registered', 'is_available', 'mating_terms', 'shelter_provider', 'travel_range']
    search_fields = ['name', 'breed', 'city', 'owner__username']
    inlines = [DogImageInline]

admin.site.register(User, CustomUserAdmin)