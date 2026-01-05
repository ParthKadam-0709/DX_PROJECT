from django import forms

class CropForm(forms.Form):
    N = forms.FloatField(label='Nitrogen', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nitrogen'}))
    P = forms.FloatField(label='Phosphorus', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Phosphorus'}))
    K = forms.FloatField(label='Potassium', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Potassium'}))
    temperature = forms.FloatField(label='Temperature (°C)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Temperature (°C)'}))
    humidity = forms.FloatField(label='Humidity (%)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Humidity (%)'}))
    ph = forms.FloatField(label='pH', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'pH'}))
    rainfall = forms.FloatField(label='Rainfall (mm)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rainfall (mm)'}))
