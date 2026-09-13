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
    username = forms.CharField(
        max_length=50,
        help_text="Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'maxlength': '50',
        }),
        required=True
    )
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

CROSSBREED_CHOICES = [
    ('', 'Select Crossbreed / Mix...'),
    ('Airedoodle', 'Airedoodle (Airedale Terrier + Poodle)'),
    ('Aussiedoodle', 'Aussiedoodle (Australian Shepherd + Poodle)'),
    ('Aussiepoo', 'Aussiepoo (Australian Shepherd + Poodle)'),
    ('Baskerville', 'Baskerville (Basset Hound + Beagle)'),
    ('Beaglier', 'Beaglier (Beagle + Cavalier King Charles)'),
    ('Bernedoodle', 'Bernedoodle (Bernese Mountain Dog + Poodle)'),
    ('Bichpoo', 'Bichpoo / Poochon (Bichon Frise + Poodle)'),
    ('Bordoodle', 'Bordoodle (Border Collie + Poodle)'),
    ('Boxerdoodle', 'Boxerdoodle (Boxer + Poodle)'),
    ('Bullpug', 'Bullpug (English Bulldog + Pug)'),
    ('Cavachon', 'Cavachon (Cavalier King Charles + Bichon Frise)'),
    ('Cavapoo', 'Cavapoo / Cavoodle (Cavalier King Charles + Poodle)'),
    ('Chiweenie', 'Chiweenie (Chihuahua + Dachshund)'),
    ('Chorkie', 'Chorkie (Chihuahua + Yorkie)'),
    ('Cockapoo', 'Cockapoo (Cocker Spaniel + Poodle)'),
    ('Corgipoo', 'Corgipoo (Corgi + Poodle)'),
    ('Double Doodle', 'Double Doodle (Goldendoodle + Labradoodle)'),
    ('Doxiepoo', 'Doxiepoo (Dachshund + Poodle)'),
    ('Frenchie Pug', 'Frenchie Pug (French Bulldog + Pug)'),
    ('Gerberian Shepsky', 'Gerberian Shepsky (German Shepherd + Husky)'),
    ('Goberian', 'Goberian (Golden Retriever + Siberian Husky)'),
    ('Goldendoodle', 'Goldendoodle (Golden Retriever + Poodle)'),
    ('Havapoo', 'Havapoo (Havanese + Poodle)'),
    ('Huskydoodle', 'Huskydoodle (Husky + Poodle)'),
    ('Indie Mix', 'Indie Mix / Native Crossbreed'),
    ('Labrabull', 'Labrabull (Labrador + Pit Bull)'),
    ('Labradoodle', 'Labradoodle (Labrador Retriever + Poodle)'),
    ('Maltipoo', 'Maltipoo (Maltese + Poodle)'),
    ('Mini Goldendoodle', 'Mini Goldendoodle (Golden Retriever + Toy Poodle)'),
    ('Mini Labradoodle', 'Mini Labradoodle (Labrador + Toy Poodle)'),
    ('Morkie', 'Morkie (Maltese + Yorkshire Terrier)'),
    ('Peekapoo', 'Peekapoo (Pekingese + Poodle)'),
    ('Pitador', 'Pitador (Pit Bull + Labrador)'),
    ('Pomapoo', 'Pomapoo (Pomeranian + Poodle)'),
    ('Pomchi', 'Pomchi (Pomeranian + Chihuahua)'),
    ('Pomsky', 'Pomsky (Pomeranian + Siberian Husky)'),
    ('Puggle', 'Puggle (Pug + Beagle)'),
    ('Pyredoodle', 'Pyredoodle (Great Pyrenees + Poodle)'),
    ('Rotticorso', 'Rotticorso (Rottweiler + Cane Corso)'),
    ('Rottsky', 'Rottsky (Rottweiler + Siberian Husky)'),
    ('Schnoodle', 'Schnoodle (Schnauzer + Poodle)'),
    ('Sheepadoodle', 'Sheepadoodle (Old English Sheepdog + Poodle)'),
    ('Shepsky', 'Shepsky (German Shepherd + Husky)'),
    ('Shichon', 'Shichon / Teddy Bear (Shih Tzu + Bichon Frise)'),
    ('Shih-Poo', 'Shih-Poo (Shih Tzu + Poodle)'),
    ('Shollie', 'Shollie (German Shepherd + Collie)'),
    ('Texas Heeler', 'Texas Heeler (Australian Cattle Dog + Australian Shepherd)'),
    ('Whoodle', 'Whoodle (Soft-Coated Wheaten Terrier + Poodle)'),
    ('Yorkipoo', 'Yorkipoo (Yorkshire Terrier + Poodle)'),
    ('Other Crossbreed', 'Other / Custom Crossbreed')
]

# --- Dog Profile & Photo Forms ---
class DogProfileForm(forms.ModelForm):
    YES_NO_CHOICES = [(True, 'Yes'), (False, 'No')]

    is_available = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        coerce=lambda x: str(x).lower() in ('true', '1', 'yes'),
        required=True,
        initial=True,
        label="Is your dog currently available for mating? *"
    )

    is_vaccinated = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        coerce=lambda x: str(x).lower() in ('true', '1', 'yes'),
        required=True,
        label="Fully Vaccinated *"
    )

    kci_registered = forms.TypedChoiceField(
        choices=YES_NO_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'btn-check'}),
        coerce=lambda x: str(x).lower() in ('true', '1', 'yes'),
        required=True,
        label="KCI Registered *"
    )

    name = forms.CharField(
        required=True,
        error_messages={'required': 'Dog name is required.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Rocky', 'required': 'required'})
    )
    breed_type = forms.ChoiceField(
        choices=DogProfile.BREED_TYPE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'breed-type-select', 'required': 'required'})
    )
    breed = forms.CharField(
        required=True,
        error_messages={'required': 'Please select a breed.'},
        widget=forms.TextInput(attrs={'class': 'form-control d-none', 'id': 'breed-hidden-input', 'required': 'required'})
    )
    secondary_breed = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control d-none', 'id': 'secondary-breed-hidden-input'})
    )
    age_years = forms.IntegerField(
        min_value=0,
        max_value=25,
        required=True,
        error_messages={'required': 'Age in years is required.', 'max_value': 'Please enter a realistic age (maximum 25 years).'},
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 25, 'required': 'required'})
    )
    age_months = forms.IntegerField(
        min_value=0,
        max_value=11,
        required=True,
        initial=0,
        error_messages={'required': 'Age in months is required.', 'max_value': 'Months must be between 0 and 11.'},
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 11, 'required': 'required'})
    )
    gender = forms.ChoiceField(
        choices=DogProfile.GENDER_CHOICES,
        required=True,
        error_messages={'required': 'Gender is required.'},
        widget=forms.Select(attrs={'class': 'form-select', 'required': 'required'})
    )
    state = forms.CharField(
        required=True,
        error_messages={'required': 'Please select a state.'},
        widget=forms.Select(attrs={'class': 'form-select search-select', 'id': 'state-select', 'required': 'required'})
    )
    city = forms.CharField(
        required=True,
        error_messages={'required': 'Please select a city.'},
        widget=forms.Select(attrs={'class': 'form-select search-select', 'id': 'city-select', 'required': 'required'})
    )
    weight = forms.DecimalField(
        required=True,
        min_value=0.1,
        error_messages={'required': 'Dog weight is required.'},
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 28.5', 'step': '0.1', 'required': 'required'})
    )
    weight_unit = forms.ChoiceField(
        choices=DogProfile.WEIGHT_UNIT_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    kci_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter official KCI registration number'})
    )
    kci_document = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,image/*'})
    )
    previous_litters = forms.IntegerField(
        min_value=0,
        required=True,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'required': 'required'})
    )
    mating_terms = forms.ChoiceField(
        choices=DogProfile.MATING_TERMS,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'mating-terms-select', 'required': 'required'})
    )
    stud_fee_amount = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 15000'})
    )
    shelter_provider = forms.ChoiceField(
        choices=DogProfile.SHELTER_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'required': 'required'})
    )
    travel_range = forms.ChoiceField(
        choices=DogProfile.TRAVEL_RANGE_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select', 'required': 'required'})
    )
    dog_friendly_rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        required=True,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'required': 'required'})
    )
    human_friendly_rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        required=True,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'required': 'required'})
    )
    energy_level_rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        required=True,
        initial=3,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5, 'required': 'required'})
    )

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
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any vaccinations, allergies, or past medical conditions...'}),
            'lineage_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Sire, Dam, champion lineage, or generation details...'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your dog\'s personality, temperament, habits, and mating preferences...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate state and city widget choices so valid HTML options exist
        state_val = None
        city_val = None
        if self.data:
            state_val = self.data.get('state')
            city_val = self.data.get('city')
        elif self.instance and self.instance.pk:
            state_val = self.instance.state
            city_val = self.instance.city

        if state_val:
            self.fields['state'].widget.choices = [(state_val, state_val)]
        if city_val:
            self.fields['city'].widget.choices = [(city_val, city_val)]

        if self.instance and self.instance.pk:
            self.fields['is_available'].initial = self.instance.is_available
            self.fields['is_vaccinated'].initial = self.instance.is_vaccinated
            self.fields['kci_registered'].initial = self.instance.kci_registered

    def clean(self):
        cleaned_data = super().clean()
        breed_type = cleaned_data.get('breed_type')
        secondary_breed = cleaned_data.get('secondary_breed')
        kci_registered = cleaned_data.get('kci_registered')
        kci_number = cleaned_data.get('kci_number')
        mating_terms = cleaned_data.get('mating_terms')
        stud_fee_amount = cleaned_data.get('stud_fee_amount')

        # Conditional crossbreed check
        if breed_type == 'crossbreed' and not secondary_breed:
            self.add_error('secondary_breed', 'Please specify the secondary parent breed or crossbreed mix.')

        # Conditional KCI check
        if kci_registered:
            existing_kci = getattr(self.instance, 'kci_number', None) if self.instance else None
            if not kci_number and not existing_kci:
                self.add_error('kci_number', 'Official KCI registration number is required for KCI registered dogs.')

        # Conditional Stud Fee check
        if mating_terms == 'stud_fee':
            if not stud_fee_amount or stud_fee_amount <= 0:
                self.add_error('stud_fee_amount', 'Please specify a valid stud fee amount in ₹.')

        return cleaned_data

# Helper form for uploading multiple dog photos
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={'class': 'form-control', 'multiple': True}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        files = [data] if not isinstance(data, (list, tuple)) else data
        
        cleaned_files = []
        for d in files:
            cleaned_file = single_file_clean(d, initial)
            if cleaned_file:
                # 1. Enforce file size <= 5MB
                max_size = 5 * 1024 * 1024  # 5 Megabytes
                if cleaned_file.size > max_size:
                    raise forms.ValidationError(
                        f"File '{cleaned_file.name}' exceeds the 5MB size limit ({(cleaned_file.size / (1024*1024)):.1f}MB). Please upload a smaller image."
                    )
                
                # 2. Enforce file extensions (.jpg, .jpeg, .png)
                import os
                ext = os.path.splitext(cleaned_file.name)[1].lower()
                valid_extensions = ['.jpg', '.jpeg', '.png']
                if ext not in valid_extensions:
                    raise forms.ValidationError(
                        f"Unsupported format '{ext}' for file '{cleaned_file.name}'. Only .jpg, .jpeg, and .png images are accepted."
                    )
                
                cleaned_files.append(cleaned_file)

        if isinstance(data, (list, tuple)):
            return cleaned_files
        return cleaned_files[0] if cleaned_files else None

class DogImageForm(forms.Form):
    images = MultipleFileField(required=False, help_text="Upload 1 or more photos of your dog")