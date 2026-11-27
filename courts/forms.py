from django import forms
from .models import Court, CourtReport, CourtReview


class CourtForm(forms.ModelForm):
    """Form for creating and editing court listings."""

    review_topics = forms.MultipleChoiceField(
        choices=Court.ReviewTopic.choices,
        required=False,
        label='Review topics',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = Court
        fields = [
            'name', 'description', 'review_topics', 'overall_rating',
            'facility_type', 'surface_type', 'number_of_courts', 'address',
            'website', 'rental_price',
            'photo',
        ]
        labels = {
            'name': 'Court Name',
            'description': 'Additional Review (optional)',
            'overall_rating': 'Overall Experience',
            'facility_type': 'Court Type',
            'website': 'Website / Social Media Link',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Court name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add details not covered by the topics above...'}),
            'facility_type': forms.Select(attrs={'class': 'form-select'}),
            'surface_type': forms.Select(attrs={'class': 'form-select'}),
            'number_of_courts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Street address in Cebu'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://website-or-social-page...'}),
            'overall_rating': forms.Select(attrs={'class': 'form-select'}),
            'rental_price': forms.TextInput(attrs={
                'class': 'form-control',
                'inputmode': 'decimal',
                'placeholder': 'e.g. 150',
            }),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        address = cleaned_data.get('address')
        if name and address:
            duplicates = Court.objects.filter(
                name__iexact=name,
                address__iexact=address,
            )
            if self.instance.pk:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                self.add_error('name', 'A court with this name and address already exists.')
        return cleaned_data


class CourtSearchForm(forms.Form):
    """Form for searching and filtering courts."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by court name or address in Cebu...',
        }),
    )
    facility_type = forms.ChoiceField(
        required=False,
        choices=[('', 'All Court Types')] + [
            choice for choice in Court.FacilityType.choices
            if choice[0] != Court.FacilityType.BOTH
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    surface_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Surface')] + list(Court.SurfaceType.choices),
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
    min_rating = forms.ChoiceField(
        required=False,
        choices=[('', 'Any Rating')] + [
            (str(rating), f'{rating}+ / 10')
            for rating in range(1, 11)
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    review_topics = forms.MultipleChoiceField(
        required=False,
        choices=Court.ReviewTopic.choices,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )


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


class CourtReviewForm(forms.ModelForm):
    """Form for submitting a rating for a court."""

    class Meta:
        model = CourtReview
        fields = ['rating', 'comment']
        labels = {
            'rating': 'Your Rating',
            'comment': 'Optional Comment',
        }
        widgets = {
            'rating': forms.Select(
                choices=[('', 'Choose a rating')] + [
                    (i, str(i))
                    for i in range(1, 11)
                ],
                attrs={'class': 'form-select'},
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Share an optional comment about your experience...',
            }),
        }
