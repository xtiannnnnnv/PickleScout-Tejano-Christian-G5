from django import forms
from .models import Court, CourtReport


class CourtForm(forms.ModelForm):
    """Form for creating and editing court listings."""

    class Meta:
        model = Court
        fields = [
            'name', 'description', 'facility_type', 'surface_type',
            'number_of_courts', 'address', 'city', 'province_state',
            'zip_code', 'latitude', 'longitude', 'contact_number',
            'email', 'website', 'operating_hours', 'rental_price',
            'has_lighting', 'has_parking', 'has_restrooms',
            'has_equipment_rental', 'has_water_fountain', 'has_seating',
            'is_wheelchair_accessible', 'photo',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Facility name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the facility...'}),
            'facility_type': forms.Select(attrs={'class': 'form-select'}),
            'surface_type': forms.Select(attrs={'class': 'form-select'}),
            'number_of_courts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'province_state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Province / State'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP code'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Latitude', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Longitude', 'step': '0.000001'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Contact email'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'operating_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mon–Fri 6 AM – 10 PM'}),
            'rental_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price per hour', 'step': '0.01'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CourtSearchForm(forms.Form):
    """Form for searching and filtering courts."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name or location...',
        }),
    )
    facility_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Types')] + list(Court.FacilityType.choices),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Max price / hr',
            'step': '50',
        }),
    )
    has_lighting = forms.BooleanField(required=False, label='Lighting')
    has_parking = forms.BooleanField(required=False, label='Parking')
    has_restrooms = forms.BooleanField(required=False, label='Restrooms')
    has_equipment_rental = forms.BooleanField(required=False, label='Equipment Rental')


class CourtReportForm(forms.ModelForm):
    """Form for reporting inaccurate court information."""

    class Meta:
        model = CourtReport
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what information is inaccurate or outdated...',
            }),
        }
