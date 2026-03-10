
# DX_APP/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone 
from datetime import timedelta
import json
import pickle
import os

# ...existing code...

# Import your forms
from .forms import CropForm, UserRegistrationForm

# Note: If you don't have these models, comment them out or create them
# from .models import CropPrice, MarketNews, PriceAlert, DemandForecast
from .forms import CropForm

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
    ],
}

crop_plans_mr = {
    'rice': [
        {'week': 1, 'task': 'शेती तयार करा आणि खत घाला', 'medicine': 'बुरशी औषध', 'precaution': 'पाणी ठेवा', 'icon': '🌱', 'tip': 'स्वच्छ पाणी वापरा'},
        {'week': 2, 'task': 'रोपे लावा', 'medicine': 'काही नाही', 'precaution': 'शेत कोरडे होऊ देऊ नका', 'icon': '🌾', 'tip': 'सावकाश लावा'},
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
def login_view(request):
    lang = request.GET.get('lang', 'en')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('home')
        messages.error(request, 'Invalid username or password')
    else:
        form = AuthenticationForm()
    
    return render(request, 'DX_APP/login.html', {'form': form, 'lang': lang})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def register_view(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/register.html', {'lang': lang})

def password_reset_view(request):
    lang = request.GET.get('lang', 'en')
    return render(request, 'DX_APP/password_reset.html', {'lang': lang})

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
# COMPONENT VIEWS (REMOVE DUPLICATE home FUNCTION)
# ======================================================
def base(request):
    return render(request, 'DX_APP/base.html')

def header(request):
    return render(request, 'DX_APP/header.html')

def footer(request):
    return render(request, 'DX_APP/footer.html')

# In DX_APP/views.py
def pricing(request):
    lang = request.GET.get('lang', 'en')
    
    # Pricing plans data
    pricing_plans = [
        {
            'name': 'Free',
            'name_hi': 'मुफ्त',
            'name_mr': 'मोफत',
            'price': '₹0',
            'period': '/month',
            'period_hi': '/महीना',
            'period_mr': '/महिना',
            'features': [
                'Basic crop recommendations',
                'Soil analysis (3 tests/month)',
                'Basic weather data',
                'Community support',
                'Email support',
                '5 crops in database'
            ],
            'features_hi': [
                'मूल फसल सिफारिशें',
                'मिट्टी विश्लेषण (3 परीक्षण/महीना)',
                'मूल मौसम डेटा',
                'समुदाय समर्थन',
                'ईमेल समर्थन',
                'डेटाबेस में 5 फसलें'
            ],
            'features_mr': [
                'मूल पीक शिफारसी',
                'माती विश्लेषण (3 चाचणी/महिना)',
                'मूल हवामान डेटा',
                'समुदाय आधार',
                'ईमेल आधार',
                'डेटाबेसमध्ये 5 पिके'
            ],
            'button_text': 'Get Started',
            'button_text_hi': 'शुरू करें',
            'button_text_mr': 'सुरू करा',
            'popular': False,
            'color': 'secondary'
        },
        {
            'name': 'Pro Farmer',
            'name_hi': 'प्रो किसान',
            'name_mr': 'प्रो शेतकरी',
            'price': '₹499',
            'period': '/month',
            'period_hi': '/महीना',
            'period_mr': '/महिना',
            'features': [
                'Advanced crop recommendations',
                'Unlimited soil analysis',
                'Detailed weather forecasts',
                'Disease prediction alerts',
                'Priority email support',
                '50+ crops in database',
                'Weekly farm planning',
                'Market price trends'
            ],
            'features_hi': [
                'उन्नत फसल सिफारिशें',
                'असीमित मिट्टी विश्लेषण',
                'विस्तृत मौसम पूर्वानुमान',
                'रोग पूर्वानुमान अलर्ट',
                'प्राथमिकता ईमेल समर्थन',
                'डेटाबेस में 50+ फसलें',
                'साप्ताहिक फार्म योजना',
                'बाजार मूल्य रुझान'
            ],
            'features_mr': [
                'प्रगत पीक शिफारसी',
                'अमर्यादित माती विश्लेषण',
                'तपशीलवार हवामान अंदाज',
                'रोग अंदाज सूचना',
                'प्राधान्य ईमेल आधार',
                'डेटाबेसमध्ये 50+ पिके',
                'साप्ताहिक शेत योजना',
                'बाजार किंमत कल'
            ],
            'button_text': 'Start Free Trial',
            'button_text_hi': 'मुफ्त ट्रायल शुरू करें',
            'button_text_mr': 'मोफत चाचणी सुरू करा',
            'popular': True,
            'color': 'success'
        },
        {
            'name': 'Enterprise',
            'name_hi': 'एंटरप्राइज',
            'name_mr': 'एंटरप्राइज',
            'price': 'Custom',
            'period': '',
            'period_hi': '',
            'period_mr': '',
            'features': [
                'Everything in Pro Farmer',
                'API access',
                'Custom AI model training',
                'Dedicated support manager',
                'On-site consultation',
                'Bulk farm management',
                'Advanced analytics dashboard',
                'Export/Import tools',
                'Multi-user accounts'
            ],
            'features_hi': [
                'प्रो किसान में सब कुछ',
                'एपीआई पहुंच',
                'कस्टम एआई मॉडल प्रशिक्षण',
                'समर्पित समर्थन प्रबंधक',
                'साइट पर परामर्श',
                'थोक फार्म प्रबंधन',
                'उन्नत विश्लेषण डैशबोर्ड',
                'निर्यात/आयात उपकरण',
                'बहु-उपयोगकर्ता खाते'
            ],
            'features_mr': [
                'प्रो शेतकरी मध्ये सर्व काही',
                'एपीआई प्रवेश',
                'सानुकूल एआई मॉडेल प्रशिक्षण',
                'समर्पित आधार व्यवस्थापक',
                'साइटवर सल्ला',
                'थोक शेत व्यवस्थापन',
                'प्रगत विश्लेषण डॅशबोर्ड',
                'निर्यात/आयात साधने',
                'बहु-वापरकर्ता खाती'
            ],
            'button_text': 'Contact Sales',
            'button_text_hi': 'सेल्स से संपर्क करें',
            'button_text_mr': 'विक्रीशी संपर्क साधा',
            'popular': False,
            'color': 'primary'
        }
    ]
    
    # FAQ data
    faqs = [
        {
            'question': 'Can I change plans anytime?',
            'question_hi': 'क्या मैं कभी भी प्लान बदल सकता हूं?',
            'question_mr': 'मी कोणत्याही वेळी योजना बदलू शकतो का?',
            'answer': 'Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately.'
        },
        {
            'question': 'Is there a free trial for Pro Farmer?',
            'question_hi': 'क्या प्रो किसान के लिए मुफ्त ट्रायल है?',
            'question_mr': 'प्रो शेतकरी साठी मोफत चाचणी आहे का?',
            'answer': 'Yes, we offer a 14-day free trial for the Pro Farmer plan. No credit card required.'
        },
        {
            'question': 'Do you offer discounts for bulk purchases?',
            'question_hi': 'क्या आप थोक खरीद के लिए छूट देते हैं?',
            'question_mr': 'तुम्ही थोक खरेदीसाठी सवलत देतात का?',
            'answer': 'Yes, we offer special discounts for cooperatives, farming communities, and educational institutions.'
        }
    ]
    
    # Feature comparison
    features_comparison = [
        {
            'feature': 'Crop Recommendations',
            'feature_hi': 'फसल सिफारिशें',
            'feature_mr': 'पीक शिफारसी',
            'free': '✓',
            'pro': '✓ Advanced',
            'enterprise': '✓ Custom'
        },
        {
            'feature': 'Soil Analysis',
            'feature_hi': 'मिट्टी विश्लेषण',
            'feature_mr': 'माती विश्लेषण',
            'free': '3/month',
            'pro': 'Unlimited',
            'enterprise': 'Unlimited + AI'
        },
        {
            'feature': 'Weather Forecast',
            'feature_hi': 'मौसम पूर्वानुमान',
            'feature_mr': 'हवामान अंदाज',
            'free': 'Basic',
            'pro': 'Detailed',
            'enterprise': 'Detailed + Alerts'
        },
        {
            'feature': 'Disease Prediction',
            'feature_hi': 'रोग पूर्वानुमान',
            'feature_mr': 'रोग अंदाज',
            'free': '✗',
            'pro': '✓',
            'enterprise': '✓ Advanced'
        },
        {
            'feature': 'Support',
            'feature_hi': 'समर्थन',
            'feature_mr': 'आधार',
            'free': 'Community',
            'pro': 'Priority Email',
            'enterprise': '24/7 Phone'
        },
        {
            'feature': 'Data Export',
            'feature_hi': 'डेटा निर्यात',
            'feature_mr': 'डेटा निर्यात',
            'free': '✗',
            'pro': '✓ PDF',
            'enterprise': '✓ PDF, Excel, API'
        }
    ]
    
    return render(request, 'DX_APP/pricing.html', {
        'lang': lang,
        'pricing_plans': pricing_plans,
        'faqs': faqs,
        'features_comparison': features_comparison
    })
    
# In DX_APP/views.py
def case_studies(request):
    lang = request.GET.get('lang', 'en')
    
    # Case studies data
    case_studies = [
        {
            'id': 1,
            'title': 'Rice Yield Increased by 35% in Punjab',
            'title_hi': 'पंजाब में चावल की पैदावार में 35% की वृद्धि',
            'title_mr': 'पंजाब मध्ये भात उत्पादन 35% ने वाढले',
            'location': 'Punjab, India',
            'location_hi': 'पंजाब, भारत',
            'location_mr': 'पंजाब, भारत',
            'farmer': 'Harpreet Singh',
            'duration': '6 months',
            'duration_hi': '6 महीने',
            'duration_mr': '6 महिने',
            'crop': 'Rice',
            'crop_hi': 'चावल',
            'crop_mr': 'भात',
            'challenge': 'Low yield due to improper fertilizer use and water management',
            'challenge_hi': 'अनुचित उर्वरक उपयोग और जल प्रबंधन के कारण कम उपज',
            'challenge_mr': 'अयोग्य खत वापर आणि पाणी व्यवस्थापनामुळे कमी उत्पादन',
            'solution': 'AI-based soil testing and customized fertilizer plan',
            'solution_hi': 'एआई-आधारित मिट्टी परीक्षण और अनुकूलित उर्वरक योजना',
            'solution_mr': 'एआई-आधारित माती चाचणी आणि सानुकूलित खत योजना',
            'result': '35% increase in yield, 20% reduction in water usage',
            'result_hi': '35% उपज वृद्धि, 20% पानी की खपत में कमी',
            'result_mr': '35% उत्पादन वाढ, 20% पाणी वापर कमी',
            'image': 'rice_field.jpg',
            'category': 'success',
            'icon': '🌾',
            'color': 'success'
        },
        {
            'id': 2,
            'title': 'Tomato Disease Prevention in Maharashtra',
            'title_hi': 'महाराष्ट्र में टमाटर रोग निवारण',
            'title_mr': 'महाराष्ट्रात टोमॅटो रोग प्रतिबंध',
            'location': 'Nashik, Maharashtra',
            'location_hi': 'नासिक, महाराष्ट्र',
            'location_mr': 'नाशिक, महाराष्ट्र',
            'farmer': 'Rajesh Patil',
            'duration': '3 months',
            'duration_hi': '3 महीने',
            'duration_mr': '3 महिने',
            'crop': 'Tomato',
            'crop_hi': 'टमाटर',
            'crop_mr': 'टोमॅटो',
            'challenge': 'Early blight disease affecting 40% of crop',
            'challenge_hi': '40% फसल को प्रभावित करने वाली अर्ली ब्लाइट बीमारी',
            'challenge_mr': '40% पीक प्रभावित करणारी अर्ली ब्लाइट रोग',
            'solution': 'AI disease prediction and targeted treatment plan',
            'solution_hi': 'एआई रोग पूर्वानुमान और लक्षित उपचार योजना',
            'solution_mr': 'एआई रोग अंदाज आणि लक्षित उपचार योजना',
            'result': '95% disease prevention, saved ₹2,00,000 in crop loss',
            'result_hi': '95% रोग निवारण, ₹2,00,000 फसल हानि में बचत',
            'result_mr': '95% रोग प्रतिबंध, ₹2,00,000 पीक तोटा वाचवला',
            'image': 'tomato_farm.jpg',
            'category': 'prevention',
            'icon': '🍅',
            'color': 'danger'
        },
        {
            'id': 3,
            'title': 'Water Optimization in Rajasthan Farms',
            'title_hi': 'राजस्थान के खेतों में जल अनुकूलन',
            'title_mr': 'राजस्थान शेतात पाणी ऑप्टिमायझेशन',
            'location': 'Jaipur, Rajasthan',
            'location_hi': 'जयपुर, राजस्थान',
            'location_mr': 'जयपूर, राजस्थान',
            'farmer': 'Mohan Lal',
            'duration': '1 year',
            'duration_hi': '1 वर्ष',
            'duration_mr': '1 वर्ष',
            'crop': 'Wheat',
            'crop_hi': 'गेहूं',
            'crop_mr': 'गहू',
            'challenge': 'Water scarcity and inefficient irrigation methods',
            'challenge_hi': 'पानी की कमी और अक्षम सिंचाई विधियां',
            'challenge_mr': 'पाणीची कमतरता आणि अकार्यक्षम सिंचन पद्धती',
            'solution': 'Smart irrigation system with soil moisture sensors',
            'solution_hi': 'मिट्टी की नमी सेंसर के साथ स्मार्ट सिंचाई प्रणाली',
            'solution_mr': 'माती ओलसर सेन्सरसह स्मार्ट सिंचन प्रणाली',
            'result': '40% water saving, increased yield by 25%',
            'result_hi': '40% पानी की बचत, 25% उपज वृद्धि',
            'result_mr': '40% पाणी वाचवणे, 25% उत्पादन वाढ',
            'image': 'wheat_field.jpg',
            'category': 'conservation',
            'icon': '💧',
            'color': 'info'
        },
        {
            'id': 4,
            'title': 'Organic Farming Success in Kerala',
            'title_hi': 'केरल में जैविक खेती की सफलता',
            'title_mr': 'केरळ मध्ये सेंद्रिय शेती यश',
            'location': 'Kochi, Kerala',
            'location_hi': 'कोच्चि, केरल',
            'location_mr': 'कोची, केरळ',
            'farmer': 'Sunita Nair',
            'duration': '8 months',
            'duration_hi': '8 महीने',
            'duration_mr': '8 महिने',
            'crop': 'Vegetables',
            'crop_hi': 'सब्जियां',
            'crop_mr': 'भाज्या',
            'challenge': 'Transition from chemical to organic farming',
            'challenge_hi': 'रासायनिक से जैविक खेती में संक्रमण',
            'challenge_mr': 'रासायनिक ते सेंद्रिय शेतीत संक्रमण',
            'solution': 'AI-guided organic farming plan and certification support',
            'solution_hi': 'एआई-निर्देशित जैविक खेती योजना और प्रमाणन समर्थन',
            'solution_mr': 'एआई-मार्गदर्शित सेंद्रिय शेती योजना आणि प्रमाणीकरण आधार',
            'result': 'Organic certification achieved, 30% premium price',
            'result_hi': 'जैविक प्रमाणन प्राप्त, 30% प्रीमियम मूल्य',
            'result_mr': 'सेंद्रिय प्रमाणीकरण मिळाले, 30% प्रीमियम किंमत',
            'image': 'organic_farm.jpg',
            'category': 'organic',
            'icon': '🌿',
            'color': 'success'
        },
        {
            'id': 5,
            'title': 'Multi-Crop Optimization in UP',
            'title_hi': 'यूपी में बहु-फसल अनुकूलन',
            'title_mr': 'यूपी मध्ये बहु-पीक ऑप्टिमायझेशन',
            'location': 'Lucknow, Uttar Pradesh',
            'location_hi': 'लखनऊ, उत्तर प्रदेश',
            'location_mr': 'लखनौ, उत्तर प्रदेश',
            'farmer': 'Amit Sharma',
            'duration': '2 years',
            'duration_hi': '2 वर्ष',
            'duration_mr': '2 वर्षे',
            'crop': 'Multiple Crops',
            'crop_hi': 'बहु फसलें',
            'crop_mr': 'बहु पिके',
            'challenge': 'Inefficient crop rotation and low profitability',
            'challenge_hi': 'अक्षम फसल चक्र और कम लाभप्रदता',
            'challenge_mr': 'अकार्यक्षम पीक फेर आणि कमी नफा',
            'solution': 'AI-powered crop rotation planning and market analysis',
            'solution_hi': 'एआई-संचालित फसल चक्र योजना और बाजार विश्लेषण',
            'solution_mr': 'एआई-चालित पीक फेर नियोजन आणि बाजार विश्लेषण',
            'result': 'Increased income by 45%, better soil health',
            'result_hi': 'आय में 45% वृद्धि, बेहतर मिट्टी स्वास्थ्य',
            'result_mr': 'उत्पन्न 45% ने वाढले, चांगले माती आरोग्य',
            'image': 'crop_rotation.jpg',
            'category': 'optimization',
            'icon': '🔄',
            'color': 'warning'
        },
        {
            'id': 6,
            'title': 'Cotton Farming Revolution in Gujarat',
            'title_hi': 'गुजरात में कपास खेती क्रांति',
            'title_mr': 'गुजरात मध्ये कापूस शेती क्रांती',
            'location': 'Ahmedabad, Gujarat',
            'location_hi': 'अहमदाबाद, गुजरात',
            'location_mr': 'अहमदाबाद, गुजरात',
            'farmer': 'Vikram Patel',
            'duration': '1.5 years',
            'duration_hi': '1.5 वर्ष',
            'duration_mr': '1.5 वर्षे',
            'crop': 'Cotton',
            'crop_hi': 'कपास',
            'crop_mr': 'कापूस',
            'challenge': 'Pest infestation and low-quality cotton',
            'challenge_hi': 'कीट संक्रमण और निम्न गुणवत्ता वाला कपास',
            'challenge_mr': 'कीट संसर्ग आणि कमी दर्जाचा कापूस',
            'solution': 'Integrated pest management using AI detection',
            'solution_hi': 'एआई पहचान का उपयोग कर एकीकृत कीट प्रबंधन',
            'solution_mr': 'एआई शोध वापरून एकीकृत कीट व्यवस्थापन',
            'result': 'Pest control by 90%, export quality cotton achieved',
            'result_hi': '90% कीट नियंत्रण, निर्यात गुणवत्ता कपास प्राप्त',
            'result_mr': '90% कीट नियंत्रण, निर्यात दर्जा कापूस मिळाला',
            'image': 'cotton_field.jpg',
            'category': 'innovation',
            'icon': '🧵',
            'color': 'primary'
        }
    ]
    
    # Categories for filtering
    categories = [
        {'id': 'all', 'name': 'All Cases', 'name_hi': 'सभी केस', 'name_mr': 'सर्व केस', 'count': len(case_studies)},
        {'id': 'success', 'name': 'Success Stories', 'name_hi': 'सफलता की कहानियाँ', 'name_mr': 'यशोगाथा', 'count': 2},
        {'id': 'prevention', 'name': 'Disease Prevention', 'name_hi': 'रोग निवारण', 'name_mr': 'रोग प्रतिबंध', 'count': 1},
        {'id': 'conservation', 'name': 'Water Conservation', 'name_hi': 'जल संरक्षण', 'name_mr': 'पाणी संवर्धन', 'count': 1},
        {'id': 'organic', 'name': 'Organic Farming', 'name_hi': 'जैविक खेती', 'name_mr': 'सेंद्रिय शेती', 'count': 1},
        {'id': 'optimization', 'name': 'Crop Optimization', 'name_hi': 'फसल अनुकूलन', 'name_mr': 'पीक ऑप्टिमायझेशन', 'count': 1},
        {'id': 'innovation', 'name': 'Innovation', 'name_hi': 'नवाचार', 'name_mr': 'नाविन्य', 'count': 1}
    ]
    
    # Stats for the page
    stats = [
        {
            'value': '50K+',
            'label': 'Farmers Impacted',
            'label_hi': 'प्रभावित किसान',
            'label_mr': 'प्रभावित शेतकरी'
        },
        {
            'value': '35%',
            'label': 'Avg. Yield Increase',
            'label_hi': 'औसत उपज वृद्धि',
            'label_mr': 'सरासरी उत्पादन वाढ'
        },
        {
            'value': '₹50Cr+',
            'label': 'Revenue Generated',
            'label_hi': 'राजस्व उत्पन्न',
            'label_mr': 'उत्पन्न निर्माण'
        },
        {
            'value': '25+',
            'label': 'States Covered',
            'label_hi': 'राज्य कवर',
            'label_mr': 'राज्ये समाविष्ट'
        }
    ]
    
    return render(request, 'DX_APP/case_studies.html', {
        'lang': lang,
        'case_studies': case_studies,
        'categories': categories,
        'stats': stats
    })
    
# In DX_APP/views.py - update the register_view function
from django.contrib.auth.models import User
from .forms import UserRegistrationForm

def register_view(request):
    lang = request.GET.get('lang', 'en')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Create user
                user = form.save(commit=False)
                user.email = form.cleaned_data['email']
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.save()
                
                # Store additional info in session
                request.session['user_phone'] = form.cleaned_data['phone']
                request.session['user_type'] = form.cleaned_data['user_type']
                request.session['user_location'] = form.cleaned_data['location']
                
                # Auto login
                from django.contrib.auth import authenticate, login
                username = form.cleaned_data['username']
                password = form.cleaned_data['password1']
                user = authenticate(username=username, password=password)
                
                if user is not None:
                    login(request, user)
                    messages.success(request, 'Registration successful! Welcome to CropAI.')
                    return redirect('home')
                    
            except Exception as e:
                messages.error(request, f'Registration error: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'DX_APP/register.html', {
        'form': form,
        'lang': lang
    })
    
# DX_APP/views.py - Add this function
def disease_diagnosis(request):
    lang = request.GET.get('lang', 'en')
    
    # Import the form
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


# ...existing code...

@login_required
def my_report(request):
    """Display user's crop recommendation report"""
    from .models import CropRecommendation
    
    recommendations = CropRecommendation.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-recommendation_date')
    
    context = {
        'recommendations': recommendations,
    }
    return render(request, 'reports/my_report.html', context)


@login_required
def generate_report(request, recommendation_id):
    """Generate detailed crop recommendation report"""
    lang = request.GET.get('lang', 'en')
    
    try:
        from .models import CropRecommendation
        recommendation = CropRecommendation.objects.get(
            id=recommendation_id,
            user=request.user
        )
    except:
        recommendation = None
    
    context = {
        'recommendation': recommendation,
        'lang': lang
    }
    return render(request, 'reports/generate_report.html', context)


@login_required
def view_report(request, report_id):
    """View a specific report"""
    from .models import Report
    try:
        report = Report.objects.get(id=report_id, user=request.user)
    except Report.DoesNotExist:
        return redirect('my_report')
    
    context = {
        'report': report,
    }
    return render(request, 'DX_APP/view_report.html', context)


@login_required
def download_report(request, report_id):
    """Download PDF report"""
    from django.shortcuts import get_object_or_404
    from django.http import FileResponse
    from .models import Report
    
    report = get_object_or_404(Report, id=report_id, user=request.user)
    
    if report.report_file:
        return FileResponse(report.report_file, as_attachment=True)
    else:
        # Generate report if not exists
        return redirect('generate_report', recommendation_id=report.recommendation.id)


@login_required
def create_action_plans(request, recommendation_id):
    """Create action plans for a recommendation"""
    from django.shortcuts import get_object_or_404
    from .models import CropRecommendation, ActionPlan
    
    recommendation = get_object_or_404(CropRecommendation, id=recommendation_id, user=request.user)
    
    # Check if action plans already exist
    if ActionPlan.objects.filter(recommendation=recommendation).exists():
        messages.info(request, 'Action plans already exist for this recommendation.')
        return redirect('view_report', report_id=recommendation.id)
    
    # Create action plans
    plans = [
        {
            'month': 1,
            'action': 'Prepare soil with basal fertilizer',
            'note': 'Apply potash-rich fertilizer for root development'
        },
        {
            'month': 2,
            'action': 'Sowing and initial irrigation',
            'note': 'Maintain proper spacing of 30cm between plants'
        },
        {
            'month': 3,
            'action': 'Monitor for pests and apply nutrients',
            'note': 'Watch for common pests in your region'
        }
    ]
    
    for plan in plans:
        ActionPlan.objects.create(
            recommendation=recommendation,
            month=plan['month'],
            action=plan['action'],
            ai_note=plan['note']
        )
    
    messages.success(request, 'Action plans created successfully!')
    return redirect('my_report')