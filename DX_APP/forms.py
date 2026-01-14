# DX_APP/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CropForm(forms.Form):
    N = forms.FloatField(label='Nitrogen', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nitrogen'}))
    P = forms.FloatField(label='Phosphorus', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Phosphorus'}))
    K = forms.FloatField(label='Potassium', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Potassium'}))
    temperature = forms.FloatField(label='Temperature (°C)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Temperature (°C)'}))
    humidity = forms.FloatField(label='Humidity (%)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Humidity (%)'}))
    ph = forms.FloatField(label='pH', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'pH'}))
    rainfall = forms.FloatField(label='Rainfall (mm)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rainfall (mm)'}))

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your last name'
        })
    )
    
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    
    user_type = forms.ChoiceField(
        choices=[
            ('farmer', 'Farmer'),
            ('buyer', 'Buyer'),
            ('expert', 'Agriculture Expert'),
            ('other', 'Other')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    location = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your city/state'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 
                 'user_type', 'location', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to all fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email

# ADD THIS FORM CLASS AT THE TOP LEVEL (same indentation as other form classes)
class DiseaseDiagnosisForm(forms.Form):
    CROP_CHOICES = [
        ('rice', 'Rice'),
        ('wheat', 'Wheat'),
        ('maize', 'Maize'),
        ('tomato', 'Tomato'),
        ('potato', 'Potato'),
        ('cotton', 'Cotton'),
        ('sugarcane', 'Sugarcane'),
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('other', 'Other')
    ]
    
    crop_type = forms.ChoiceField(
        choices=CROP_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Select crop type'
        }),
        label='Crop Type'
    )
    
    symptoms = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe the symptoms you observed (e.g., yellow leaves, spots, wilting)',
            'rows': 4
        }),
        label='Symptoms Description'
    )
    
    leaf_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        label='Upload Leaf Image (Optional)'
    )
    
    plant_part = forms.ChoiceField(
        choices=[
            ('leaf', 'Leaf'),
            ('stem', 'Stem'),
            ('fruit', 'Fruit'),
            ('root', 'Root'),
            ('flower', 'Flower'),
            ('whole_plant', 'Whole Plant')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Affected Plant Part'
    )
    
    severity = forms.ChoiceField(
        choices=[
            ('low', 'Low (less than 10%)'),
            ('medium', 'Medium (10-30%)'),
            ('high', 'High (30-60%)'),
            ('severe', 'Severe (more than 60%)')
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Disease Severity'
    )
    
    weather_conditions = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., humid, rainy, dry'
        }),
        label='Recent Weather Conditions'
    )