import json
from unittest.mock import patch
from django.test import TestCase, Client, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from core.models import DogProfile, VeterinaryClinic, ChatMessage, MatchRequest, ReportListing
from core.forms import DogProfileForm
from core.utils import get_city_coordinates, haversine_distance
from core.views import custom_404_view, custom_403_view, custom_500_view
from core.places_service import get_nearby_vets_dynamic, fetch_google_places_vets

User = get_user_model()

class DogRegistrationValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword123',
            email='test@example.com'
        )

    def test_mandatory_fields_validation(self):
        """Blank form submission must be invalid and flag mandatory fields."""
        form = DogProfileForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('breed', form.errors)
        self.assertIn('age_years', form.errors)
        self.assertIn('gender', form.errors)
        self.assertIn('state', form.errors)
        self.assertIn('city', form.errors)
        self.assertIn('weight', form.errors)
        self.assertIn('is_vaccinated', form.errors)
        self.assertIn('kci_registered', form.errors)
        self.assertIn('is_available', form.errors)

    def test_crossbreed_requires_secondary_breed(self):
        """Selecting crossbreed without specifying secondary_breed should raise validation error."""
        data = {
            'name': 'Buddy',
            'breed_type': 'crossbreed',
            'breed': 'Labradoodle',
            
            'age_years': 2,
            'age_months': 4,
            'gender': 'male',
            'state': 'Maharashtra',
            'city': 'Mumbai',
            'weight': 25.5,
            'weight_unit': 'kg',
            'is_vaccinated': True,
            'kci_registered': False,
            'is_available': True,
            'previous_litters': 0,
            'mating_terms': 'want_puppy',
            'shelter_provider': 'my_place',
            'travel_range': '0-5',
            'dog_friendly_rating': 4,
            'human_friendly_rating': 5,
            'energy_level_rating': 4,
        }
        form = DogProfileForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('secondary_breed', form.errors)

    def test_kci_registered_requires_kci_number(self):
        """KCI registered dogs must have a KCI registration number."""
        data = {
            'name': 'Max',
            'breed_type': 'purebred',
            'breed': 'Golden Retriever',
            'age_years': 3,
            'age_months': 0,
            'gender': 'male',
            'state': 'Maharashtra',
            'city': 'Mumbai',
            'weight': 30.0,
            'weight_unit': 'kg',
            'is_vaccinated': True,
            'kci_registered': True,
            'kci_number': '',  # missing
            'is_available': True,
            'previous_litters': 0,
            'mating_terms': 'negotiable',
            'shelter_provider': 'my_place',
            'travel_range': '0-5',
            'dog_friendly_rating': 4,
            'human_friendly_rating': 4,
            'energy_level_rating': 3,
        }
        form = DogProfileForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('kci_number', form.errors)

    def test_available_for_mating_toggle(self):
        """Test that is_available toggle correctly parses True and False."""
        base_data = {
            'name': 'Charlie',
            'breed_type': 'purebred',
            'breed': 'Beagle',
            'age_years': 1,
            'age_months': 6,
            'gender': 'male',
            'state': 'Maharashtra',
            'city': 'Pune',
            'weight': 12.0,
            'weight_unit': 'kg',
            'is_vaccinated': True,
            'kci_registered': False,
            'previous_litters': 0,
            'mating_terms': 'negotiable',
            'shelter_provider': 'my_place',
            'travel_range': '0-5',
            'dog_friendly_rating': 5,
            'human_friendly_rating': 5,
            'energy_level_rating': 4,
        }

        # Available = True
        data_yes = base_data.copy()
        data_yes['is_available'] = True
        form_yes = DogProfileForm(data=data_yes)
        self.assertTrue(form_yes.is_valid(), form_yes.errors)
        self.assertTrue(form_yes.cleaned_data['is_available'])

        # Available = False (Hidden)
        data_no = base_data.copy()
        data_no['is_available'] = False
        form_no = DogProfileForm(data=data_no)
        self.assertTrue(form_no.is_valid(), form_no.errors)
        self.assertFalse(form_no.cleaned_data['is_available'])

    def test_edit_dog_availability_toggle(self):
        """Editing a dog profile and toggling is_available to False must save and persist."""
        dog = DogProfile.objects.create(
            owner=self.user,
            name='Bella',
            breed='Labrador Retriever',
            age_years=3,
            gender='female',
            city='Mumbai',
            state='Maharashtra',
            weight=25.0,
            is_vaccinated=True,
            kci_registered=False,
            is_available=True,
            approval_status='approved'
        )

        client = Client()
        client.login(username='testuser', password='testpassword123')

        edit_data = {
            'name': 'Bella',
            'breed_type': 'purebred',
            'breed': 'Labrador Retriever',
            'age_years': 3,
            'age_months': 0,
            'gender': 'female',
            'state': 'Maharashtra',
            'city': 'Mumbai',
            'weight': 25.0,
            'weight_unit': 'kg',
            'is_vaccinated': 'True',
            'kci_registered': 'False',
            'previous_litters': 0,
            'mating_terms': 'negotiable',
            'shelter_provider': 'negotiable',
            'travel_range': '0-5',
            'dog_friendly_rating': 4,
            'human_friendly_rating': 4,
            'energy_level_rating': 4,
            'is_available': 'False'
        }

        response = client.post(reverse('edit_dog', args=[dog.id]), edit_data)
        self.assertEqual(response.status_code, 302)
        dog.refresh_from_db()
        self.assertFalse(dog.is_available)

        # Toggle back to True
        edit_data['is_available'] = 'True'
        response2 = client.post(reverse('edit_dog', args=[dog.id]), edit_data)
        self.assertEqual(response2.status_code, 302)
        dog.refresh_from_db()
        self.assertTrue(dog.is_available)

    def test_add_dog_view_sets_pending_status_and_coordinates(self):
        """add_dog view must set approval_status='pending' and calculate coordinates."""
        client = Client()
        client.login(username='testuser', password='testpassword123')

        post_data = {
            'name': 'Simba',
            'breed_type': 'purebred',
            'breed': 'German Shepherd',
            'age_years': 2,
            'age_months': 2,
            'gender': 'male',
            'state': 'Maharashtra',
            'city': 'Mumbai',
            'weight': 32.0,
            'weight_unit': 'kg',
            'is_vaccinated': 'True',
            'kci_registered': 'False',
            'is_available': 'True',
            'previous_litters': 0,
            'mating_terms': 'negotiable',
            'shelter_provider': 'negotiable',
            'travel_range': '0-5',
            'dog_friendly_rating': 4,
            'human_friendly_rating': 4,
            'energy_level_rating': 4,
        }

        response = client.post(reverse('add_dog'), data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        dog = DogProfile.objects.filter(name='Simba').first()
        self.assertIsNotNone(dog)
        self.assertEqual(dog.approval_status, 'pending')
        self.assertTrue(dog.is_available)
        self.assertIsNotNone(dog.latitude)
        self.assertIsNotNone(dog.longitude)

    def test_haversine_distance_calculation(self):
        """Mumbai to Pune distance should be approximately 120-150 km."""
        mumbai_lat, mumbai_lng = get_city_coordinates('Mumbai')
        pune_lat, pune_lng = get_city_coordinates('Pune')
        distance = haversine_distance(mumbai_lat, mumbai_lng, pune_lat, pune_lng)
        self.assertIsNotNone(distance)
        self.assertTrue(100 < distance < 160)

    def test_dog_age_bounds_validation(self):
        """Negative age or age > 25 must fail validation."""
        data_negative = {
            'name': 'Oldie',
            'breed_type': 'purebred',
            'breed': 'Beagle',
            'age_years': -1,
            'age_months': 5,
            'gender': 'male',
            'state': 'Maharashtra',
            'city': 'Mumbai',
            'weight': 10.0,
            'weight_unit': 'kg',
            'is_vaccinated': True,
            'kci_registered': False,
            'is_available': True,
            'previous_litters': 0,
            'mating_terms': 'negotiable',
            'shelter_provider': 'my_place',
            'travel_range': '0-5',
            'dog_friendly_rating': 3,
            'human_friendly_rating': 3,
            'energy_level_rating': 3,
        }
        form_neg = DogProfileForm(data=data_negative)
        self.assertFalse(form_neg.is_valid())
        self.assertIn('age_years', form_neg.errors)

        data_exceed = data_negative.copy()
        data_exceed['age_years'] = 26
        form_exceed = DogProfileForm(data=data_exceed)
        self.assertFalse(form_exceed.is_valid())
        self.assertIn('age_years', form_exceed.errors)

    def test_unauthenticated_route_protection(self):
        """Unauthenticated requests to protected endpoints must redirect to login."""
        client = Client()
        protected_urls = [
            reverse('my_dogs'),
            reverse('add_dog'),
            reverse('profile'),
            reverse('match_requests_dashboard'),
        ]
        for url in protected_urls:
            response = client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('login'), response.url)

    def test_matching_business_rules(self):
        """Model validation must enforce opposite-gender and prevent self-matching."""
        from django.core.exceptions import ValidationError
        from core.models import MatchRequest

        user2 = User.objects.create_user(username='otherowner', password='password123')

        male_dog1 = DogProfile.objects.create(
            owner=self.user, name='Rex', breed='German Shepherd',
            age_years=3, gender='male', city='Mumbai'
        )
        male_dog2 = DogProfile.objects.create(
            owner=user2, name='Thor', breed='Rottweiler',
            age_years=4, gender='male', city='Mumbai'
        )
        female_dog = DogProfile.objects.create(
            owner=user2, name='Bella', breed='German Shepherd',
            age_years=2, gender='female', city='Mumbai'
        )

        # 1. Self-match prevention
        req_self = MatchRequest(sender=self.user, receiver=self.user, target_dog=male_dog1, sender_dog=male_dog1)
        with self.assertRaises(ValidationError):
            req_self.clean()

        # 2. Same gender breeding rejection (male to male)
        req_same_gender = MatchRequest(sender=self.user, receiver=user2, target_dog=male_dog2, sender_dog=male_dog1)
        with self.assertRaises(ValidationError):
            req_same_gender.clean()

        # 3. Valid opposite gender matching (male to female)
        req_valid = MatchRequest(sender=self.user, receiver=user2, target_dog=female_dog, sender_dog=male_dog1)
        req_valid.clean()  # Should succeed without exception
        req_valid.save()
        self.assertEqual(req_valid.status, 'pending')

    def test_chat_message_sanitization(self):
        """Chat input must reject empty whitespace and strip raw HTML tags."""
        client = Client()
        client.login(username='testuser', password='testpassword123')

        user2 = User.objects.create_user(username='partner', password='password123')
        dog1 = DogProfile.objects.create(owner=self.user, name='Dog1', breed='Beagle', age_years=2, gender='male', city='Mumbai')
        dog2 = DogProfile.objects.create(owner=user2, name='Dog2', breed='Beagle', age_years=2, gender='female', city='Mumbai')

        match = MatchRequest.objects.create(
            sender=self.user, receiver=user2, target_dog=dog2, sender_dog=dog1, status='accepted'
        )

        # Reject empty whitespace
        resp_empty = client.post(reverse('send_message_api', args=[match.id]), data={'message': '   '})
        self.assertEqual(resp_empty.status_code, 400)

        # Sanitize HTML tags
        resp_html = client.post(reverse('send_message_api', args=[match.id]), data={'message': '<script>alert("hack")</script>Hello partner!'})
        self.assertEqual(resp_html.status_code, 200)
        self.assertNotIn('<script>', resp_html.json()['message'])
        self.assertIn('alert("hack")Hello partner!', resp_html.json()['message'])

    def test_custom_error_pages(self):
        """Verify custom 404, 403, and 500 error views render properly."""
        client = Client()
        resp_404 = client.get('/this-path-definitely-does-not-exist-404/')
        self.assertEqual(resp_404.status_code, 404)
        self.assertTemplateUsed(resp_404, '404.html')


class Epic2And3DiscoveryAndFilterTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')

        # User 1's dog (Mumbai)
        self.my_dog = DogProfile.objects.create(
            owner=self.user1, name='MyDog', breed='Beagle', breed_type='purebred',
            age_years=2, gender='male', state='Maharashtra', city='Mumbai',
            latitude=19.0760, longitude=72.8777,
            approval_status='approved', is_available=True
        )

        # User 2's approved & available dog in Mumbai (Close by: ~0 km)
        self.partner_mumbai = DogProfile.objects.create(
            owner=self.user2, name='BellaMumbai', breed='Beagle', breed_type='purebred',
            age_years=3, gender='female', state='Maharashtra', city='Mumbai',
            latitude=19.0760, longitude=72.8777,
            approval_status='approved', is_available=True
        )

        # User 2's approved & available dog in Pune (~120-150 km)
        self.partner_pune = DogProfile.objects.create(
            owner=self.user2, name='LunaPune', breed='German Shepherd', breed_type='purebred',
            age_years=2, gender='female', state='Maharashtra', city='Pune',
            latitude=18.5204, longitude=73.8567,
            approval_status='approved', is_available=True
        )

        # User 2's unapproved dog (pending)
        self.pending_dog = DogProfile.objects.create(
            owner=self.user2, name='PendingDog', breed='Beagle', breed_type='purebred',
            age_years=1, gender='female', state='Maharashtra', city='Mumbai',
            latitude=19.0760, longitude=72.8777,
            approval_status='pending', is_available=True
        )

        # User 2's hidden dog (unavailable)
        self.hidden_dog = DogProfile.objects.create(
            owner=self.user2, name='HiddenDog', breed='Beagle', breed_type='purebred',
            age_years=4, gender='female', state='Maharashtra', city='Mumbai',
            latitude=19.0760, longitude=72.8777,
            approval_status='approved', is_available=False
        )

    def test_explore_excludes_own_dogs(self):
        """Logged in user's own dogs must never appear in search results."""
        client = Client()
        client.login(username='user1', password='password123')
        response = client.get(reverse('explore_dogs'))
        self.assertEqual(response.status_code, 200)
        dog_names = [d.name for d in response.context['dogs']]
        self.assertNotIn('MyDog', dog_names)
        self.assertIn('BellaMumbai', dog_names)

    def test_explore_excludes_unapproved_and_hidden_dogs(self):
        """Unapproved (pending/rejected) and hidden (is_available=False) dogs must not appear in discovery."""
        client = Client()
        response = client.get(reverse('explore_dogs'))
        self.assertEqual(response.status_code, 200)
        dog_names = [d.name for d in response.context['dogs']]
        self.assertNotIn('PendingDog', dog_names)
        self.assertNotIn('HiddenDog', dog_names)
        self.assertIn('BellaMumbai', dog_names)
        self.assertIn('LunaPune', dog_names)

    def test_explore_breed_and_gender_filters(self):
        """Filtering by breed and gender should strictly narrow the queryset."""
        client = Client()
        # Filter German Shepherd
        resp_gsd = client.get(reverse('explore_dogs'), {'breed': 'German Shepherd'})
        gsd_names = [d.name for d in resp_gsd.context['dogs']]
        self.assertIn('LunaPune', gsd_names)
        self.assertNotIn('BellaMumbai', gsd_names)

        # Filter Female
        resp_female = client.get(reverse('explore_dogs'), {'gender': 'female'})
        female_names = [d.name for d in resp_female.context['dogs']]
        self.assertIn('BellaMumbai', female_names)
        self.assertIn('LunaPune', female_names)

    def test_explore_radius_distance_filter(self):
        """Radius filter should exclude dogs farther than the specified km."""
        client = Client()
        client.login(username='user1', password='password123')

        # Within 20 km from Mumbai (Bella is in Mumbai ~0 km, Luna is in Pune ~140 km)
        resp_20km = client.get(reverse('explore_dogs'), {'radius': '20', 'my_dog': self.my_dog.id})
        dogs_20km = [d.name for d in resp_20km.context['dogs']]
        self.assertIn('BellaMumbai', dogs_20km)
        self.assertNotIn('LunaPune', dogs_20km)

        # Within 200 km from Mumbai (Should include both Mumbai and Pune)
        resp_200km = client.get(reverse('explore_dogs'), {'radius': '200', 'my_dog': self.my_dog.id})
        dogs_200km = [d.name for d in resp_200km.context['dogs']]
        self.assertIn('BellaMumbai', dogs_200km)
        self.assertIn('LunaPune', dogs_200km)


class Epic4MessagingTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='chatuser1', password='password123')
        self.user2 = User.objects.create_user(username='chatuser2', password='password123')
        self.user3 = User.objects.create_user(username='chatuser3', password='password123')

        self.dog1 = DogProfile.objects.create(
            owner=self.user1, name='DogOne', breed='Beagle', age_years=2, gender='male', city='Mumbai'
        )
        self.dog2 = DogProfile.objects.create(
            owner=self.user2, name='DogTwo', breed='Beagle', age_years=2, gender='female', city='Mumbai'
        )

        self.accepted_match = MatchRequest.objects.create(
            sender=self.user1, receiver=self.user2, target_dog=self.dog2, sender_dog=self.dog1, status='accepted'
        )

        self.message = ChatMessage.objects.create(
            match=self.accepted_match,
            sender=self.user1,
            message="Original message text"
        )

    def test_chats_inbox_renders_accepted_conversations(self):
        """chats_inbox must list accepted match conversations with last message preview."""
        client = Client()
        client.login(username='chatuser1', password='password123')

        response = client.get(reverse('chats_inbox'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/chats_inbox.html')
        self.assertEqual(len(response.context['conversations']), 1)
        conv = response.context['conversations'][0]
        self.assertEqual(conv['other_user'], self.user2)
        self.assertEqual(conv['last_message'], "Original message text")

    def test_edit_message_by_sender(self):
        """Sender should be able to edit their message."""
        client = Client()
        client.login(username='chatuser1', password='password123')

        response = client.post(
            reverse('edit_message_api', args=[self.message.id]),
            {'message': 'Updated text content'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_edited'])
        self.message.refresh_from_db()
        self.assertEqual(self.message.message, 'Updated text content')
        self.assertTrue(self.message.is_edited)

    def test_edit_message_denied_for_other_user(self):
        """User2 must not be able to edit User1's message."""
        client = Client()
        client.login(username='chatuser2', password='password123')

        response = client.post(
            reverse('edit_message_api', args=[self.message.id]),
            {'message': 'Malicious edit attempt'}
        )
        self.assertEqual(response.status_code, 403)
        self.message.refresh_from_db()
        self.assertEqual(self.message.message, 'Original message text')

    def test_delete_message_by_sender(self):
        """Sender can delete message, marking is_deleted=True and updating text."""
        client = Client()
        client.login(username='chatuser1', password='password123')

        response = client.post(reverse('delete_message_api', args=[self.message.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_deleted'])
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_deleted)
        self.assertEqual(self.message.message, "This message was deleted.")

    def test_delete_message_denied_for_other_user(self):
        """Non-sender must not be able to delete another user's message."""
        client = Client()
        client.login(username='chatuser2', password='password123')

        response = client.post(reverse('delete_message_api', args=[self.message.id]))
        self.assertEqual(response.status_code, 403)
        self.message.refresh_from_db()
        self.assertFalse(self.message.is_deleted)


class Epic5AdminWorkflowTest(TestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(username='regular_user', password='password123')
        self.staff_user = User.objects.create_user(username='staff_admin', password='password123', is_staff=True)

        self.pending_dog = DogProfile.objects.create(
            owner=self.regular_user,
            name='TestPendingDog',
            breed='Boxer',
            age_years=2,
            gender='male',
            city='Mumbai',
            approval_status='pending',
            is_available=True
        )

    def test_admin_dashboard_access_restricted_to_staff(self):
        """Non-staff users should be redirected when accessing admin-dashboard."""
        client = Client()
        client.login(username='regular_user', password='password123')
        response = client.get(reverse('admin_dashboard'))
        self.assertNotEqual(response.status_code, 200)
        self.assertEqual(response.status_code, 302)

    def test_staff_can_access_admin_dashboard(self):
        """Staff user can successfully view the admin dashboard."""
        client = Client()
        client.login(username='staff_admin', password='password123')
        response = client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/admin_dashboard.html')
        self.assertContains(response, 'TestPendingDog')

    def test_admin_can_approve_dog(self):
        """Staff user can approve dog; status changes to approved and it shows in explore."""
        client = Client()
        client.login(username='staff_admin', password='password123')

        response = client.post(
            reverse('admin_approve_reject_dog', args=[self.pending_dog.id, 'approve']),
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.pending_dog.refresh_from_db()
        self.assertEqual(self.pending_dog.approval_status, 'approved')

        # Check explore page for this dog as an unauthenticated visitor
        explore_client = Client()
        resp_explore = explore_client.get(reverse('explore_dogs'))
        dog_names = [d.name for d in resp_explore.context['dogs']]
        self.assertIn('TestPendingDog', dog_names)

    def test_admin_can_reject_dog_with_reason(self):
        """Staff user can reject dog with reason; status changes to rejected."""
        client = Client()
        client.login(username='staff_admin', password='password123')

        response = client.post(
            reverse('admin_approve_reject_dog', args=[self.pending_dog.id, 'reject']),
            {'rejection_reason': 'Vaccination certificate illegible'},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.pending_dog.refresh_from_db()
        self.assertEqual(self.pending_dog.approval_status, 'rejected')
        self.assertEqual(self.pending_dog.admin_rejection_reason, 'Vaccination certificate illegible')


@override_settings(GOOGLE_MAPS_API_KEY='')
class Epic6VeterinaryDirectoryTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.clinic_mumbai = VeterinaryClinic.objects.create(
            name="Mumbai 24/7 Animal Hospital",
            doctor_name="Dr. Rohan Sharma",
            specialization="Emergency & Orthopedics",
            phone_number="+91 98200 12345",
            email="mumbai@paws.in",
            address="Linking Road, Bandra",
            city="Mumbai",
            state="Maharashtra",
            latitude=19.0596,
            longitude=72.8295,
            is_24x7_emergency=True,
            rating=4.9,
            services_offered="ICU, Surgery, Blood Bank"
        )
        self.clinic_pune = VeterinaryClinic.objects.create(
            name="Pune Pet Care Clinic",
            doctor_name="Dr. Sneha Kulkarni",
            specialization="Vaccinations & OPD",
            phone_number="+91 98220 54321",
            address="FC Road, Shivaji Nagar",
            city="Pune",
            state="Maharashtra",
            latitude=18.5204,
            longitude=73.8567,
            is_24x7_emergency=False,
            rating=4.6,
            services_offered="Vaccinations, Grooming"
        )
        self.clinic_delhi = VeterinaryClinic.objects.create(
            name="Delhi Emergency Vet Centre",
            doctor_name="Dr. Anil Khanna",
            specialization="Trauma Care",
            phone_number="+91 98110 99887",
            address="Defence Colony",
            city="Delhi",
            state="Delhi",
            latitude=28.5729,
            longitude=77.2341,
            is_24x7_emergency=True,
            rating=4.8,
            services_offered="24/7 Emergency, CT Scan"
        )

    def test_vets_directory_renders_all_clinics(self):
        """Directory view should render HTTP 200 with all clinics."""
        response = self.client.get(reverse('vets_directory'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/vets_directory.html')
        self.assertEqual(len(response.context['clinics']), 3)
        self.assertContains(response, "Mumbai 24/7 Animal Hospital")
        self.assertContains(response, "Pune Pet Care Clinic")

    def test_vets_directory_city_filter(self):
        """Filtering by city returns only clinics in that city."""
        response = self.client.get(reverse('vets_directory'), {'city': 'Mumbai'})
        self.assertEqual(response.status_code, 200)
        clinics = response.context['clinics']
        self.assertEqual(len(clinics), 1)
        self.assertEqual(clinics[0].name, "Mumbai 24/7 Animal Hospital")

    def test_vets_directory_emergency_filter(self):
        """Filtering by emergency=true returns only 24x7 emergency clinics."""
        response = self.client.get(reverse('vets_directory'), {'emergency': 'true'})
        self.assertEqual(response.status_code, 200)
        clinics = response.context['clinics']
        self.assertEqual(len(clinics), 2)
        for clinic in clinics:
            self.assertTrue(clinic.is_24x7_emergency)

    def test_vets_directory_search_query(self):
        """Search query matches clinic name, doctor, specialization, or services."""
        response = self.client.get(reverse('vets_directory'), {'q': 'Sneha'})
        self.assertEqual(response.status_code, 200)
        clinics = response.context['clinics']
        self.assertEqual(len(clinics), 1)
        self.assertEqual(clinics[0].name, "Pune Pet Care Clinic")

    def test_vets_directory_state_filter(self):
        """Filtering by state returns only clinics located in that state."""
        response = self.client.get(reverse('vets_directory'), {'state': 'Maharashtra'})
        self.assertEqual(response.status_code, 200)
        clinics = response.context['clinics']
        self.assertEqual(len(clinics), 2)
        for c in clinics:
            self.assertEqual(c.state, "Maharashtra")

    def test_vets_directory_distance_calculation(self):
        """Clinics should have distance_km calculated relative to city reference point."""
        response = self.client.get(reverse('vets_directory'), {'city': 'Mumbai'})
        self.assertEqual(response.status_code, 200)
        clinics = response.context['clinics']
        self.assertTrue(hasattr(clinics[0], 'distance_km'))
        self.assertIsNotNone(clinics[0].distance_km)

    def test_vets_directory_live_gps_distance_and_radius(self):
        """Passing user_lat, user_lng, and radius=5 should filter clinics within 5km."""
        # Clinic Mumbai is at (19.0596, 72.8295). User is at (19.0600, 72.8300) - ~0.1 km away
        response = self.client.get(reverse('vets_directory'), {
            'user_lat': '19.0600',
            'user_lng': '72.8300',
            'radius': '5'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_live_gps'])
        clinics = response.context['clinics']
        self.assertEqual(len(clinics), 1)
        self.assertEqual(clinics[0].name, "Mumbai 24/7 Animal Hospital")
        self.assertLess(clinics[0].distance_km, 5.0)

    def test_vets_directory_smart_fallback_when_none_in_radius(self):
        """When 0 clinics are within strict radius, smart fallback provides closest clinics."""
        # Location far from any test clinic (e.g. 24.0, 78.0)
        response = self.client.get(reverse('vets_directory'), {
            'user_lat': '24.0000',
            'user_lng': '78.0000',
            'radius': '5'
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['has_expanded_fallback'])
        self.assertGreater(len(response.context['clinics']), 0)


class Phase3SecurityAndPerformanceTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_secret_key_and_env_loaded(self):
        """SECRET_KEY should be configured and non-empty."""
        self.assertTrue(bool(settings.SECRET_KEY))
        self.assertGreater(len(settings.SECRET_KEY), 10)

    def test_security_headers_configured(self):
        """Standard HTTP security headers should be enabled."""
        self.assertTrue(getattr(settings, 'SECURE_BROWSER_XSS_FILTER', False))
        self.assertTrue(getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', False))
        self.assertEqual(getattr(settings, 'X_FRAME_OPTIONS', None), 'DENY')

    def test_database_indexes_defined_on_models(self):
        """Ensure performance database indexes exist on key models."""
        dog_indexes = [idx.fields for idx in DogProfile._meta.indexes]
        self.assertIn(['approval_status', 'is_available'], dog_indexes)
        self.assertIn(['city'], dog_indexes)
        self.assertIn(['breed'], dog_indexes)
        self.assertIn(['gender'], dog_indexes)

        match_indexes = [idx.fields for idx in MatchRequest._meta.indexes]
        self.assertIn(['sender', 'status'], match_indexes)
        self.assertIn(['receiver', 'status'], match_indexes)
        self.assertIn(['target_dog', 'status'], match_indexes)

        chat_indexes = [idx.fields for idx in ChatMessage._meta.indexes]
        self.assertIn(['match', 'timestamp'], chat_indexes)

        clinic_indexes = [idx.fields for idx in VeterinaryClinic._meta.indexes]
        self.assertIn(['city'], clinic_indexes)
        self.assertIn(['is_24x7_emergency'], clinic_indexes)

    def test_custom_404_view(self):
        """Custom 404 view should render 404.html with status 404."""
        request = self.factory.get('/nonexistent-test-url-404/')
        response = custom_404_view(request)
        self.assertEqual(response.status_code, 404)

    def test_custom_403_view(self):
        """Custom 403 view should render 403.html with status 403."""
        request = self.factory.get('/forbidden-test-url-403/')
        response = custom_403_view(request)
        self.assertEqual(response.status_code, 403)

    def test_custom_500_view(self):
        """Custom 500 view should render 500.html with status 500."""
        request = self.factory.get('/server-error-test-url-500/')
        response = custom_500_view(request)
        self.assertEqual(response.status_code, 500)


from core.models import EmailOTP
from core.email_utils import send_otp_email

class EmailOTPAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@gmail.com',
            password='password123'
        )

    def test_otp_generation_and_validation(self):
        """OTP should be 6-digits and validate correctly."""
        otp = EmailOTP.generate_otp(email='new@gmail.com', purpose='signup')
        self.assertEqual(len(otp.otp_code), 6)
        self.assertTrue(otp.otp_code.isdigit())

        # Wrong code
        valid, msg = otp.is_valid('000000')
        self.assertFalse(valid)

        # Correct code
        valid, msg = otp.is_valid(otp.otp_code)
        self.assertTrue(valid)

        # Cannot reuse already used OTP
        valid, msg = otp.is_valid(otp.otp_code)
        self.assertFalse(valid)

    def test_send_otp_email_utility(self):
        """send_otp_email should create OTP and send email."""
        success, otp_obj, err = send_otp_email('test_mail@gmail.com', purpose='signup')
        self.assertTrue(success)
        self.assertIsNotNone(otp_obj)
        self.assertEqual(len(otp_obj.otp_code), 6)

    def test_registration_flow_with_otp(self):
        """Submitting registration should stage session and verify via OTP."""
        post_data = {
            'username': 'newpupowner',
            'email': 'newpup@gmail.com',
            'role': 'owner',
            'phone_number': '9876543210',
            'password1': 'ComplexP@ss123',
            'password2': 'ComplexP@ss123',
        }
        res = self.client.post(reverse('register'), post_data)
        self.assertRedirects(res, reverse('verify_registration_otp'))

        # Check session
        self.assertEqual(self.client.session.get('otp_email'), 'newpup@gmail.com')

        # Retrieve generated OTP
        otp_obj = EmailOTP.objects.filter(email='newpup@gmail.com', purpose='signup', is_used=False).first()
        self.assertIsNotNone(otp_obj)

        # Submit OTP to activate
        res2 = self.client.post(reverse('verify_registration_otp'), {'otp_code': otp_obj.otp_code})
        self.assertRedirects(res2, reverse('home'))

        # User now created and active
        self.assertTrue(User.objects.filter(username='newpupowner').exists())

    def test_forgot_password_flow_with_otp(self):
        """Forgot password should generate OTP and allow resetting password."""
        res = self.client.post(reverse('forgot_password'), {'email': 'existing@gmail.com'})
        self.assertRedirects(res, reverse('reset_password_otp'))

        otp_obj = EmailOTP.objects.filter(email='existing@gmail.com', purpose='forgot_password', is_used=False).first()
        self.assertIsNotNone(otp_obj)

        # Submit valid OTP and new password
        res2 = self.client.post(reverse('reset_password_otp'), {
            'otp_code': otp_obj.otp_code,
            'new_password1': 'NewSecretPass123',
            'new_password2': 'NewSecretPass123',
        })
        self.assertRedirects(res2, reverse('login'))

        # Verify password updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecretPass123'))

    def test_google_login_redirect(self):
        """Google login redirect test."""
        res = self.client.get(reverse('google_login'))
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            self.assertEqual(res.status_code, 302)
            self.assertTrue(res.url.startswith('https://accounts.google.com/o/oauth2/v2/auth'))
        else:
            self.assertRedirects(res, reverse('login'))


class AutomaticLocationAndDistanceFilterTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username='breeder_bob',
            email='bob@k9match.com',
            password='Password123'
        )
        self.seeker = User.objects.create_user(
            username='seeker_sara',
            email='sara@k9match.com',
            password='Password123'
        )

        # Reference point: Mumbai CST (18.9400, 72.8350)
        # Dog 1: Marine Lines (18.9430, 72.8230) -> ~1.3 km away
        self.dog_1km = DogProfile.objects.create(
            owner=self.owner,
            name='Bruno',
            breed='Labrador Retriever',
            age_years=3,
            age_months=2,
            gender='male',
            state='Maharashtra',
            city='Mumbai',
            latitude=18.943000,
            longitude=72.823000,
            location_address='Marine Lines',
            approval_status='approved',
            is_available=True,
            weight=30.0,
            is_vaccinated=True,
            kci_registered=True,
        )

        # Dog 2: Dadar (19.0178, 72.8478) -> ~8.7 km away
        self.dog_8km = DogProfile.objects.create(
            owner=self.owner,
            name='Rocky',
            breed='Golden Retriever',
            age_years=2,
            age_months=5,
            gender='male',
            state='Maharashtra',
            city='Mumbai',
            latitude=19.017800,
            longitude=72.847800,
            location_address='Dadar West',
            approval_status='approved',
            is_available=True,
            weight=28.0,
            is_vaccinated=True,
            kci_registered=False,
        )

        # Dog 3: Thane (19.2183, 72.9781) -> ~34 km away
        self.dog_34km = DogProfile.objects.create(
            owner=self.owner,
            name='Max',
            breed='German Shepherd',
            age_years=4,
            age_months=0,
            gender='male',
            state='Maharashtra',
            city='Thane',
            latitude=19.218300,
            longitude=72.978100,
            location_address='Thane West',
            approval_status='approved',
            is_available=True,
            weight=35.0,
            is_vaccinated=True,
            kci_registered=True,
        )

    def test_dog_creation_with_real_coordinates(self):
        """Dog profile correctly stores precise decimal coordinates and neighborhood."""
        self.assertEqual(float(self.dog_1km.latitude), 18.943)
        self.assertEqual(float(self.dog_1km.longitude), 72.823)
        self.assertEqual(self.dog_1km.location_address, 'Marine Lines')

    def test_radius_filter_5km_excludes_dogs_further_away(self):
        """5km radius should only return the 1.3km dog, excluding 8.7km and 34km dogs."""
        url = reverse('explore_dogs')
        res = self.client.get(url, {
            'user_lat': '18.9400',
            'user_lng': '72.8350',
            'radius': '5'
        })
        self.assertEqual(res.status_code, 200)
        returned_dogs = res.context['dogs']
        returned_ids = [d.id for d in returned_dogs]

        self.assertIn(self.dog_1km.id, returned_ids)
        self.assertNotIn(self.dog_8km.id, returned_ids)
        self.assertNotIn(self.dog_34km.id, returned_ids)

    def test_radius_filter_10km_includes_5km_and_excludes_34km(self):
        """10km radius should return both the 1.3km and 8.7km dogs, excluding the 34km dog."""
        url = reverse('explore_dogs')
        res = self.client.get(url, {
            'user_lat': '18.9400',
            'user_lng': '72.8350',
            'radius': '10'
        })
        self.assertEqual(res.status_code, 200)
        returned_dogs = res.context['dogs']
        returned_ids = [d.id for d in returned_dogs]

        self.assertIn(self.dog_1km.id, returned_ids)
        self.assertIn(self.dog_8km.id, returned_ids)
        self.assertNotIn(self.dog_34km.id, returned_ids)

        # Closest dog should be sorted first
        self.assertEqual(returned_dogs[0].id, self.dog_1km.id)
        self.assertEqual(returned_dogs[1].id, self.dog_8km.id)

    def test_near_me_gps_parameter_displays_relative_distance(self):
        """Explore page displays calculated distance badge for nearby dogs."""
        url = reverse('explore_dogs')
        res = self.client.get(url, {
            'user_lat': '18.9400',
            'user_lng': '72.8350'
        })
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')

        self.assertIn('km away', content)
        self.assertIn('Near Current Device GPS', content)

    def test_privacy_exact_coordinates_not_leaked_publicly(self):
        """Exact latitude and longitude numbers must never be leaked in public HTML."""
        url = reverse('explore_dogs')
        res = self.client.get(url, {
            'user_lat': '18.9400',
            'user_lng': '72.8350'
        })
        content = res.content.decode('utf-8')

        # Raw coordinate strings must not appear in HTML
        self.assertNotIn('18.943000', content)
        self.assertNotIn('72.823000', content)
        self.assertNotIn('19.017800', content)

        # But neighborhood and distance are safely shown
        self.assertIn('Marine Lines', content)
        self.assertIn('km away', content)

        # Same privacy check on logged-in dog detail page
        self.client.login(username='seeker_sara', password='Password123')
        detail_res = self.client.get(reverse('dog_detail', args=[self.dog_1km.id]))
        self.assertEqual(detail_res.status_code, 200)
        detail_content = detail_res.content.decode('utf-8')
        self.assertNotIn('18.943000', detail_content)
        self.assertNotIn('72.823000', detail_content)
        self.assertIn('Marine Lines', detail_content)


class MatchProposalWorkflowTests(TestCase):
    def setUp(self):
        self.owner_a = User.objects.create_user(username='owner_a', email='a@example.com', password='Password123')
        self.owner_b = User.objects.create_user(username='owner_b', email='b@example.com', password='Password123')

        self.dog_a = DogProfile.objects.create(
            owner=self.owner_a,
            name='Rocky',
            breed='Golden Retriever',
            gender='male',
            age_years=3,
            state='Maharashtra',
            city='Mumbai',
            weight=30.0,
            is_vaccinated=True,
            is_available=True,
            mating_terms='want_puppy'
        )

        self.dog_b = DogProfile.objects.create(
            owner=self.owner_b,
            name='Bella',
            breed='Golden Retriever',
            gender='female',
            age_years=2,
            state='Maharashtra',
            city='Mumbai',
            weight=26.0,
            is_vaccinated=True,
            is_available=True,
            mating_terms='want_puppy'
        )

    def test_ajax_send_proposal_returns_json_and_success_message(self):
        """AJAX POST to send_match_request returns JSON with success flag and message."""
        self.client.login(username='owner_a', password='Password123')
        url = reverse('send_match_request', args=[self.dog_b.id])
        res = self.client.post(
            url,
            {'sender_dog': self.dog_a.id, 'message': 'Hello, interested in pairing!'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            HTTP_ACCEPT='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get('success'))
        self.assertIn('Match request sent to Bella', data.get('message', ''))

        # Verify request exists in database
        self.assertTrue(MatchRequest.objects.filter(sender=self.owner_a, target_dog=self.dog_b, status='pending').exists())

    def test_sent_request_displays_request_sent_button_on_dog_detail(self):
        """When viewing dog_detail for a dog with a pending sent request, 'Request Sent' button is rendered."""
        MatchRequest.objects.create(
            sender=self.owner_a,
            receiver=self.owner_b,
            sender_dog=self.dog_a,
            target_dog=self.dog_b,
            status='pending'
        )
        self.client.login(username='owner_a', password='Password123')
        res = self.client.get(reverse('dog_detail', args=[self.dog_b.id]))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertIn('Request Sent', content)
        self.assertIn('You Sent a Breeding Proposal for Bella', content)

    def test_inbound_proposal_rendered_with_decision_panel_at_end_of_profile(self):
        """When recipient views sender dog profile, inbound proposal banner and decision panel appear."""
        proposal = MatchRequest.objects.create(
            sender=self.owner_a,
            receiver=self.owner_b,
            sender_dog=self.dog_a,
            target_dog=self.dog_b,
            message='Please review Rocky for Bella!',
            status='pending'
        )
        self.client.login(username='owner_b', password='Password123')
        res = self.client.get(reverse('dog_detail', args=[self.dog_a.id]) + f'?proposal_id={proposal.id}')
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')

        # Check top notification banner
        self.assertIn('Breeding Match Proposal Received for Bella', content)
        # Check decision panel at end of profile
        self.assertIn('proposal-decision-panel', content)
        self.assertIn('Accept Proposal', content)
        self.assertIn('Reject Proposal', content)
        self.assertIn('Please review Rocky for Bella!', content)

    def test_inbound_proposal_accept_via_respond_view(self):
        """Accepting proposal sets status to accepted and provides chat link."""
        proposal = MatchRequest.objects.create(
            sender=self.owner_a,
            receiver=self.owner_b,
            sender_dog=self.dog_a,
            target_dog=self.dog_b,
            status='pending'
        )
        self.client.login(username='owner_b', password='Password123')
        url = reverse('respond_match_request', args=[proposal.id, 'accept'])
        res = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('action'), 'accepted')

        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'accepted')

    def test_inbound_proposal_reject_via_respond_view(self):
        """Rejecting proposal sets status to declined."""
        proposal = MatchRequest.objects.create(
            sender=self.owner_a,
            receiver=self.owner_b,
            sender_dog=self.dog_a,
            target_dog=self.dog_b,
            status='pending'
        )
        self.client.login(username='owner_b', password='Password123')
        url = reverse('respond_match_request', args=[proposal.id, 'reject'])
        res = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('action'), 'declined')

        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'declined')

    def test_prevent_duplicate_pending_proposal_same_dog_pair(self):
        """Cannot send a proposal for the same dog pair if one is already pending in either direction."""
        # Proposal from dog_a to dog_b
        MatchRequest.objects.create(
            sender=self.owner_a,
            receiver=self.owner_b,
            sender_dog=self.dog_a,
            target_dog=self.dog_b,
            status='pending'
        )

        # Owner B tries to send proposal back from dog_b to dog_a
        self.client.login(username='owner_b', password='Password123')
        url = reverse('send_match_request', args=[self.dog_a.id])
        res = self.client.post(url, data={'sender_dog': self.dog_b.id, 'message': 'Reverse request'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data.get('success'))
        self.assertTrue(data.get('already_sent'))
        self.assertIn('already', data.get('error', '').lower())

    def test_prevent_proposal_when_already_matched(self):
        """Cannot send another proposal for a pair that is already accepted/matched."""
        MatchRequest.objects.create(
            sender=self.owner_a,
            receiver=self.owner_b,
            sender_dog=self.dog_a,
            target_dog=self.dog_b,
            status='accepted'
        )

        # Owner A tries to send another proposal for dog_b
        self.client.login(username='owner_a', password='Password123')
        url = reverse('send_match_request', args=[self.dog_b.id])
        res = self.client.post(url, data={'sender_dog': self.dog_a.id, 'message': 'Second proposal'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = res.json()
        self.assertTrue(data.get('already_matched'))
        self.assertIn('already matched', data.get('error', '').lower())

    def test_single_conversation_per_dog_pair_in_chats_inbox(self):
        """Chats inbox strictly displays a single conversation per pair of dogs."""
        match = MatchRequest.objects.create(
            sender=self.owner_a,
            receiver=self.owner_b,
            sender_dog=self.dog_a,
            target_dog=self.dog_b,
            status='accepted'
        )
        self.client.login(username='owner_a', password='Password123')
        res = self.client.get(reverse('chats_inbox'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['conversations']), 1)


class CompetitorLimitationsResolutionTests(TestCase):
    """
    Automated test coverage ensuring K9Match overcomes competitor limitations:
    1. Petmeetly Underage Breeding Prevention (<18 months).
    2. PairMyPet / Petmeetly Mandatory KCI & Health Document Verification.
    3. PairMyPet 1-Click Availability Switch.
    4. Herobreeder Data Portability (Exportable PDF Canine Passport).
    5. DogSpot / Dogs India Community Listing Reporting & Moderation.
    """

    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username='breeder_owner',
            email='owner@k9match.com',
            phone_number='9876543210',
            password='Password123'
        )
        self.staff_admin = User.objects.create_user(
            username='moderator_staff',
            email='admin@k9match.com',
            phone_number='9876543211',
            password='Password123',
            is_staff=True
        )
        self.reporter = User.objects.create_user(
            username='vigilant_user',
            email='reporter@k9match.com',
            phone_number='9876543212',
            password='Password123'
        )

        self.adult_dog = DogProfile.objects.create(
            owner=self.owner,
            name='Thor',
            breed='German Shepherd',
            age_years=2,
            age_months=4,
            gender='male',
            city='Mumbai',
            weight=32.0,
            is_vaccinated=True,
            is_available=True,
            approval_status='approved'
        )

        self.junior_dog = DogProfile.objects.create(
            owner=self.owner,
            name='PuppyRex',
            breed='Golden Retriever',
            age_years=1,
            age_months=2, # 14 months total (< 18 months)
            gender='male',
            city='Pune',
            weight=20.0,
            is_vaccinated=True,
            is_available=False,
            approval_status='approved'
        )

    def test_underage_breeding_validation_error(self):
        """Underage dog (<18 months) cannot be marked available for mating."""
        from django.core.exceptions import ValidationError
        self.junior_dog.is_available = True
        with self.assertRaises(ValidationError):
            self.junior_dog.clean()

    def test_underage_breeding_allowed_when_resting(self):
        """Underage dog can be registered and saved as long as is_available=False."""
        self.junior_dog.is_available = False
        # clean() should not raise any validation error
        self.junior_dog.clean()
        self.assertFalse(self.junior_dog.is_breeding_age)
        self.assertEqual(self.junior_dog.total_age_months, 14)

    def test_kci_registration_requires_document_in_clean(self):
        """Canine marked as KCI registered must provide kci_document."""
        from django.core.exceptions import ValidationError
        self.adult_dog.kci_registered = True
        self.adult_dog.kci_document = None
        with self.assertRaises(ValidationError):
            self.adult_dog.clean()

    def test_toggle_dog_availability_ajax_success(self):
        """Owner can toggle adult dog availability on and off via 1-click AJAX."""
        self.client.login(username='breeder_owner', password='Password123')
        url = reverse('toggle_dog_availability', args=[self.adult_dog.id])

        # Toggle from available (True) to resting (False)
        res = self.client.post(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertFalse(data['is_available'])
        self.adult_dog.refresh_from_db()
        self.assertFalse(self.adult_dog.is_available)

        # Toggle back to available (True)
        res2 = self.client.post(url)
        self.assertEqual(res2.status_code, 200)
        data2 = res2.json()
        self.assertTrue(data2['success'])
        self.assertTrue(data2['is_available'])
        self.adult_dog.refresh_from_db()
        self.assertTrue(self.adult_dog.is_available)

    def test_toggle_dog_availability_blocks_underage(self):
        """Attempting to activate an underage dog via 1-click toggle fails with 400 error."""
        self.client.login(username='breeder_owner', password='Password123')
        url = reverse('toggle_dog_availability', args=[self.junior_dog.id])

        res = self.client.post(url)
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data['success'])
        self.assertIn('Ethical Safeguard', data['error'])
        self.junior_dog.refresh_from_db()
        self.assertFalse(self.junior_dog.is_available)

    def test_export_dog_passport_pdf_generation(self):
        """User can download authenticated canine passport PDF."""
        self.client.login(username='breeder_owner', password='Password123')
        url = reverse('export_dog_passport_pdf', args=[self.adult_dog.id])
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/pdf')
        self.assertIn('Thor_K9Match_Passport.pdf', res['Content-Disposition'])
        self.assertTrue(len(res.content) > 1000)

    def test_report_dog_listing_workflow(self):
        """Community member can report a suspicious listing and admin can resolve it."""
        self.client.login(username='vigilant_user', password='Password123')
        report_url = reverse('report_dog_listing', args=[self.adult_dog.id])

        post_data = {
            'reason': 'puppy_mill',
            'details': 'Suspicious commercial breeder advertising multiple unrelated litters.'
        }
        res = self.client.post(report_url, data=post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        report = ReportListing.objects.filter(reported_dog=self.adult_dog).first()
        self.assertIsNotNone(report)
        self.assertEqual(report.reporter, self.reporter)
        self.assertEqual(report.reason, 'puppy_mill')
        self.assertFalse(report.is_resolved)

        # Admin resolves the report and suspends the dog
        self.client.login(username='moderator_staff', password='Password123')
        resolve_url = reverse('admin_resolve_report', args=[report.id])
        admin_res = self.client.post(resolve_url, data={
            'action': 'suspend_dog',
            'admin_notes': 'Confirmed commercial puppy mill violation.'
        }, follow=True)
        self.assertEqual(admin_res.status_code, 200)

        report.refresh_from_db()
        self.assertTrue(report.is_resolved)
        self.adult_dog.refresh_from_db()
        self.assertEqual(self.adult_dog.approval_status, 'rejected')
        self.assertFalse(self.adult_dog.is_available)


class DynamicVeterinaryRadarTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.clinic = VeterinaryClinic.objects.create(
            name="Panvel Pet Clinic & Surgical Centre",
            doctor_name="Dr. Vivek Deshmukh",
            specialization="Canine Theriogenology",
            address="Shop 4, Near Station, Old Panvel",
            city="Panvel",
            state="Maharashtra",
            latitude=18.9894,
            longitude=73.1175,
            is_24x7_emergency=True,
            rating=4.9
        )

    def test_dynamic_vets_fallback_without_api_key(self):
        """When no Google Maps API key is set, dynamic service falls back to local database."""
        with patch.object(settings, 'GOOGLE_MAPS_API_KEY', ''):
            result = get_nearby_vets_dynamic(lat=18.9894, lng=73.1175, radius_km=10, city="Panvel")
            self.assertEqual(result['status'], 'success')
            self.assertFalse(result['google_places_active'])
            self.assertFalse(result['google_places_configured'])
            self.assertGreaterEqual(result['total_count'], 1)
            self.assertEqual(result['clinics'][0].name, "Panvel Pet Clinic & Surgical Centre")
            self.assertEqual(result['clinics'][0].distance_km, 0.0)

    @patch('core.places_service.urllib.request.urlopen')
    def test_dynamic_vets_with_google_places_mock(self, mock_urlopen):
        """When Google Maps API key is present, queries Google Places and standardizes clinics."""
        mock_response = {
            "places": [
                {
                    "id": "ChIJ1234567890",
                    "displayName": {"text": "Panvel 24/7 Advanced Veterinary Hospital"},
                    "formattedAddress": "Sector 15, New Panvel, Panvel, Maharashtra",
                    "rating": 4.8,
                    "userRatingCount": 95,
                    "location": {"latitude": 18.9950, "longitude": 73.1200},
                    "currentOpeningHours": {"openNow": True},
                    "types": ["veterinary_care", "hospital"]
                },
                {
                    "id": "ChIJ0987654321",
                    "displayName": {"text": "Khanda Colony Pet Clinic"},
                    "formattedAddress": "Khanda Colony, Panvel, Maharashtra",
                    "rating": 4.6,
                    "userRatingCount": 42,
                    "location": {"latitude": 19.0060, "longitude": 73.1100},
                    "currentOpeningHours": {"openNow": False},
                    "types": ["veterinary_care"]
                }
            ]
        }
        mock_urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(mock_response).encode('utf-8')

        with patch.object(settings, 'GOOGLE_MAPS_API_KEY', 'AIzaFakeTestKeyForGooglePlaces123'):
            result = get_nearby_vets_dynamic(lat=18.9894, lng=73.1175, radius_km=10)
            self.assertEqual(result['status'], 'success')
            self.assertTrue(result['google_places_active'])
            self.assertTrue(result['google_places_configured'])
            self.assertGreaterEqual(result['total_count'], 2)
            names = [c.name for c in result['clinics']]
            self.assertIn("Panvel 24/7 Advanced Veterinary Hospital", names)
            self.assertIn("Khanda Colony Pet Clinic", names)
            gp_emergency = next(c for c in result['clinics'] if c.name == "Panvel 24/7 Advanced Veterinary Hospital")
            self.assertTrue(gp_emergency.is_24x7_emergency)

    def test_api_nearby_vets_endpoint(self):
        """API endpoint /api/vets/nearby/ returns JSON HTTP 200 with dynamic search results."""
        url = reverse('api_nearby_vets')
        res = self.client.get(url, {'lat': '18.9894', 'lng': '73.1175', 'radius': '10', 'city': 'Panvel'})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('clinics', data)
        self.assertIn('google_places_active', data)
        self.assertIn('total_count', data)
        self.assertGreaterEqual(data['total_count'], 1)







