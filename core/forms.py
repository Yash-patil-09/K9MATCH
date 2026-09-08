from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from .models import User, DogProfile, DogImage

# --- User Registration Form ---
phone_regex = RegexValidator(
    regex=r'^\d{10}$',
    message="Phone number must be exactly 10 digits (e.g. 9876543210)."
)

class CustomUserCreationForm(UserCreationForm):
    phone_number = forms.CharField(
        validators=[phone_regex],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 10-digit phone number',
            'maxlength': '10',
        }),
        required=True
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'phone_number')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

ALL_BREEDS = [
    ('Affenpinscher', 'Affenpinscher'), ('Afghan Hound', 'Afghan Hound'), ('Airedale Terrier', 'Airedale Terrier'),
    ('Akita', 'Akita'), ('Alaskan Malamute', 'Alaskan Malamute'), ('American Bully', 'American Bully'),
    ('American Pit Bull Terrier', 'American Pit Bull Terrier'), ('Beagle', 'Beagle'), ('Boxer', 'Boxer'),
    ('Bulldog', 'Bulldog'), ('Cane Corso', 'Cane Corso'), ('Chihuahua', 'Chihuahua'), ('Cocker Spaniel', 'Cocker Spaniel'),
    ('Dachshund', 'Dachshund'), ('Doberman Pinscher', 'Doberman Pinscher'), ('French Bulldog', 'French Bulldog'),
    ('German Shepherd', 'German Shepherd'), ('Golden Retriever', 'Golden Retriever'), ('Great Dane', 'Great Dane'),
    ('Indie / Native Breed', 'Indie / Native Breed'), ('Labrador Retriever', 'Labrador Retriever'),
    ('Lhasa Apso', 'Lhasa Apso'), ('Maltese', 'Maltese'), ('Pomeranian', 'Pomeranian'), ('Poodle', 'Poodle'),
    ('Pug', 'Pug'), ('Rottweiler', 'Rottweiler'), ('Saint Bernard', 'Saint Bernard'), ('Shih Tzu', 'Shih Tzu'),
    ('Siberian Husky', 'Siberian Husky'), ('Tibetan Mastiff', 'Tibetan Mastiff'), ('Other', 'Other / Custom')
]
PUREBRED_CHOICES = [
    ('', 'Select Purebred Dog Breed...'),
    ('Affenpinscher', 'Affenpinscher'), ('Afghan Hound', 'Afghan Hound'), ('Airedale Terrier', 'Airedale Terrier'),
    ('Akita', 'Akita'), ('Alaskan Malamute', 'Alaskan Malamute'), ('American Bully', 'American Bully'),
    ('American Pit Bull Terrier', 'American Pit Bull Terrier'), ('Australian Shepherd', 'Australian Shepherd'),
    ('Beagle', 'Beagle'), ('Bernese Mountain Dog', 'Bernese Mountain Dog'), ('Bichon Frise', 'Bichon Frise'),
    ('Border Collie', 'Border Collie'), ('Boston Terrier', 'Boston Terrier'), ('Boxer', 'Boxer'),
    ('Bullmastiff', 'Bullmastiff'), ('Cane Corso', 'Cane Corso'), ('Cavalier King Charles Spaniel', 'Cavalier King Charles Spaniel'),
    ('Chihuahua', 'Chihuahua'), ('Chow Chow', 'Chow Chow'), ('Cocker Spaniel', 'Cocker Spaniel'),
    ('Dachshund', 'Dachshund'), ('Dalmatian', 'Dalmatian'), ('Doberman Pinscher', 'Doberman Pinscher'),
    ('English Bulldog', 'English Bulldog'), ('French Bulldog', 'French Bulldog'), ('German Shepherd', 'German Shepherd'),
    ('Golden Retriever', 'Golden Retriever'), ('Great Dane', 'Great Dane'), ('Great Pyrenees', 'Great Pyrenees'),
    ('Greyhound', 'Greyhound'), ('Indie / Native Breed', 'Indie / Native Breed'), ('Jack Russell Terrier', 'Jack Russell Terrier'),
    ('Labrador Retriever', 'Labrador Retriever'), ('Lhasa Apso', 'Lhasa Apso'), ('Maltese', 'Maltese'),
    ('Miniature Pinscher', 'Miniature Pinscher'), ('Pekingese', 'Pekingese'), ('Pomeranian', 'Pomeranian'),
    ('Poodle (Standard)', 'Poodle (Standard)'), ('Poodle (Toy)', 'Poodle (Toy)'), ('Pug', 'Pug'),
    ('Rottweiler', 'Rottweiler'), ('Saint Bernard', 'Saint Bernard'), ('Samoyed', 'Samoyed'),
    ('Shih Tzu', 'Shih Tzu'), ('Siberian Husky', 'Siberian Husky'), ('Tibetan Mastiff', 'Tibetan Mastiff'),
    ('Whippet', 'Whippet'), ('Other', 'Other Purebred')
]

# --- Dog Profile & Photo Forms ---
class DogProfileForm(forms.ModelForm):
    YES_NO_CHOICES = [(True, 'Yes'), (False, 'No')]

    is_vaccinated = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        coerce=lambda x: x == 'True',
        required=True,
        label="Fully Vaccinated *"
    )

    kci_registered = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        coerce=lambda x: x == 'True',
        required=True,
        label="KCI Registered *"
    )
    secondary_breed = forms.CharField(required=False)
    kci_number = forms.CharField(required=False)
    kci_document = forms.FileField(required=False)
    stud_fee_amount = forms.DecimalField(required=False)
    class Meta:
        model = DogProfile
        fields = [
            'name', 'breed_type', 'breed', 'secondary_breed', 'age_years', 'age_months', 'gender', 'state', 'city',
            'weight_unit', 'weight',
            'is_vaccinated', 'medical_history',
            'kci_registered', 'kci_number', 'kci_document', 'lineage_details',
            'previous_litters', 'mating_terms', 'stud_fee_amount', 'shelter_provider', 'travel_range',
            'dog_friendly_rating', 'human_friendly_rating', 'energy_level_rating',
            'bio', 'is_available'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Rocky'}),
            'breed_type': forms.Select(attrs={'class': 'form-select', 'id': 'breed-type-select'}),
            'breed': forms.TextInput(attrs={'class': 'form-control d-none', 'id': 'breed-hidden-input'}),
            'secondary_breed': forms.TextInput(attrs={'class': 'form-control d-none', 'id': 'secondary-breed-hidden-input'}),
            'age_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'age_months': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 11}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'state': forms.Select(attrs={'class': 'form-select search-select', 'id': 'state-select'}),
            'city': forms.Select(attrs={'class': 'form-select search-select', 'id': 'city-select'}),
            'weight_unit': forms.Select(attrs={'class': 'form-select'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 28.5', 'step': '0.1'}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'kci_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter official KCI registration number'}),
            'kci_document': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,image/*'}),
            'lineage_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'previous_litters': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'mating_terms': forms.Select(attrs={'class': 'form-select', 'id': 'mating-terms-select'}),
            'stud_fee_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 15000'}),
            'shelter_provider': forms.Select(attrs={'class': 'form-select'}),
            'travel_range': forms.Select(attrs={'class': 'form-select'}),
            'dog_friendly_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'human_friendly_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'energy_level_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# Helper form for uploading multiple dog photos
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-control', 'multiple': True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)

class DogImageForm(forms.Form):
    images = MultipleFileField(required=False, help_text="Upload 1 or more photos of your dog")