import json
import math
import secrets
import urllib.parse
import urllib.request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone

from .forms import CustomUserCreationForm, DogProfileForm, DogImageForm, PUREBRED_CHOICES, CROSSBREED_CHOICES
from .models import DogProfile, DogImage, MatchRequest, ChatMessage, VeterinaryClinic, EmailOTP
from .utils import get_city_coordinates, haversine_distance
from .email_utils import send_otp_email



def home(request):
    # Fetch the active user model for this project
    User = get_user_model()
    
    # 1. Real count of registered dogs
    total_dogs = DogProfile.objects.filter(approval_status='approved').count()
    if total_dogs == 0:
        total_dogs = DogProfile.objects.count()
    
    # 2. Real count of registered users (owners)
    total_owners = User.objects.count()
    
    # 3. Real count of successful matches
    successful_matches = MatchRequest.objects.filter(status='accepted').count()
    
    # 4. Total partner clinics
    total_clinics = VeterinaryClinic.objects.count()
    
    # 5. Featured spotlight dogs
    featured_dogs = DogProfile.objects.filter(approval_status='approved', is_available=True).prefetch_related('images')[:6]
    if not featured_dogs.exists():
        featured_dogs = DogProfile.objects.prefetch_related('images')[:6]

    context = {
        'total_dogs': total_dogs,
        'total_owners': total_owners,
        'successful_matches': successful_matches,
        'total_clinics': total_clinics,
        'featured_dogs': featured_dogs,
    }
    
    return render(request, 'core/home.html', context)
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Store validated registration data in session
            request.session['pending_registration'] = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'role': form.cleaned_data['role'],
                'phone_number': form.cleaned_data['phone_number'],
                'password': form.cleaned_data['password1'],
            }
            email = form.cleaned_data['email']
            request.session['otp_email'] = email

            # Send verification OTP
            send_otp_email(email, purpose='signup')
            messages.info(request, f"A 6-digit verification code has been dispatched to {email}. Please verify below to activate your account.")
            return redirect('verify_registration_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})


def verify_registration_otp_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    reg_data = request.session.get('pending_registration')
    email = request.session.get('otp_email')

    if not reg_data or not email:
        messages.warning(request, "Please fill out the registration form to start verification.")
        return redirect('register')

    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        otp_obj = EmailOTP.objects.filter(email=email, purpose='signup', is_used=False).first()

        if not otp_obj:
            messages.error(request, "No active verification code found. Please click Resend.")
            return render(request, 'core/verify_otp.html', {'email': email})

        is_valid, msg = otp_obj.is_valid(otp_code)
        if is_valid:
            User = get_user_model()
            if User.objects.filter(username=reg_data['username']).exists() or User.objects.filter(email=reg_data['email']).exists():
                messages.error(request, "An account with these details was already created. Please log in.")
                return redirect('login')

            user = User.objects.create_user(
                username=reg_data['username'],
                email=reg_data['email'],
                password=reg_data['password'],
                role=reg_data['role'],
                phone_number=reg_data['phone_number'],
                is_verified=True,
            )
            login(request, user)

            if 'pending_registration' in request.session:
                del request.session['pending_registration']
            if 'otp_email' in request.session:
                del request.session['otp_email']

            messages.success(request, f"🎉 Email successfully verified! Welcome to K9Match, {user.username}.")
            return redirect('home')
        else:
            messages.error(request, msg)

    return render(request, 'core/verify_otp.html', {'email': email})


def forgot_password_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()

        if user:
            send_otp_email(user.email, purpose='forgot_password')
            request.session['reset_password_email'] = user.email
            messages.success(request, f"A 6-digit password reset code was sent to {user.email}.")
            return redirect('reset_password_otp')
        else:
            messages.error(request, "No registered account found with that email address. Please check your spelling.")

    return render(request, 'core/forgot_password.html')


def reset_password_otp_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    email = request.session.get('reset_password_email')
    if not email:
        messages.info(request, "Please enter your email to request a password reset code.")
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_code = request.POST.get('otp_code', '').strip()
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')

        if new_password1 != new_password2:
            messages.error(request, "The new passwords entered do not match.")
            return render(request, 'core/reset_password_otp.html', {'email': email})

        if len(new_password1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'core/reset_password_otp.html', {'email': email})

        otp_obj = EmailOTP.objects.filter(email=email, purpose='forgot_password', is_used=False).first()
        if not otp_obj:
            messages.error(request, "No active reset code found. Please request a new code.")
            return render(request, 'core/reset_password_otp.html', {'email': email})

        is_valid, msg = otp_obj.is_valid(otp_code)
        if is_valid:
            User = get_user_model()
            user = User.objects.filter(email__iexact=email).first()
            if user:
                user.set_password(new_password1)
                user.save()
                if 'reset_password_email' in request.session:
                    del request.session['reset_password_email']
                messages.success(request, "🎉 Your password has been successfully updated! Please log in with your new password.")
                return redirect('login')
            else:
                messages.error(request, "User account could not be found.")
        else:
            messages.error(request, msg)

    return render(request, 'core/reset_password_otp.html', {'email': email})


def resend_otp_view(request):
    if request.method == 'POST':
        purpose = request.POST.get('purpose', 'signup')
        if purpose == 'signup':
            email = request.session.get('otp_email')
            redirect_view = 'verify_registration_otp'
        else:
            email = request.session.get('reset_password_email')
            redirect_view = 'reset_password_otp'

        if email:
            send_otp_email(email, purpose=purpose)
            messages.success(request, f"A fresh 6-digit verification code has been dispatched to {email}.")
            return redirect(redirect_view)
        else:
            messages.error(request, "Session expired. Please start over.")
            return redirect('register' if purpose == 'signup' else 'forgot_password')
    return redirect('home')


def google_login_view(request):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.warning(
            request,
            "Google 1-Click Sign-In requires GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file. "
            "In the meantime, you can register or log in using email & OTP!"
        )
        return redirect('login')

    redirect_uri = request.build_absolute_uri(reverse('google_callback'))
    state = secrets.token_urlsafe(16)
    request.session['google_oauth_state'] = state
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return redirect(url)


def google_callback_view(request):
    code = request.GET.get('code')
    if not code:
        messages.error(request, "Google sign-in was cancelled or failed.")
        return redirect('login')

    redirect_uri = request.build_absolute_uri(reverse('google_callback'))

    try:
        token_url = "https://oauth2.googleapis.com/token"
        token_data = urllib.parse.urlencode({
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code',
        }).encode('utf-8')

        req = urllib.request.Request(token_url, data=token_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(req) as resp:
            token_res = json.loads(resp.read().decode('utf-8'))

        access_token = token_res.get('access_token')
        if not access_token:
            messages.error(request, "Failed to retrieve access token from Google.")
            return redirect('login')

        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_req = urllib.request.Request(userinfo_url, headers={'Authorization': f'Bearer {access_token}'})
        with urllib.request.urlopen(user_req) as resp:
            profile_data = json.loads(resp.read().decode('utf-8'))

        email = profile_data.get('email')
        if not email:
            messages.error(request, "Google account did not provide an email address.")
            return redirect('login')

        User = get_user_model()
        user = User.objects.filter(email__iexact=email).first()

        if not user:
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            first_name = profile_data.get('given_name', '')
            last_name = profile_data.get('family_name', '')

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_verified=True,
                role='owner',
            )

        login(request, user)
        messages.success(request, f"Welcome to K9Match, {user.username}! Successfully logged in with Google.")
        return redirect('home')

    except Exception as e:
        messages.error(request, f"Google authentication failed: {str(e)}")
        return redirect('login')

def login_view(request):
  if request.method == 'POST':
    form = AuthenticationForm(request, data=request.POST)
    if form.is_valid():
      username = form.cleaned_data.get('username')
      password = form.cleaned_data.get('password')
      user = authenticate(request, username=username, password=password)
      if user is not None:
        login(request, user)
        messages.info(request, f'You are now logged in as {username}.')
        return redirect('home')
      else:
        messages.error(request, 'Invalid username or password.')
    else:
      messages.error(request, 'Invalid username or password.')
  else:
    form = AuthenticationForm()

  return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def add_dog(request):
    if request.method == 'POST':
        form = DogProfileForm(request.POST, request.FILES)
        image_form = DogImageForm(request.POST, request.FILES)

        if form.is_valid():
            dog = form.save(commit=False)
            dog.owner = request.user
            dog.approval_status = 'pending'
            
            # Clean up conditional values
            if dog.breed_type == 'purebred':
                dog.secondary_breed = ''
                
            # Handle string-to-boolean check for KCI registration
            kci_status = request.POST.get('kci_registered')
            if kci_status == 'False' or not dog.kci_registered:
                dog.kci_registered = False
                dog.kci_number = ''
                dog.kci_document = None
            else:
                dog.kci_registered = True

            # Preserve user-submitted GPS coordinates from map picker; fallback to city coordinates
            post_lat = form.cleaned_data.get('latitude')
            post_lng = form.cleaned_data.get('longitude')
            if post_lat is not None and post_lng is not None:
                dog.latitude = post_lat
                dog.longitude = post_lng
            elif not dog.latitude or not dog.longitude:
                lat, lng = get_city_coordinates(dog.city)
                if lat and lng:
                    dog.latitude = lat
                    dog.longitude = lng

            dog.save()

            # Save uploaded images from multi-file input
            images = request.FILES.getlist('images')
            for img in images:
                DogImage.objects.create(dog=dog, image=img)

            if dog.is_available:
                messages.success(request, f"🎉 {dog.name}'s profile has been submitted and is pending admin approval! Once approved, it will appear in Find Matches.")
            else:
                messages.info(request, f"🔒 {dog.name}'s profile has been registered as Private / Hidden (unavailable for mating).")
            return redirect('my_dogs')
        else:
            messages.error(request, "Please correct the mandatory errors highlighted below before submitting.")
    else:
        form = DogProfileForm()
        image_form = DogImageForm()

    return render(request, 'core/add_dog.html', {
        'form': form,
        'image_form': image_form,
        'is_edit': False,
        'dog': None,
        'selected_state': '',
        'selected_city': '',
    })

@login_required
def my_dogs(request):
    # Retrieve all dogs owned by the currently logged-in user
    dogs = DogProfile.objects.filter(owner=request.user).order_by('-id')
    return render(request, 'core/my_dogs.html', {'dogs': dogs})

@login_required
def dog_detail(request, dog_id):
    dog = get_object_or_404(DogProfile, id=dog_id)  
    user_dogs = DogProfile.objects.filter(owner=request.user)

    # 1. Check if an accepted match exists involving this dog and request.user
    accepted_match = MatchRequest.objects.filter(
        (
            (Q(sender=request.user) & (Q(target_dog=dog) | Q(sender_dog=dog))) |
            (Q(receiver=request.user) & (Q(target_dog=dog) | Q(sender_dog=dog)))
        ),
        status='accepted'
    ).first()

    inbound_proposal = None
    sent_request = None

    # Only look for pending proposals if not already matched
    if not accepted_match:
        # Check if this dog has an inbound proposal to any of current user's dogs
        proposal_id = request.GET.get('proposal_id')
        if proposal_id:
            inbound_proposal = MatchRequest.objects.filter(
                id=proposal_id,
                receiver=request.user,
                status='pending'
            ).select_related('sender', 'target_dog', 'sender_dog').first()

        if not inbound_proposal:
            inbound_proposal = MatchRequest.objects.filter(
                receiver=request.user,
                sender_dog=dog,
                status='pending'
            ).select_related('sender', 'target_dog', 'sender_dog').first()

        # Check if current user sent an outbound proposal for this dog
        sent_request = MatchRequest.objects.filter(
            sender=request.user,
            target_dog=dog,
            status='pending'
        ).order_by('-id').first()

    return render(request, 'core/dog_detail.html', {
        'dog': dog,
        'user_dogs': user_dogs,
        'sent_request': sent_request,
        'inbound_proposal': inbound_proposal,
        'accepted_match': accepted_match,
    })


@login_required
def edit_dog(request, dog_id):
    dog = get_object_or_404(DogProfile, id=dog_id, owner=request.user)

    if request.method == 'POST':
        form = DogProfileForm(request.POST, request.FILES, instance=dog)
        image_form = DogImageForm(request.POST, request.FILES)

        if form.is_valid():
            updated_dog = form.save(commit=False)
            
            # Clean up conditional values
            if updated_dog.breed_type == 'purebred':
                updated_dog.secondary_breed = ''

            # Explicitly sync boolean values from POST radio inputs
            avail_status = request.POST.get('is_available')
            if avail_status is not None:
                updated_dog.is_available = str(avail_status).lower() in ('true', '1', 'yes')

            vac_status = request.POST.get('is_vaccinated')
            if vac_status is not None:
                updated_dog.is_vaccinated = str(vac_status).lower() in ('true', '1', 'yes')

            # Handle radio string-to-boolean check for KCI
            kci_status = request.POST.get('kci_registered')
            if kci_status == 'False' or not updated_dog.kci_registered:
                updated_dog.kci_registered = False
                updated_dog.kci_number = ''
                updated_dog.kci_document = None
            else:
                updated_dog.kci_registered = True

            # Preserve user-submitted GPS coordinates from map picker; fallback to city coordinates
            post_lat = form.cleaned_data.get('latitude')
            post_lng = form.cleaned_data.get('longitude')
            if post_lat is not None and post_lng is not None:
                updated_dog.latitude = post_lat
                updated_dog.longitude = post_lng
            elif not updated_dog.latitude or not updated_dog.longitude:
                lat, lng = get_city_coordinates(updated_dog.city)
                if lat and lng:
                    updated_dog.latitude = lat
                    updated_dog.longitude = lng

            updated_dog.save()

            # Handle new photo uploads if added during edit
            images = request.FILES.getlist('images')
            for img in images:
                DogImage.objects.create(dog=updated_dog, image=img)

            messages.success(request, f"{updated_dog.name}'s profile updated successfully!")
            return redirect('dog_detail', dog_id=updated_dog.id)
        else:
            error_list = [f"{field.replace('_', ' ').title()}: {', '.join(errs)}" for field, errs in form.errors.items()]
            messages.error(request, f"Please correct the errors: {'; '.join(error_list)}")
    else:
        form = DogProfileForm(instance=dog)
        image_form = DogImageForm()

    return render(request, 'core/add_dog.html', {
        'form': form,
        'image_form': image_form,
        'is_edit': True,
        'dog': dog,
        'selected_state': dog.state,
        'selected_city': dog.city,
    })


@login_required
def delete_dog(request, dog_id):
    dog = get_object_or_404(DogProfile, id=dog_id, owner=request.user)

    if request.method == 'POST':
        dog_name = dog.name
        dog.delete()
        messages.success(request, f"{dog_name}'s profile has been deleted.")
        return redirect('my_dogs')

    return render(request, 'core/delete_dog_confirm.html', {'dog': dog})

@login_required
def profile_view(request):
    if request.method == 'POST':
        request.user.email = request.POST.get('email')
        request.user.first_name = request.POST.get('first_name')
        request.user.last_name = request.POST.get('last_name')
        request.user.save()
        messages.success(request, "Your profile details have been updated successfully!")
        return redirect('profile')

    return render(request, 'core/profile.html')


def explore_dogs(request):
    # Base discovery pool: strictly approved and available dogs
    dogs = DogProfile.objects.filter(approval_status='approved', is_available=True).order_by('-id')

    # Epic 2 Task 2.2: Exclude user's own dogs from search results
    user_dogs = []
    if request.user.is_authenticated:
        dogs = dogs.exclude(owner=request.user)
        user_dogs = list(DogProfile.objects.filter(owner=request.user))

    # Extract structured filter parameters (Task 3.1 & 3.3)
    breed_type_filter = request.GET.get('breed_type', '').strip()
    breed_filter = request.GET.get('breed', '').strip()
    gender_filter = request.GET.get('gender', '').strip()
    state_filter = request.GET.get('state', '').strip()
    city_filter = request.GET.get('city', '').strip()
    radius_filter = request.GET.get('radius', '').strip()
    my_dog_id = request.GET.get('my_dog', '').strip()
    kci_only = request.GET.get('kci_only', '').strip()

    # Apply Structured Filters
    if breed_type_filter:
        dogs = dogs.filter(breed_type__iexact=breed_type_filter)

    if breed_filter:
        dogs = dogs.filter(breed__iexact=breed_filter)

    if gender_filter:
        dogs = dogs.filter(gender__iexact=gender_filter)

    if state_filter:
        dogs = dogs.filter(state__iexact=state_filter)

    if city_filter:
        dogs = dogs.filter(city__iexact=city_filter)

    if kci_only == 'true':
        dogs = dogs.filter(kci_registered=True)

    # Reference Coordinates for Distance & Radius Filter (Task 3.2)
    ref_lat = None
    ref_lng = None
    ref_location_label = ""
    active_dog = None

    # 1. Live Device Coordinates from "Near Me" GPS Button
    user_lat_param = request.GET.get('user_lat', '').strip()
    user_lng_param = request.GET.get('user_lng', '').strip()
    user_lat = None
    user_lng = None
    if user_lat_param and user_lng_param:
        try:
            user_lat = float(user_lat_param)
            user_lng = float(user_lng_param)
            ref_lat = user_lat
            ref_lng = user_lng
            ref_location_label = "Your Current Location"
        except (ValueError, TypeError):
            pass

    # 2. Selected Active Dog Coordinates
    if not ref_lat and my_dog_id and request.user.is_authenticated:
        active_dog = next((d for d in user_dogs if str(d.id) == str(my_dog_id)), None)
        if active_dog and active_dog.latitude and active_dog.longitude:
            ref_lat = active_dog.latitude
            ref_lng = active_dog.longitude
            ref_location_label = f"{active_dog.name} ({active_dog.location_address or active_dog.city})"

    # 3. User's First Dog Coordinates
    if not ref_lat and request.user.is_authenticated and user_dogs:
        first_dog = user_dogs[0]
        if first_dog.latitude and first_dog.longitude:
            ref_lat = first_dog.latitude
            ref_lng = first_dog.longitude
            ref_location_label = f"{first_dog.name} ({first_dog.location_address or first_dog.city})"
            active_dog = first_dog

    # 4. City Filter Fallback
    if not ref_lat and city_filter:
        c_lat, c_lng = get_city_coordinates(city_filter)
        if c_lat and c_lng:
            ref_lat, ref_lng = c_lat, c_lng
            ref_location_label = city_filter

    # SQL Bounding Box Filter Optimization (Trims 99% in database index before Haversine)
    if ref_lat is not None and ref_lng is not None and radius_filter:
        try:
            radius_val = float(radius_filter)
            lat_delta = radius_val / 111.0
            cos_lat = math.cos(math.radians(float(ref_lat)))
            lng_delta = radius_val / (111.0 * max(abs(cos_lat), 0.01))

            min_lat = float(ref_lat) - lat_delta
            max_lat = float(ref_lat) + lat_delta
            min_lng = float(ref_lng) - lng_delta
            max_lng = float(ref_lng) + lng_delta

            dogs = dogs.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                latitude__gte=min_lat,
                latitude__lte=max_lat,
                longitude__gte=min_lng,
                longitude__lte=max_lng
            )
        except (ValueError, TypeError):
            pass

    # Convert to list to calculate exact distance for each dog
    dogs_list = list(dogs)
    for dog in dogs_list:
        if ref_lat is not None and ref_lng is not None and dog.latitude is not None and dog.longitude is not None:
            dist = haversine_distance(ref_lat, ref_lng, dog.latitude, dog.longitude)
            dog.distance_km = round(dist, 1) if dist is not None else None
        else:
            dog.distance_km = None

    # Precise Haversine Radius Filter
    if radius_filter:
        try:
            radius_val = float(radius_filter)
            dogs_list = [d for d in dogs_list if d.distance_km is not None and d.distance_km <= radius_val]
        except (ValueError, TypeError):
            pass

    # Sort: If distance is available, sort closest first! Otherwise newest first
    if ref_lat is not None and ref_lng is not None:
        dogs_list.sort(key=lambda d: (d.distance_km is None, d.distance_km if d.distance_km is not None else float('inf')))

    # Count active filters
    active_filters_count = sum(1 for val in [breed_type_filter, breed_filter, gender_filter, state_filter, city_filter, radius_filter, (kci_only == 'true'), user_lat] if val)

    sent_request_dog_ids = set()
    accepted_match_dog_ids = set()
    inbound_proposal_dog_ids = set()

    if request.user.is_authenticated:
        # Dogs with pending requests sent by user
        sent_request_dog_ids = set(
            MatchRequest.objects.filter(
                sender=request.user,
                status='pending'
            ).values_list('target_dog_id', flat=True)
        )

        # Dogs with accepted matches involving user (either as sender_dog or target_dog)
        accepted_matches = MatchRequest.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user),
            status='accepted'
        ).values_list('sender_dog_id', 'target_dog_id')
        for s_id, t_id in accepted_matches:
            if s_id:
                accepted_match_dog_ids.add(s_id)
            if t_id:
                accepted_match_dog_ids.add(t_id)

        # Dogs with inbound pending proposals sent to user
        inbound_proposals = MatchRequest.objects.filter(
            receiver=request.user,
            status='pending'
        ).values_list('sender_dog_id', flat=True)
        inbound_proposal_dog_ids = set(p for p in inbound_proposals if p)

    context = {
        'dogs': dogs_list,
        'total_results': len(dogs_list),
        'user_dogs': user_dogs,
        'active_dog': active_dog,
        'my_dog_id': my_dog_id,
        'breed_filter': breed_filter,
        'gender_filter': gender_filter,
        'breed_type_filter': breed_type_filter,
        'state_filter': state_filter,
        'city_filter': city_filter,
        'radius_filter': radius_filter,
        'kci_only': kci_only,
        'user_lat': user_lat,
        'user_lng': user_lng,
        'ref_location_label': ref_location_label,
        'active_filters_count': active_filters_count,
        'purebred_choices': PUREBRED_CHOICES,
        'crossbreed_choices': CROSSBREED_CHOICES,
        'sent_request_dog_ids': sent_request_dog_ids,
        'accepted_match_dog_ids': accepted_match_dog_ids,
        'inbound_proposal_dog_ids': inbound_proposal_dog_ids,
    }
    return render(request, 'core/explore_dogs.html', context)

@login_required
def send_match_request(request, dog_id):
    target_dog = get_object_or_404(DogProfile, id=dog_id)
    is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
               'application/json' in request.headers.get('Accept', ''))

    # Don't allow liking your own dog
    if target_dog.owner == request.user:
        msg = "You cannot send a match request to your own dog!"
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg}, status=400)
        messages.warning(request, msg)
        return redirect('dog_detail', dog_id=target_dog.id)

    sender_dog_id = request.POST.get('sender_dog') if request.method == 'POST' else None
    sender_dog = None
    if sender_dog_id:
        sender_dog = DogProfile.objects.filter(id=sender_dog_id, owner=request.user).first()

    # Check if already matched (accepted) in EITHER direction
    existing_accepted = MatchRequest.objects.filter(
        (
            (Q(sender_dog=sender_dog, target_dog=target_dog) | Q(sender_dog=target_dog, target_dog=sender_dog))
            if sender_dog else
            (
                (Q(sender=request.user) & (Q(target_dog=target_dog) | Q(sender_dog=target_dog))) |
                (Q(receiver=request.user) & (Q(target_dog=target_dog) | Q(sender_dog=target_dog)))
            )
        ),
        status='accepted'
    ).first()

    if existing_accepted:
        msg = f"You are already matched with {target_dog.name}! You can chat directly in Messages."
        if is_ajax:
            return JsonResponse({
                'success': False,
                'error': msg,
                'already_matched': True,
                'chat_url': reverse('chat_room', args=[existing_accepted.id])
            }, status=200)
        messages.info(request, msg)
        return redirect('chat_room', match_id=existing_accepted.id)

    # Check if a pending request already exists in EITHER direction
    existing_pending = MatchRequest.objects.filter(
        (
            (Q(sender_dog=sender_dog, target_dog=target_dog) | Q(sender_dog=target_dog, target_dog=sender_dog))
            if sender_dog else
            (
                (Q(sender=request.user) & (Q(target_dog=target_dog) | Q(sender_dog=target_dog))) |
                (Q(receiver=request.user) & (Q(target_dog=target_dog) | Q(sender_dog=target_dog)))
            )
        ),
        status='pending'
    ).first()

    if existing_pending:
        if existing_pending.sender == request.user:
            msg = f"You have already sent a match request for {target_dog.name}. Please wait for the owner to accept or reject it."
        else:
            msg = f"{target_dog.owner.username} has already sent you a proposal for this match! Check your Proposals dashboard."
        if is_ajax:
            return JsonResponse({'success': False, 'error': msg, 'already_sent': True}, status=200)
        messages.info(request, msg)
        return redirect('dog_detail', dog_id=target_dog.id)

    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()

        from django.core.exceptions import ValidationError
        try:
            match_req = MatchRequest(
                sender=request.user,
                receiver=target_dog.owner,
                target_dog=target_dog,
                sender_dog=sender_dog,
                message=message_text,
                status='pending'
            )
            match_req.full_clean()
            match_req.save()
            success_msg = f"❤️ Match request sent to {target_dog.name}'s owner ({target_dog.owner.username})!"
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': success_msg,
                    'dog_id': target_dog.id,
                    'dog_name': target_dog.name,
                    'request_id': match_req.id
                })
            messages.success(request, success_msg)
        except ValidationError as e:
            err_msg = e.messages[0] if hasattr(e, 'messages') else str(e)
            if is_ajax:
                return JsonResponse({'success': False, 'error': err_msg}, status=400)
            messages.error(request, err_msg)

        next_url = request.POST.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('dog_detail', dog_id=target_dog.id)

    return redirect('dog_detail', dog_id=target_dog.id)


@login_required
def match_requests_dashboard(request):
    received_requests = MatchRequest.objects.filter(receiver=request.user).order_by('-created_at')
    sent_requests = MatchRequest.objects.filter(sender=request.user).order_by('-created_at')
    
    # Count ONLY pending requests that need action
    pending_received_count = MatchRequest.objects.filter(receiver=request.user, status='pending').count()

    return render(request, 'core/match_requests.html', {
        'received_requests': received_requests,
        'sent_requests': sent_requests,
        'pending_received_count': pending_received_count,
    })


@login_required
def respond_match_request(request, request_id, action):
    match_req = get_object_or_404(MatchRequest, id=request_id, receiver=request.user)
    is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
               'application/json' in request.headers.get('Accept', ''))

    if action == 'accept':
        match_req.status = 'accepted'
        match_req.save()
        success_msg = f"You accepted the match proposal from {match_req.sender.username} for {match_req.sender_dog.name if match_req.sender_dog else 'their canine'}!"
        if is_ajax:
            return JsonResponse({
                'success': True, 
                'action': 'accepted', 
                'message': success_msg, 
                'chat_url': reverse('chat_room', args=[match_req.id])
            })
        messages.success(request, success_msg)
    elif action in ['decline', 'reject']:
        match_req.status = 'declined'
        match_req.save()
        info_msg = "Match proposal declined."
        if is_ajax:
            return JsonResponse({'success': True, 'action': 'declined', 'message': info_msg})
        messages.info(request, info_msg)

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('match_requests_dashboard')

@login_required
def chats_inbox(request):
    matches = MatchRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='accepted'
    ).select_related('sender', 'receiver', 'target_dog', 'sender_dog').prefetch_related('messages').order_by('-updated_at')

    seen_pairs = set()
    conversations = []
    for m in matches:
        dog_a_id = m.sender_dog_id or 0
        dog_b_id = m.target_dog_id or 0
        canonical_pair = tuple(sorted([dog_a_id, dog_b_id]))

        # Guarantee: Between any two dogs, only ONE single chat conversation is opened/shown
        if dog_a_id and dog_b_id:
            if canonical_pair in seen_pairs:
                continue
            seen_pairs.add(canonical_pair)

        other_user = m.receiver if request.user == m.sender else m.sender
        my_dog = m.sender_dog if request.user == m.sender else m.target_dog
        partner_dog = m.target_dog if request.user == m.sender else m.sender_dog

        last_msg = m.messages.last()
        last_text = "No messages yet. Say hello to discuss breeding terms!"
        last_time = m.updated_at
        is_deleted = False

        if last_msg:
            is_deleted = last_msg.is_deleted
            last_text = "This message was deleted." if is_deleted else last_msg.message
            last_time = last_msg.timestamp

        conversations.append({
            'match': m,
            'other_user': other_user,
            'my_dog': my_dog,
            'partner_dog': partner_dog,
            'last_message': last_text,
            'is_deleted': is_deleted,
            'last_time': last_time,
            'has_messages': bool(last_msg),
        })

    conversations.sort(key=lambda c: c['last_time'], reverse=True)

    return render(request, 'core/chats_inbox.html', {
        'conversations': conversations,
        'total_conversations': len(conversations),
    })

@login_required
def chat_room(request, match_id):
    # Ensure only the sender or receiver of the accepted match can access this room
    match_req = get_object_or_404(MatchRequest, id=match_id, status='accepted')
    
    if request.user != match_req.sender and request.user != match_req.receiver:
        messages.error(request, "You do not have access to this conversation.")
        return redirect('match_requests_dashboard')

    other_user = match_req.receiver if request.user == match_req.sender else match_req.sender
    chat_messages = match_req.messages.all()

    return render(request, 'core/chat_room.html', {
        'match_req': match_req,
        'other_user': other_user,
        'chat_messages': chat_messages,
    })


@login_required
def send_message_api(request, match_id):
    if request.method == 'POST':
        match_req = get_object_or_404(MatchRequest, id=match_id, status='accepted')
        
        if request.user != match_req.sender and request.user != match_req.receiver:
            return JsonResponse({'error': 'Unauthorized'}, status=403)

        raw_text = request.POST.get('message', '')
        # 1. Sanitize text: prevent empty whitespace messages
        stripped_text = raw_text.strip()
        if not stripped_text:
            return JsonResponse({'error': 'Cannot send empty or whitespace-only messages.'}, status=400)

        # 2. XSS prevention: strip unsafe HTML tags
        from django.utils.html import escape, strip_tags
        sanitized_text = strip_tags(stripped_text)
        if not sanitized_text.strip():
            return JsonResponse({'error': 'Invalid message content.'}, status=400)

        msg = ChatMessage.objects.create(
            match=match_req,
            sender=request.user,
            message=sanitized_text
        )
        # Convert timestamp to local time zone
        local_time = timezone.localtime(msg.timestamp).strftime('%I:%M %p')
        return JsonResponse({
            'status': 'ok',
            'id': msg.id,
            'sender': msg.sender.username,
            'message': msg.message,
            'timestamp': local_time,
            'is_edited': False,
            'is_deleted': False
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def get_messages_api(request, match_id):
    match_req = get_object_or_404(MatchRequest, id=match_id, status='accepted')
    
    if request.user != match_req.sender and request.user != match_req.receiver:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    messages_data = [
        {
            'id': m.id,
            'sender': m.sender.username,
            'is_me': m.sender == request.user,
            'message': 'This message was deleted.' if m.is_deleted else m.message,
            'timestamp': timezone.localtime(m.timestamp).strftime('%I:%M %p'),
            'is_edited': m.is_edited,
            'is_deleted': m.is_deleted
        }
        for m in match_req.messages.all()
    ]
    return JsonResponse({'messages': messages_data})


@login_required
def edit_message_api(request, message_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    msg = get_object_or_404(ChatMessage, id=message_id)
    if msg.sender != request.user:
        return JsonResponse({'error': 'You can only edit your own messages.'}, status=403)

    if msg.is_deleted:
        return JsonResponse({'error': 'Deleted messages cannot be edited.'}, status=400)

    raw_text = request.POST.get('message', '').strip()
    from django.utils.html import strip_tags
    sanitized_text = strip_tags(raw_text).strip()
    if not sanitized_text:
        return JsonResponse({'error': 'Message content cannot be empty.'}, status=400)

    msg.message = sanitized_text
    msg.is_edited = True
    msg.save()

    return JsonResponse({
        'status': 'ok',
        'id': msg.id,
        'message': msg.message,
        'is_edited': True
    })


@login_required
def delete_message_api(request, message_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    msg = get_object_or_404(ChatMessage, id=message_id)
    if msg.sender != request.user:
        return JsonResponse({'error': 'You can only delete your own messages.'}, status=403)

    msg.is_deleted = True
    msg.message = "This message was deleted."
    msg.save()

    return JsonResponse({
        'status': 'ok',
        'id': msg.id,
        'is_deleted': True,
        'message': msg.message
    })


@staff_member_required
def admin_dashboard(request):
    status_filter = request.GET.get('status', 'pending').strip().lower()
    
    total_dogs = DogProfile.objects.count()
    pending_count = DogProfile.objects.filter(approval_status='pending').count()
    approved_count = DogProfile.objects.filter(approval_status='approved').count()
    rejected_count = DogProfile.objects.filter(approval_status='rejected').count()

    dogs = DogProfile.objects.select_related('owner').prefetch_related('images').order_by('-created_at')

    if status_filter in ['pending', 'approved', 'rejected']:
        dogs = dogs.filter(approval_status=status_filter)

    search_q = request.GET.get('q', '').strip()
    if search_q:
        dogs = dogs.filter(
            Q(name__icontains=search_q) |
            Q(breed__icontains=search_q) |
            Q(city__icontains=search_q) |
            Q(owner__username__icontains=search_q) |
            Q(kci_number__icontains=search_q)
        )

    context = {
        'dogs': dogs,
        'status_filter': status_filter,
        'search_q': search_q,
        'total_dogs': total_dogs,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'core/admin_dashboard.html', context)


@staff_member_required
def admin_approve_reject_dog(request, dog_id, action):
    dog = get_object_or_404(DogProfile, id=dog_id)

    if action == 'approve':
        dog.approval_status = 'approved'
        dog.admin_rejection_reason = ''
        dog.save()
        messages.success(request, f"✅ Dog profile '{dog.name}' (ID: #{dog.id}) has been approved and is now live in Find Matches!")
    elif action == 'reject':
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        dog.approval_status = 'rejected'
        dog.admin_rejection_reason = rejection_reason if rejection_reason else 'Profile did not meet verification criteria.'
        dog.save()
        messages.warning(request, f"❌ Dog profile '{dog.name}' (ID: #{dog.id}) was rejected.")
    else:
        messages.error(request, "Invalid admin action.")

    return redirect('admin_dashboard')


def vets_directory(request):
    clinics = VeterinaryClinic.objects.all().order_by('-rating', '-created_at')

    # Filter parameters
    state_filter = request.GET.get('state', '').strip()
    city_filter = request.GET.get('city', '').strip()
    emergency_filter = request.GET.get('emergency', '').strip()
    radius_filter = request.GET.get('radius', '').strip()
    search_q = request.GET.get('q', '').strip()

    if state_filter:
        clinics = clinics.filter(state__iexact=state_filter)

    if city_filter:
        clinics = clinics.filter(city__iexact=city_filter)

    if emergency_filter == 'true':
        clinics = clinics.filter(is_24x7_emergency=True)

    if search_q:
        clinics = clinics.filter(
            Q(name__icontains=search_q) |
            Q(doctor_name__icontains=search_q) |
            Q(specialization__icontains=search_q) |
            Q(address__icontains=search_q) |
            Q(city__icontains=search_q) |
            Q(services_offered__icontains=search_q)
        )

    # Reference coordinates for distance
    ref_lat = None
    ref_lng = None
    ref_location_label = ""

    if city_filter:
        c_lat, c_lng = get_city_coordinates(city_filter)
        if c_lat and c_lng:
            ref_lat, ref_lng = c_lat, c_lng
            ref_location_label = city_filter
    elif request.user.is_authenticated:
        user_dog = request.user.dogs.first()
        if user_dog and user_dog.latitude and user_dog.longitude:
            ref_lat, ref_lng = user_dog.latitude, user_dog.longitude
            ref_location_label = f"your registered location ({user_dog.city})"

    clinics_list = list(clinics)
    for clinic in clinics_list:
        if not clinic.latitude or not clinic.longitude:
            c_lat, c_lng = get_city_coordinates(clinic.city)
            if c_lat and c_lng:
                clinic.latitude, clinic.longitude = c_lat, c_lng

        if ref_lat is not None and ref_lng is not None and clinic.latitude is not None and clinic.longitude is not None:
            dist = haversine_distance(ref_lat, ref_lng, clinic.latitude, clinic.longitude)
            clinic.distance_km = round(dist, 1) if dist is not None else None
        else:
            clinic.distance_km = None

    if radius_filter:
        try:
            r_val = float(radius_filter)
            clinics_list = [c for c in clinics_list if c.distance_km is not None and c.distance_km <= r_val]
        except (ValueError, TypeError):
            pass

    if ref_lat is not None and ref_lng is not None:
        clinics_list.sort(key=lambda c: (c.distance_km is None, c.distance_km if c.distance_km is not None else float('inf')))

    available_states = VeterinaryClinic.objects.exclude(state__isnull=True).exclude(state='').values_list('state', flat=True).distinct().order_by('state')
    available_cities = VeterinaryClinic.objects.values_list('city', flat=True).distinct().order_by('city')
    total_emergency = VeterinaryClinic.objects.filter(is_24x7_emergency=True).count()

    context = {
        'clinics': clinics_list,
        'total_clinics': len(clinics_list),
        'state_filter': state_filter,
        'city_filter': city_filter,
        'emergency_filter': emergency_filter,
        'radius_filter': radius_filter,
        'search_q': search_q,
        'ref_location_label': ref_location_label,
        'available_states': available_states,
        'available_cities': available_cities,
        'total_emergency': total_emergency,
    }
    return render(request, 'core/vets_directory.html', context)


# Custom HTTP Error Page Views
def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)

def custom_500_view(request):
    return render(request, '500.html', status=500)


def reverse_geocode_api(request):
    """
    Server-side proxy for reverse geocoding to bypass browser CORS and User-Agent restrictions.
    Returns detected state, city, and locality.
    """
    lat = request.GET.get('lat')
    lng = request.GET.get('lng') or request.GET.get('lon')
    if not lat or not lng:
        return JsonResponse({'success': False, 'error': 'Missing coordinates'}, status=400)

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lng}"
        req = urllib.request.Request(url, headers={'User-Agent': 'K9Match-App/1.0 (support@k9match.com)'})
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode('utf-8'))
            addr = data.get('address', {})
            
            state = addr.get('state') or addr.get('state_district') or addr.get('region') or ''
            
            city_candidates = [
                addr.get('city'),
                addr.get('town'),
                addr.get('municipality'),
                addr.get('suburb'),
                addr.get('county'),
                addr.get('city_district'),
                addr.get('state_district')
            ]
            city = ''
            for cand in city_candidates:
                if cand:
                    city = cand.replace('Subdistrict', '').replace('District', '').strip()
                    break
            
            locality = addr.get('suburb') or addr.get('neighbourhood') or addr.get('road') or city or data.get('name') or ''
            
            return JsonResponse({
                'success': True,
                'state': state,
                'city': city,
                'locality': locality
            })
    except Exception:
        # Fallback to BigDataCloud
        try:
            bdc_url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lng}&localityLanguage=en"
            req2 = urllib.request.Request(bdc_url, headers={'User-Agent': 'K9Match-App/1.0'})
            with urllib.request.urlopen(req2, timeout=6) as response2:
                bg_data = json.loads(response2.read().decode('utf-8'))
                state = bg_data.get('principalSubdivision') or ''
                city = bg_data.get('city') or bg_data.get('locality') or ''
                locality = bg_data.get('locality') or bg_data.get('neighbourhood') or city
                return JsonResponse({
                    'success': True,
                    'state': state,
                    'city': city,
                    'locality': locality
                })
        except Exception as e2:
            return JsonResponse({'success': False, 'error': str(e2)}, status=500)