
"""
train_model.py
Trains a RandomForest model on dummy data and saves it to DX_APP/crop_recommendation_model.pkl
"""
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import pickle

# Use dummy data for model training
from django import forms

df = pd.read_csv('ml/Crop_recommendation.csv')
print(df.head())

class CropForm(forms.Form):
    N = forms.FloatField(label='Nitrogen', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nitrogen'}))
    P = forms.FloatField(label='Phosphorus', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Phosphorus'}))
    K = forms.FloatField(label='Potassium', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Potassium'}))
    temperature = forms.FloatField(label='Temperature (°C)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Temperature (°C)'}))
    humidity = forms.FloatField(label='Humidity (%)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Humidity (%)'}))
    ph = forms.FloatField(label='pH', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'pH'}))
    rainfall = forms.FloatField(label='Rainfall (mm)', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Rainfall (mm)'}))

df = pd.DataFrame(data)

X = df[['N', 'P', 'K', 'temperature', 'humidity', 'ph', 'rainfall']]
y = df['label']

model = RandomForestClassifier()
model.fit(X, y)

# Save the model to DX_APP directory using absolute path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(project_root, 'DX_APP', 'crop_recommendation_model.pkl')
with open(model_path, 'wb') as f:
    pickle.dump(model, f)

print(f'Model trained and saved as crop_recommendation_model.pkl in DX_APP directory: {model_path}')