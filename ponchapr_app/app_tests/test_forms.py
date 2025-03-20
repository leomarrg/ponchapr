from django.test import TestCase
from registratepr_app.forms import AttendeeForm
from registratepr_app.models import Attendee

class AttendeeFormTests(TestCase):
    
    def test_valid_form(self):
        form_data = {
            'name': 'John',
            'last_name': 'Doe',
            'phone_number': '1234567890',
            'date_of_birth': '1990-01-01',
            'email': 'john.doe@example.com',
        }
        form = AttendeeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_fields(self):
        form_data = {
            'name': 'John',
            'last_name': '',
            'phone_number': '1234567890',
            'date_of_birth': '1990-01-01',
            'email': 'john.doe@example.com',
        }
        form = AttendeeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)


    def test_duplicate_email(self):
        Attendee.objects.create(
            name='Jane',
            last_name='Doe',
            phone_number='0987654321',
            date_of_birth='1992-02-02',
            email='jane.doe@example.com'
        )
        form_data = {
            'name': 'John',
            'last_name': 'Smith',
            'phone_number': '1234567890',
            'date_of_birth': '1990-01-01',
            'email': 'jane.doe@example.com',
        }
        form = AttendeeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_phone_number(self):
        form_data = {
            'name': 'John',
            'last_name': 'Doe',
            'phone_number': 'invalid_phone',
            'date_of_birth': '1990-01-01',
            'email': 'john.doe@example.com',
        }
        form = AttendeeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone_number', form.errors)

    def test_date_input_widget(self):
        form = AttendeeForm()
        self.assertIn('type="date"', str(form['date_of_birth']))

    def test_empty_submission(self):
        form = AttendeeForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 5)  # Assuming 5 required fields

    def test_cross_field_validation(self):
        form_data = {
            'name': 'John',
            'last_name': 'Doe',
            'phone_number': '',
            'date_of_birth': '1990-01-01',
            'email': '',
        }
        form = AttendeeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)  # Cross-field errors are in '__all__'
