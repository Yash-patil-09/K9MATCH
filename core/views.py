from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone

from .forms import CustomUserCreationForm, DogProfileForm, DogImageForm
from .models import DogProfile, DogImage, MatchRequest, ChatMessage



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

            dog.save()

            # Save uploaded images from multi-file input
            images = request.FILES.getlist('images')
            for img in images:
                DogImage.objects.create(dog=dog, image=img)

            messages.success(request, f"{dog.name}'s profile has been registered successfully!")
            return redirect('my_dogs')
        else:
            messages.error(request, "Please correct the errors below before submitting.")
            print("--- FORM ERRORS ---")
            print(form.errors)
            print(image_form.errors)
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
            
            # Handle radio string-to-boolean check for KCI
            kci_status = request.POST.get('kci_registered')
            if kci_status == 'False' or not updated_dog.kci_registered:
                updated_dog.kci_registered = False
                updated_dog.kci_number = ''
                updated_dog.kci_document = None
            else:
                updated_dog.kci_registered = True

            updated_dog.save()

            # Handle new photo uploads if added during edit
            images = request.FILES.getlist('images')
            for img in images:
                DogImage.objects.create(dog=updated_dog, image=img)

            messages.success(request, f"{updated_dog.name}'s profile updated successfully!")
            return redirect('dog_detail', dog_id=updated_dog.id)
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
    # Base queryset: exclude dogs owned by the logged-in user if authenticated (optional, or keep all)
    dogs = DogProfile.objects.all().order_by('-id')

    # Extract filter parameters from request.GET
    search_query = request.GET.get('q', '').strip()
    breed_filter = request.GET.get('breed', '').strip()
    gender_filter = request.GET.get('gender', '').strip()
    breed_type_filter = request.GET.get('breed_type', '').strip()
    state_filter = request.GET.get('state', '').strip()
    city_filter = request.GET.get('city', '').strip()

    # Apply Filters
    if search_query:
        dogs = dogs.filter(
            Q(name__icontains=search_query) |
            Q(breed__icontains=search_query) |
            Q(city__icontains=search_query) |
            Q(bio__icontains=search_query)
        )

    if breed_filter:
        dogs = dogs.filter(breed__iexact=breed_filter)

    if gender_filter:
        dogs = dogs.filter(gender__iexact=gender_filter)

    if breed_type_filter:
        dogs = dogs.filter(breed_type__iexact=breed_type_filter)

    if state_filter:
        dogs = dogs.filter(state__iexact=state_filter)

    if city_filter:
        dogs = dogs.filter(city__iexact=city_filter)

    # Get distinct values for filter dropdown options
    available_breeds = DogProfile.objects.values_list('breed', flat=True).distinct().order_by('breed')
    available_states = DogProfile.objects.values_list('state', flat=True).distinct().order_by('state')
    available_cities = DogProfile.objects.values_list('city', flat=True).distinct().order_by('city')

    context = {
        'dogs': dogs,
        'search_query': search_query,
        'breed_filter': breed_filter,
        'gender_filter': gender_filter,
        'breed_type_filter': breed_type_filter,
        'state_filter': state_filter,
        'city_filter': city_filter,
        'available_breeds': available_breeds,
        'available_states': available_states,
        'available_cities': available_cities,
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

        MatchRequest.objects.create(
            sender=request.user,
            receiver=target_dog.owner,
            target_dog=target_dog,
            sender_dog=sender_dog,
            message=message_text,
            status='pending'
        )

        messages.success(request, f"❤️ Match request sent to {target_dog.name}'s owner!")
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
def chat_room(request, match_id):
    # Ensure only the sender or receiver of the accepted match can access this room
    match_req = get_object_or_404(MatchRequest, id=match_id, status='accepted')
    
    if request.user != match_req.sender and request.user != match_req.receiver:
        messages.error(request, "You do not have access to this conversation.")
        return redirect('match_requests_dashboard')

    other_user = match_req.receiver if request.user == match_req.sender else match_req.sender

    return render(request, 'core/chat_room.html', {
        'match_req': match_req,
        'other_user': other_user,
    })



@login_required
def chat_room(request, match_id):
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

        text = request.POST.get('message', '').strip()
        if text:
            msg = ChatMessage.objects.create(
                match=match_req,
                sender=request.user,
                message=text
            )
            # Convert timestamp to local time zone
            local_time = timezone.localtime(msg.timestamp).strftime('%I:%M %p')
            return JsonResponse({
                'status': 'ok',
                'sender': msg.sender.username,
                'message': msg.message,
                'timestamp': local_time
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def get_messages_api(request, match_id):
    match_req = get_object_or_404(MatchRequest, id=match_id, status='accepted')
    
    if request.user != match_req.sender and request.user != match_req.receiver:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    messages_data = [
        {
            'sender': m.sender.username,
            'is_me': m.sender == request.user,
            'message': m.message,
            'timestamp': timezone.localtime(m.timestamp).strftime('%I:%M %p')
        }
        for m in match_req.messages.all()
    ]
    return JsonResponse({'messages': messages_data})