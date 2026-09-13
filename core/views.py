from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from .forms import CustomUserCreationForm, DogProfileForm, DogImageForm, PUREBRED_CHOICES, CROSSBREED_CHOICES
from .models import DogProfile, DogImage, MatchRequest, ChatMessage, VeterinaryClinic
from .utils import get_city_coordinates, haversine_distance



def home(request):
    # Fetch the active user model for this project
    User = get_user_model()
    
    # 1. Real count of registered dogs
    total_dogs = DogProfile.objects.count()
    
    # 2. Real count of registered users (owners)
    total_owners = User.objects.count()
    
    # 3. Real count of successful matches
    successful_matches = MatchRequest.objects.filter(status='accepted').count()

    context = {
        'total_dogs': total_dogs,
        'total_owners': total_owners,
        'successful_matches': successful_matches,
    }
    
    return render(request, 'core/home.html', context)
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in user after successful sign-up
            messages.success(request, f"Account created successfully! Welcome, {user.username}.")
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'core/register.html', {'form': form})

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

            # Populate coordinates if available
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
        'image_form': image_form
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

    return render(request, 'core/dog_detail.html', {
        'dog': dog,
        'user_dogs': user_dogs
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

            # Update coordinates if city changed
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

    if my_dog_id and request.user.is_authenticated:
        active_dog = next((d for d in user_dogs if str(d.id) == str(my_dog_id)), None)
        if active_dog and active_dog.latitude and active_dog.longitude:
            ref_lat = active_dog.latitude
            ref_lng = active_dog.longitude
            ref_location_label = f"{active_dog.name} ({active_dog.city})"

    if not ref_lat and city_filter:
        c_lat, c_lng = get_city_coordinates(city_filter)
        if c_lat and c_lng:
            ref_lat, ref_lng = c_lat, c_lng
            ref_location_label = city_filter

    if not ref_lat and request.user.is_authenticated and user_dogs:
        first_dog = user_dogs[0]
        if first_dog.latitude and first_dog.longitude:
            ref_lat = first_dog.latitude
            ref_lng = first_dog.longitude
            ref_location_label = f"{first_dog.name} ({first_dog.city})"
            active_dog = first_dog

    # Convert to list to calculate distance for each dog
    dogs_list = list(dogs)
    for dog in dogs_list:
        # Populate coordinates if missing
        if not dog.latitude or not dog.longitude:
            lat, lng = get_city_coordinates(dog.city)
            if lat and lng:
                dog.latitude = lat
                dog.longitude = lng

        if ref_lat is not None and ref_lng is not None and dog.latitude is not None and dog.longitude is not None:
            dist = haversine_distance(ref_lat, ref_lng, dog.latitude, dog.longitude)
            dog.distance_km = round(dist, 1) if dist is not None else None
        else:
            dog.distance_km = None

    # Geolocation Radius Filter
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
    active_filters_count = sum(1 for val in [breed_type_filter, breed_filter, gender_filter, state_filter, city_filter, radius_filter, (kci_only == 'true')] if val)

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
        'ref_location_label': ref_location_label,
        'active_filters_count': active_filters_count,
        'purebred_choices': PUREBRED_CHOICES,
        'crossbreed_choices': CROSSBREED_CHOICES,
    }
    return render(request, 'core/explore_dogs.html', context)

@login_required
def send_match_request(request, dog_id):
    target_dog = get_object_or_404(DogProfile, id=dog_id)

    # Don't allow liking your own dog
    if target_dog.owner == request.user:
        messages.warning(request, "You cannot send a match request to your own dog!")
        return redirect('dog_detail', dog_id=target_dog.id)

    # Check if a pending request already exists
    existing_request = MatchRequest.objects.filter(
        sender=request.user,
        target_dog=target_dog,
        status='pending'
    ).first()

    if existing_request:
        messages.info(request, f"You have already sent a match request for {target_dog.name}.")
        return redirect('dog_detail', dog_id=target_dog.id)

    if request.method == 'POST':
        sender_dog_id = request.POST.get('sender_dog')
        sender_dog = None
        if sender_dog_id:
            sender_dog = DogProfile.objects.filter(id=sender_dog_id, owner=request.user).first()

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
            messages.success(request, f"❤️ Match request sent to {target_dog.name}'s owner!")
        except ValidationError as e:
            messages.error(request, e.messages[0] if hasattr(e, 'messages') else str(e))

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

    if action == 'accept':
        match_req.status = 'accepted'
        match_req.save()
        messages.success(request, f"You accepted the match request from {match_req.sender.username}!")
    elif action == 'decline':
        match_req.status = 'declined'
        match_req.save()
        messages.info(request, "Match request declined.")

    return redirect('match_requests_dashboard')

@login_required
def chats_inbox(request):
    matches = MatchRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='accepted'
    ).select_related('sender', 'receiver', 'target_dog', 'sender_dog').prefetch_related('messages')

    conversations = []
    for m in matches:
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