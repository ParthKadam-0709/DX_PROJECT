# DX_APP/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json
import pickle
import os

# Import your forms
from .forms import CropForm

# Note: If you don't have these models, comment them out or create them
# from .models import CropPrice, MarketNews, PriceAlert, DemandForecast

# ======================================================
# LOAD ML MODEL
# ======================================================
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'crop_recommendation_model.pkl')
try:
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    model = None
    print(f"Warning: Model file not found at {MODEL_PATH}")

# ======================================================
# CROP PLANS (EN / HI / MR)
# ======================================================
crop_plans_en = {
    'rice': [
        {'week': 1, 'task': 'Prepare field and add fertilizer', 'medicine': 'Fungus medicine', 'precaution': 'Keep water', 'icon': '🌱', 'tip': 'Use clean water'},
        {'week': 2, 'task': 'Transplant seedlings', 'medicine': 'None', 'precaution': 'Do not let field dry', 'icon': '🌾', 'tip': 'Plant gently'},
        {'week': 3, 'task': 'Add water', 'medicine': 'None', 'precaution': 'Check water level', 'icon': '💧', 'tip': 'Water in morning'},
        {'week': 4, 'task': 'Look for bugs', 'medicine': 'Bug spray', 'precaution': 'Check leaves', 'icon': '🐛', 'tip': 'Use spray only if needed'},
    ],
    'wheat': [
        {'week': 1, 'task': 'Sow seeds and add fertilizer', 'medicine': 'None', 'precaution': 'Keep soil moist', 'icon': '🌱', 'tip': 'Use good seeds'},
        {'week': 2, 'task': 'Add water', 'medicine': 'None', 'precaution': 'Do not flood', 'icon': '💧', 'tip': 'Water in morning'},
        {'week': 3, 'task': 'Remove weeds', 'medicine': 'Weed killer', 'precaution': 'Wear gloves', 'icon': '🌿', 'tip': 'Pull weeds by hand'},
        {'week': 4, 'task': 'Check for disease', 'medicine': 'Fungus medicine', 'precaution': 'Check leaves', 'icon': '🍂', 'tip': 'Yellow spots mean disease'},
    ],
    'maize': [
        {'week': 1, 'task': 'Plant seeds', 'medicine': 'None', 'precaution': 'Keep soil moist', 'icon': '🌽', 'tip': 'Use quality seeds'},
        {'week': 2, 'task': 'Water regularly', 'medicine': 'None', 'precaution': 'Avoid overwatering', 'icon': '💧', 'tip': 'Morning watering is best'},
        {'week': 3, 'task': 'Check for pests', 'medicine': 'Pest control', 'precaution': 'Wear protection', 'icon': '🐛', 'tip': 'Early detection helps'},
        {'week': 4, 'task': 'Add fertilizer', 'medicine': 'None', 'precaution': 'Follow instructions', 'icon': '🧪', 'tip': 'Balance nutrients'},
    ],
}

crop_plans_hi = {
    'rice': [
        {'week': 1, 'task': 'खेत तैयार करें और खाद डालें', 'medicine': 'फफूंदी दवा', 'precaution': 'पानी रखें', 'icon': '🌱', 'tip': 'साफ पानी का उपयोग करें'},
        {'week': 2, 'task': 'पौधे लगाएं', 'medicine': 'कोई नहीं', 'precaution': 'खेत सूखने न दें', 'icon': '🌾', 'tip': 'धीरे से लगाएं'},
        {'week': 3, 'task': 'पानी डालें', 'medicine': 'कोई नहीं', 'precaution': 'पानी स्तर जांचें', 'icon': '💧', 'tip': 'सुबह पानी डालें'},
        {'week': 4, 'task': 'कीट जांचें', 'medicine': 'कीटनाशक', 'precaution': 'पत्ते जांचें', 'icon': '🐛', 'tip': 'आवश्यकता होने पर छिड़कें'},
    ],
    'wheat': [
        {'week': 1, 'task': 'बीज बोएं और खाद डालें', 'medicine': 'कोई नहीं', 'precaution': 'मिट्टी नम रखें', 'icon': '🌱', 'tip': 'अच्छे बीज उपयोग करें'},
        {'week': 2, 'task': 'पानी डालें', 'medicine': 'कोई नहीं', 'precaution': 'अधिक पानी न डालें', 'icon': '💧', 'tip': 'सुबह पानी डालें'},
        {'week': 3, 'task': 'Remove weeds', 'medicine': 'Weed killer', 'precaution': 'Wear gloves', 'icon': '🌿', 'tip': 'Pull weeds by hand'},
        {'week': 4, 'task': 'Check for disease', 'medicine': 'Fungus medicine', 'precaution': 'Check leaves', 'icon': '🍂', 'tip': 'Yellow spots mean disease'},
    ],
}

crop_plans_mr = {
    'rice': [
        {'week': 1, 'task': 'शेती तयार करा आणि खत घाला', 'medicine': 'बुरशी औषध', 'precaution': 'पाणी ठेवा', 'icon': '🌱', 'tip': 'स्वच्छ पाणी वापरा'},
        {'week': 2, 'task': 'रोपे लावा', 'medicine': 'काही नाही', 'precaution': 'शेत कोरडे होऊ देऊ नका', 'icon': '🌾', 'tip': 'सावकाश लावा'},
        {'week': 3, 'task': 'पाणी घाला', 'medicine': 'काही नाही', 'precaution': 'पाणी पातळी तपासा', 'icon': '💧', 'tip': 'सकाळी पाणी द्या'},
        {'week': 4, 'task': 'कीटक तपासा', 'medicine': 'कीटकनाशक', 'precaution': 'पाने तपासा', 'icon': '🐛', 'tip': 'गरजेपुरतेच फवारणी वापरा'},
    ],
}

# ======================================================
# HOME (CROP RECOMMENDATION) - MAIN VIEW
# ======================================================
def home(request):
    lang = request.GET.get('lang', 'en')
    
    # Select crop plans based on language
    if lang == 'en':
        crop_plans = crop_plans_en
    elif lang == 'hi':
        crop_plans = crop_plans_hi
    elif lang == 'mr':
        crop_plans = crop_plans_mr
    else:
        crop_plans = crop_plans_en
    
    form = CropForm(request.POST if request.method == 'POST' else None)
    result = None
    plan = None
    
    if request.method == 'POST' and form.is_valid():
        if model:  # Check if model is loaded
            data = [
                form.cleaned_data['N'],
                form.cleaned_data['P'],
                form.cleaned_data['K'],
                form.cleaned_data['temperature'],
                form.cleaned_data['humidity'],
                form.cleaned_data['ph'],
                form.cleaned_data['rainfall'],
            ]
            try:
                prediction = model.predict([data])[0]
                result = f"Recommended Crop: {prediction}"
                plan = crop_plans.get(prediction.lower())
            except:
                result = "Error: Could not make prediction"
        else:
            result = "Error: Model not loaded"
    
    return render(request, 'DX_APP/home.html', {
        'form': form,
        'result': result,
        'plan': plan,
        'lang': lang
    })

# ======================================================
# QUICK LINKS PAGES
# ======================================================
def about(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/about.html', {'lang': lang})

def solutions(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/solutions.html', {'lang': lang})

def pricing(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/pricing.html', {'lang': lang})

def case_studies(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/case_studies.html', {'lang': lang})

# ======================================================
# RESOURCES PAGES
# ======================================================
def documentation(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/documentation.html', {'lang': lang})

def api_reference(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/api_reference.html', {'lang': lang})

def blog(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/blog.html', {'lang': lang})

def help_center(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/help_center.html', {'lang': lang})

def community(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/community.html', {'lang': lang})

# ======================================================
# AUTHENTICATION
# ======================================================
# ======================================================
# AUTHENTICATION
# ======================================================
def login_view(request):
    lang = request.GET.get('lang', 'en')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            # Use 'login' (URL name) instead of 'login_view' (function name)
            return redirect('login')  # Changed from 'login_view'

    return render(request, 'DX_APP/login.html', {'lang': lang})

def logout_view(request):
    auth_logout(request)  
    request.session.flush()
    messages.info(request, "You have been logged out.")
    # Redirect to login page - use 'login' (the name from your urls.py)
    return redirect('login')  # Changed from 'login_view' to 'login'

def register_view(request):
    lang = request.GET.get('lang', 'en')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Password match check
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')  # Changed from 'register_view'

        # Username already taken
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')  # Changed from 'register_view'

        # Email already used
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register')  # Changed from 'register_view'

        # ✅ Create and save user
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        
        # Auto login after registration
        user = authenticate(username=username, password=password)
        if user is not None:
            auth_login(request, user)
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            messages.success(request, "Account created successfully!")
            return redirect('home')

    return render(request, 'DX_APP/register.html', {'lang': lang})

# ======================================================
# MARKET INSIGHTS
# ======================================================
def market_insights(request):
    lang = request.GET.get('lang', 'en')
    
    # Sample data for market insights
    crop_prices = [
        {'name': 'Rice', 'grade': 'Grade A', 'min_price': 2200, 'max_price': 2800, 'avg_price': 2500, 
         'trend': '+3.5', 'trend_icon': 'up', 'trend_color': 'success', 'market': 'APMC Mumbai', 'updated': '2 hours ago'},
        {'name': 'Wheat', 'grade': 'Sharbati', 'min_price': 2400, 'max_price': 2600, 'avg_price': 2500, 
         'trend': '-1.2', 'trend_icon': 'down', 'trend_color': 'danger', 'market': 'APMC Pune', 'updated': '1 hour ago'},
        {'name': 'Maize', 'grade': 'Feed Grade', 'min_price': 1800, 'max_price': 2200, 'avg_price': 2000, 
         'trend': '+2.8', 'trend_icon': 'up', 'trend_color': 'success', 'market': 'APMC Nagpur', 'updated': '3 hours ago'},
    ]
    
    demand_forecast = [
        {'crop': 'Rice', 'period': 'Next 30 days', 'demand_level': 'High', 'level_color': 'success', 'change': '+12'},
        {'crop': 'Wheat', 'period': 'Next 45 days', 'demand_level': 'Medium', 'level_color': 'warning', 'change': '+5'},
        {'crop': 'Vegetables', 'period': 'Next 15 days', 'demand_level': 'Very High', 'level_color': 'success', 'change': '+25'},
    ]
    
    price_alerts = [
        {'crop': 'Rice', 'message': 'Price crossed ₹2600 mark', 'priority': 'High', 'priority_color': 'danger', 'time': '10 min ago'},
        {'crop': 'Cotton', 'message': 'Price drop alert triggered', 'priority': 'Medium', 'priority_color': 'warning', 'time': '1 hour ago'},
    ]
    
    top_gainers = [
        {'crop': 'Tomato', 'change': '+12.5'},
        {'crop': 'Onion', 'change': '+8.3'},
        {'crop': 'Potato', 'change': '+6.7'},
    ]
    
    top_losers = [
        {'crop': 'Wheat', 'change': '-3.2'},
        {'crop': 'Maize', 'change': '-2.8'},
        {'crop': 'Sugarcane', 'change': '-1.5'},
    ]
    
    market_news = [
        {'title': 'Government increases MSP for Kharif crops', 'summary': 'Minimum support price increased by 5-7%', 'category': 'Policy', 'category_color': 'info', 'time': '2 hours ago'},
        {'title': 'Heavy rainfall affects vegetable supply', 'summary': 'Prices expected to rise due to supply chain', 'category': 'Weather', 'category_color': 'warning', 'time': '4 hours ago'},
        {'title': 'Export demand increases for basmati rice', 'summary': 'International demand pushes prices up', 'category': 'Export', 'category_color': 'success', 'time': '6 hours ago'},
    ]
    
    return render(request, 'DX_APP/market_insights.html', {
        'lang': lang,
        'crop_prices': crop_prices,
        'demand_forecast': demand_forecast,
        'price_alerts': price_alerts,
        'top_gainers': top_gainers,
        'top_losers': top_losers,
        'market_news': market_news,
    })

# ======================================================
# COMPONENT VIEWS
# ======================================================
def base(request):
    return render(request, 'DX_APP/base.html')

def header(request):
    return render(request, 'DX_APP/header.html')

def footer(request):
    return render(request, 'DX_APP/footer.html')

# ======================================================
# DISEASE DIAGNOSIS
# ======================================================
def disease_diagnosis(request):
    lang = request.GET.get('lang', 'en')
    
    # Import the form locally to avoid circular imports
    from .forms import DiseaseDiagnosisForm
    
    diagnosis_result = None
    treatment_plan = None
    
    if request.method == 'POST':
        form = DiseaseDiagnosisForm(request.POST, request.FILES)
        if form.is_valid():
            # Get form data
            crop_type = form.cleaned_data['crop_type']
            symptoms = form.cleaned_data['symptoms']
            plant_part = form.cleaned_data['plant_part']
            severity = form.cleaned_data['severity']
            weather = form.cleaned_data['weather_conditions']
            
            # Sample disease database (in real app, use ML model)
            disease_database = {
                'rice': {
                    'yellow_leaves': {
                        'disease': 'Rice Blast',
                        'confidence': 85,
                        'description': 'Fungal disease causing spindle-shaped spots on leaves',
                        'causes': 'High humidity and temperature between 25-30°C',
                        'treatment': 'Apply fungicides like Tricyclazole or Azoxystrobin'
                    },
                    'brown_spots': {
                        'disease': 'Brown Spot',
                        'confidence': 78,
                        'description': 'Circular brown spots with yellow halo',
                        'causes': 'Poor soil nutrition and warm humid conditions',
                        'treatment': 'Improve soil nutrition, apply Mancozeb'
                    }
                },
                'wheat': {
                    'yellow_rust': {
                        'disease': 'Yellow Rust',
                        'confidence': 92,
                        'description': 'Yellow-orange pustules on leaves',
                        'causes': 'Cool temperatures (10-15°C) with high humidity',
                        'treatment': 'Use resistant varieties, apply Propiconazole'
                    },
                    'powdery_mildew': {
                        'disease': 'Powdery Mildew',
                        'confidence': 87,
                        'description': 'White powdery growth on leaves and stems',
                        'causes': 'Moderate temperatures with high humidity',
                        'treatment': 'Apply Sulfur-based fungicides, improve air circulation'
                    }
                },
                'tomato': {
                    'late_blight': {
                        'disease': 'Late Blight',
                        'confidence': 90,
                        'description': 'Water-soaked lesions on leaves and fruits',
                        'causes': 'Cool wet conditions, Phytophthora infestans fungus',
                        'treatment': 'Remove infected plants, apply Copper fungicides'
                    },
                    'early_blight': {
                        'disease': 'Early Blight',
                        'confidence': 82,
                        'description': 'Target-like spots with concentric rings',
                        'causes': 'Alternaria fungus, warm humid weather',
                        'treatment': 'Apply Chlorothalonil, practice crop rotation'
                    }
                }
            }
            
            # Simple symptom matching (in real app, use NLP/ML)
            symptoms_lower = symptoms.lower()
            possible_diseases = []
            
            # Check crop type in database
            if crop_type in disease_database:
                for symptom_key, disease_info in disease_database[crop_type].items():
                    if symptom_key in symptoms_lower:
                        possible_diseases.append(disease_info)
            
            # If no match found, provide general diagnosis
            if not possible_diseases:
                diagnosis_result = {
                    'disease': 'General Plant Stress',
                    'confidence': 65,
                    'description': f'Based on your description of "{symptoms[:50]}...", your {crop_type} plant shows signs of stress.',
                    'causes': f'Could be due to {weather if weather else "environmental factors"}, nutrient deficiency, or improper care.',
                    'treatment': 'Improve plant care, ensure proper watering, and monitor for changes.'
                }
            else:
                # Get the most likely disease (highest confidence)
                diagnosis_result = max(possible_diseases, key=lambda x: x['confidence'])
            
            # Generate treatment plan based on severity
            treatment_plan = generate_treatment_plan(diagnosis_result, severity, crop_type, lang)
            
            messages.success(request, 'Disease diagnosis completed successfully!')
    else:
        form = DiseaseDiagnosisForm()
    
    # Common diseases for quick selection
    common_diseases = [
        {
            'name': 'Rice Blast',
            'crop': 'Rice',
            'symptoms': 'Spindle-shaped spots on leaves',
            'icon': '🌾',
            'color': 'danger'
        },
        {
            'name': 'Yellow Rust',
            'crop': 'Wheat',
            'symptoms': 'Yellow-orange pustules',
            'icon': '🌾',
            'color': 'warning'
        },
        {
            'name': 'Late Blight',
            'crop': 'Tomato',
            'symptoms': 'Water-soaked lesions',
            'icon': '🍅',
            'color': 'danger'
        },
        {
            'name': 'Powdery Mildew',
            'crop': 'Multiple',
            'symptoms': 'White powdery growth',
            'icon': '🍃',
            'color': 'info'
        }
    ]
    
    return render(request, 'DX_APP/disease_diagnosis.html', {
        'form': form,
        'lang': lang,
        'diagnosis_result': diagnosis_result,
        'treatment_plan': treatment_plan,
        'common_diseases': common_diseases
    })

def generate_treatment_plan(diagnosis, severity, crop_type, lang):
    """Generate a treatment plan based on diagnosis and severity"""
    
    severity_multiplier = {
        'low': 1,
        'medium': 1.5,
        'high': 2,
        'severe': 3
    }
    
    multiplier = severity_multiplier.get(severity, 1)
    
    treatment_plan = {
        'immediate': [],
        'short_term': [],
        'long_term': []
    }
    
    # Immediate actions (within 24 hours)
    if diagnosis['disease'] == 'General Plant Stress':
        treatment_plan['immediate'].append('Remove severely affected leaves/plants')
        treatment_plan['immediate'].append(f'Apply recommended fungicide: {diagnosis.get("treatment", "General plant tonic")}')
    else:
        treatment_plan['immediate'].append(f'Apply {diagnosis["treatment"]}')
        treatment_plan['immediate'].append('Isolate affected plants if possible')
    
    # Short-term actions (within 1 week)
    treatment_plan['short_term'].append(f'Monitor plant response for {int(7 * multiplier)} days')
    treatment_plan['short_term'].append(f'Reapply treatment if needed after {int(5 * multiplier)} days')
    treatment_plan['short_term'].append('Adjust watering schedule based on weather')
    
    # Long-term prevention
    treatment_plan['long_term'].append('Practice crop rotation next season')
    treatment_plan['long_term'].append('Use disease-resistant varieties')
    treatment_plan['long_term'].append('Maintain proper plant spacing for air circulation')
    treatment_plan['long_term'].append('Regular soil testing and fertilization')
    
    return treatment_plan

# ======================================================
# API ENDPOINTS FOR FRONTEND
# ======================================================
def get_current_user(request):
    """API endpoint to get current user info for JavaScript"""
    if request.user.is_authenticated:
        user_info = {
            'isLoggedIn': True,
            'name': request.user.first_name or request.user.username,
            'username': request.user.username,
            'email': request.user.email,
        }
        return JsonResponse(user_info)
    else:
        return JsonResponse({'isLoggedIn': False})



    