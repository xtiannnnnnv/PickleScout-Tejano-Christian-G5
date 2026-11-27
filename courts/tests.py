from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser
from .forms import CourtForm
from .models import Court


class CourtAccessAndCreationTests(TestCase):
    def setUp(self):
        self.player = CustomUser.objects.create_user(
            username='court-player',
            password='test-password',
        )

    def court_data(self, **overrides):
        data = {
            'name': 'Community Pickleball Courts',
            'description': 'Outdoor courts for local players.',
            'facility_type': Court.FacilityType.OUTDOOR,
            'surface_type': Court.SurfaceType.SILICA_SAND,
            'number_of_courts': '2',
            'address': '123 Cebu Road',
        }
        data.update(overrides)
        return data

    def test_anonymous_users_can_browse_but_not_add_courts(self):
        court = Court.objects.create(
            name='Community Pickleball Courts',
            address='123 Cebu Road',
            created_by=self.player,
            contact_number='09123456789',
            email='court@example.com',
        )
        public_paths = [
            reverse('landing'),
            reverse('court_list'),
            reverse('court_detail', kwargs={'pk': court.pk}),
        ]
        for path in public_paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

        court_list_response = self.client.get(reverse('court_list'))
        self.assertNotContains(court_list_response, 'Add Court')
        court_detail_response = self.client.get(
            reverse('court_detail', kwargs={'pk': court.pk})
        )
        self.assertNotContains(court_detail_response, '09123456789')
        self.assertNotContains(court_detail_response, 'mailto:')

        create_response = self.client.get(reverse('court_create'))
        self.assertEqual(create_response.status_code, 302)
        self.assertIn('/accounts/login/', create_response.url)
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)

    def test_logged_in_player_can_create_court_without_optional_location_fields(self):
        self.client.force_login(self.player)
        court_list_response = self.client.get(reverse('court_list'))
        self.assertContains(court_list_response, 'Add Court')
        court_form_response = self.client.get(reverse('court_create'))
        self.assertContains(court_form_response, 'Court Quality')
        self.assertContains(court_form_response, 'Facilities')
        self.assertContains(court_form_response, 'Affordability')
        self.assertContains(court_form_response, 'Accessibility')
        self.assertContains(court_form_response, 'Equipment')
        self.assertContains(court_form_response, 'Staff &amp; Service')
        self.assertContains(court_form_response, 'Overall Experience')
        self.assertContains(court_form_response, '<span class="input-group-text">/ 10</span>')
        self.assertNotContains(court_form_response, '1 / 10')
        self.assertEqual(
            [label for _, label in CourtForm.base_fields['overall_rating'].choices[1:]],
            [str(rating) for rating in range(1, 11)],
        )
        self.assertContains(court_form_response, 'Additional Review (optional)')
        rental_price_widget = CourtForm.base_fields['rental_price'].widget
        self.assertEqual(rental_price_widget.input_type, 'text')
        self.assertEqual(rental_price_widget.attrs['inputmode'], 'decimal')
        self.assertNotIn('step', rental_price_widget.attrs)

        response = self.client.post(
            reverse('court_create'),
            self.court_data(description='', rental_price='150'),
        )

        self.assertEqual(response.status_code, 302)
        court = Court.objects.get(name='Community Pickleball Courts')
        self.assertEqual(court.created_by, self.player)
        self.assertEqual(court.city, 'Cebu')
        self.assertEqual(court.review_topics, [])
        self.assertEqual(court.description, '')
        self.assertIsNone(court.overall_rating)
        self.assertEqual(court.rental_price, Decimal('150.00'))
        self.assertIsNone(court.latitude)
        self.assertIsNone(court.longitude)
        self.assertNotIn('city', CourtForm.base_fields)
        self.assertNotIn('province_state', CourtForm.base_fields)
        self.assertNotIn('zip_code', CourtForm.base_fields)
        self.assertNotIn('latitude', CourtForm.base_fields)
        self.assertNotIn('longitude', CourtForm.base_fields)
        self.assertNotIn('contact_number', CourtForm.base_fields)
        self.assertNotIn('email', CourtForm.base_fields)
        self.assertNotIn('operating_hours', CourtForm.base_fields)
        self.assertTrue({
            'has_lighting',
            'has_parking',
            'has_restrooms',
            'has_equipment_rental',
            'has_water_fountain',
            'has_seating',
            'is_wheelchair_accessible',
        }.isdisjoint(CourtForm.base_fields))
        self.assertFalse(CourtForm.base_fields['website'].required)

    def test_selected_review_topics_and_optional_custom_review_are_saved(self):
        self.client.force_login(self.player)

        response = self.client.post(
            reverse('court_create'),
            self.court_data(
                review_topics=[
                    Court.ReviewTopic.COURT_QUALITY,
                    Court.ReviewTopic.AFFORDABILITY,
                ],
                overall_rating='8',
                description='A welcoming place to play.',
            ),
        )

        self.assertEqual(response.status_code, 302)
        court = Court.objects.get(name='Community Pickleball Courts')
        self.assertEqual(
            court.review_topics,
            [
                Court.ReviewTopic.COURT_QUALITY,
                Court.ReviewTopic.AFFORDABILITY,
            ],
        )
        self.assertEqual(court.overall_rating, 8)
        self.assertEqual(
            court.get_review_topic_labels(),
            ['Court Quality', 'Affordability'],
        )
        self.assertEqual(court.description, 'A welcoming place to play.')

        detail_response = self.client.get(
            reverse('court_detail', kwargs={'pk': court.pk})
        )
        self.assertContains(detail_response, 'Court Quality')
        self.assertContains(detail_response, 'Affordability')
        self.assertContains(detail_response, '8 / 10')
        self.assertContains(detail_response, 'A welcoming place to play.')

    def test_overall_experience_rating_is_limited_to_one_through_ten(self):
        for rating, valid in (('1', True), ('10', True), ('0', False), ('11', False)):
            with self.subTest(rating=rating):
                form = CourtForm(data=self.court_data(overall_rating=rating))
                self.assertEqual(form.is_valid(), valid)

    def test_duplicate_court_name_and_address_is_rejected_case_insensitively(self):
        self.client.force_login(self.player)
        Court.objects.create(
            name='Community Pickleball Courts',
            address='123 Cebu Road',
            created_by=self.player,
        )

        response = self.client.post(
            reverse('court_create'),
            self.court_data(
                name='community pickleball courts',
                address='123 cebu road',
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A court with this name and address already exists.')
        self.assertEqual(Court.objects.count(), 1)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Court.objects.create(
                    name='community pickleball courts',
                    address='123 cebu road',
                    created_by=self.player,
                )

    def test_surface_choices_are_limited_to_silica_sand_or_not(self):
        choices = set(CourtForm.base_fields['surface_type'].choices)
        self.assertEqual(
            choices,
            {
                (Court.SurfaceType.SILICA_SAND, 'Silica Sand'),
                (Court.SurfaceType.NOT_SILICA_SAND, 'Not Silica Sand'),
            },
        )

    def test_system_admin_can_edit_another_users_court(self):
        court = Court.objects.create(
            name='Community Pickleball Courts',
            address='123 Cebu Road',
            created_by=self.player,
            has_lighting=True,
            operating_hours='Daily, 7 AM–9 PM',
        )
        admin_user = CustomUser.objects.create_user(
            username='system-admin',
            password='test-password',
            role=CustomUser.Role.SYSTEM_ADMIN,
        )
        self.client.force_login(admin_user)

        response = self.client.get(reverse('court_edit', kwargs={'pk': court.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Court Name')
        self.assertContains(response, 'Review')
        self.assertNotContains(response, 'Description')
        self.assertContains(response, 'Court Type')
        self.assertContains(response, 'Website / Social Media Link')
        self.assertNotContains(response, 'Facility')
        self.assertNotContains(response, 'Contact email')
        self.assertNotContains(response, 'Phone')
        self.assertNotContains(response, 'Amenities')
        self.assertNotContains(response, 'Operating Hours')
        self.assertTrue({
            'has_lighting',
            'has_parking',
            'has_restrooms',
            'has_equipment_rental',
            'has_water_fountain',
            'has_seating',
            'is_wheelchair_accessible',
        }.isdisjoint(CourtForm.base_fields))

        edit_response = self.client.post(
            reverse('court_edit', kwargs={'pk': court.pk}),
            self.court_data(name='Updated Court Name'),
        )
        self.assertEqual(edit_response.status_code, 302)
        court.refresh_from_db()
        self.assertTrue(court.has_lighting)
        self.assertEqual(court.operating_hours, 'Daily, 7 AM–9 PM')
