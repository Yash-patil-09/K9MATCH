from django.test import TestCase, Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from core.models import DogProfile, VeterinaryClinic, ChatMessage, MatchRequest
from core.forms import DogProfileForm
from core.utils import get_city_coordinates, haversine_distance
from core.views import custom_404_view, custom_403_view, custom_500_view

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
            'secondary_breed': '',  # missing
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

    def test_vets_directory_distance_calculation(self):
        """Clinics should have distance_km calculated relative to city reference point."""
        response = self.client.get(reverse('vets_directory'), {'city': 'Mumbai'})
        self.assertEqual(response.status_code, 200)
        clinics = response.context['clinics']
        self.assertTrue(hasattr(clinics[0], 'distance_km'))
        self.assertIsNotNone(clinics[0].distance_km)


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


