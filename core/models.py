from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = (
        ('breeder', 'Breeder'),
        ('owner', 'Dog Owner'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='owner')
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class DogProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
    )

    MATING_TERMS = (
        ('stud_fee', 'Stud Fee'),
        ('want_puppy', 'Want Puppy (Pick of Litter)'),
        ('negotiable', 'Negotiable'),
    )

    SHELTER_CHOICES = (
        ('my_place', 'Arranged by me (At my place)'),
        ('other_place', 'Arranged by the mating partner'),
        ('negotiable', 'Negotiable'),
    )

    WEIGHT_UNIT_CHOICES = (
        ('kg', 'kg'),
        ('lbs', 'lbs'),
    )

    TRAVEL_RANGE_CHOICES = (
        ('none', 'Not willing to travel (Local pickup/meet only)'),
        ('0-5', 'Within 0 - 5 km'),
        ('5-20', 'Within 5 - 20 km'),
        ('20-50', 'Within 20 - 50 km'),
        ('50+', '50+ km (Statewide / Long distance)'),
        ('negotiable', 'Negotiable / Flexible'),
    )

    BREED_CHOICES = (
        ('Beagle', 'Beagle'),
        ('Boxer', 'Boxer'),
        ('Bulldog', 'Bulldog'),
        ('Cocker Spaniel', 'Cocker Spaniel'),
        ('Dachshund', 'Dachshund'),
        ('Doberman Pinscher', 'Doberman Pinscher'),
        ('French Bulldog', 'French Bulldog'),
        ('German Shepherd', 'German Shepherd'),
        ('Golden Retriever', 'Golden Retriever'),
        ('Great Dane', 'Great Dane'),
        ('Labrador Retriever', 'Labrador Retriever'),
        ('Pomeranian', 'Pomeranian'),
        ('Poodle', 'Poodle'),
        ('Pug', 'Pug'),
        ('Rottweiler', 'Rottweiler'),
        ('Shih Tzu', 'Shih Tzu'),
        ('Siberian Husky', 'Siberian Husky'),
        ('Other', 'Other / Crossbreed'),
    )

    BREED_TYPE_CHOICES = (
    ('purebred', 'Purebred'),
    ('crossbreed', 'Crossbreed / Mix'),
    )

    # Ownership Link
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dogs')
    
    # Core Details (Mandatory fields)
    
    name = models.CharField(max_length=100)
    breed_type = models.CharField(max_length=20, choices=BREED_TYPE_CHOICES, default='purebred')
    breed = models.CharField(max_length=100, default='Labrador Retriever')
    secondary_breed = models.CharField(max_length=100, blank=True, null=True)  # For parent 2 if crossbreed
    age_years = models.PositiveIntegerField()
    age_months = models.PositiveIntegerField(default=0)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    
    # State & City
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100)

    # Physical Attributes
    weight_unit = models.CharField(max_length=5, choices=WEIGHT_UNIT_CHOICES, default='kg')
    weight = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)

    # Health & KCI Verification
    is_vaccinated = models.BooleanField(null=True, blank=False)  # Explicit Choice Needed
    medical_history = models.TextField(blank=True)

    kci_registered = models.BooleanField(null=True, blank=False) # Explicit Choice Needed
    kci_number = models.CharField(max_length=50, blank=True, null=True)
    kci_document = models.FileField(upload_to='kci_documents/', blank=True, null=True)
    lineage_details = models.TextField(blank=True)

    # Breeding & Terms
    previous_litters = models.PositiveIntegerField(default=0)
    mating_terms = models.CharField(max_length=20, choices=MATING_TERMS, default='negotiable')
    stud_fee_amount = models.PositiveIntegerField(blank=True, null=True, help_text="Amount in ₹")
    
    shelter_provider = models.CharField(max_length=20, choices=SHELTER_CHOICES, default='negotiable')
    travel_range = models.CharField(max_length=20, choices=TRAVEL_RANGE_CHOICES, default='0-5')

    # Behavioral Ratings
    dog_friendly_rating = models.PositiveIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    human_friendly_rating = models.PositiveIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    energy_level_rating = models.PositiveIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])

    bio = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dogs')

    def __str__(self):
        return f"{self.name} ({self.breed}) - {self.city}"


# Model for Multiple Photo Uploads
class DogImage(models.Model):
    dog = models.ForeignKey(DogProfile, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='dog_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.dog.name}"

class MatchRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    target_dog = models.ForeignKey(DogProfile, on_delete=models.CASCADE, related_name='received_matches')
    sender_dog = models.ForeignKey(DogProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_matches')
    message = models.TextField(blank=True, default='')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent duplicate pending requests for the same target dog by the same sender
        unique_together = ('sender', 'target_dog', 'status')

    def __str__(self):
        return f"{self.sender.username} -> {self.target_dog.name} ({self.status})"


class ChatMessage(models.Model):
    match = models.ForeignKey(MatchRequest, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.message[:20]}"