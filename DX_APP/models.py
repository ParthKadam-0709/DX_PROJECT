# models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timesince import timesince

class CropPrice(models.Model):
    CROP_TYPES = [
        ('rice', 'Rice'),
        ('wheat', 'Wheat'),
        ('maize', 'Maize'),
        ('cotton', 'Cotton'),
        ('sugarcane', 'Sugarcane'),
        ('pulses', 'Pulses'),
        ('vegetables', 'Vegetables'),
    ]
    
    STATES = [
        ('maharashtra', 'Maharashtra'),
        ('punjab', 'Punjab'),
        ('uttar_pradesh', 'Uttar Pradesh'),
        ('madhya_pradesh', 'Madhya Pradesh'),
        ('karnataka', 'Karnataka'),
        ('gujarat', 'Gujarat'),
    ]
    
    MARKETS = [
        ('mumbai', 'APMC Mumbai'),
        ('pune', 'APMC Pune'),
        ('nagpur', 'APMC Nagpur'),
        ('nashik', 'APMC Nashik'),
        ('aurangabad', 'APMC Aurangabad'),
    ]
    
    name = models.CharField(max_length=100)
    crop_type = models.CharField(max_length=20, choices=CROP_TYPES)
    grade = models.CharField(max_length=50, default='Grade A')
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='quintal')
    trend_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    state = models.CharField(max_length=20, choices=STATES)
    market_name = models.CharField(max_length=20, choices=MARKETS)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def get_time_ago(self):
        return timesince(self.updated_at) + ' ago'
    
    class Meta:
        ordering = ['-updated_at']

class PriceAlert(models.Model):
    ALERT_TYPES = [
        ('above', 'Price Above'),
        ('below', 'Price Below'),
        ('change', 'Price Change %'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crop = models.CharField(max_length=100)
    target_price = models.DecimalField(max_digits=10, decimal_places=2)
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES)
    notification_method = models.JSONField(default=list)  # ['email', 'sms', 'app']
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

class MarketNews(models.Model):
    CATEGORIES = [
        ('policy', 'Policy'),
        ('weather', 'Weather'),
        ('market', 'Market'),
        ('technology', 'Technology'),
        ('export', 'Export'),
    ]
    
    title = models.CharField(max_length=200)
    summary = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES)
    source = models.CharField(max_length=100)
    published_at = models.DateTimeField()
    url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-published_at']
        verbose_name_plural = 'Market News'

class DemandForecast(models.Model):
    crop = models.CharField(max_length=100)
    period = models.CharField(max_length=50)
    demand_level = models.CharField(max_length=20)
    change_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    forecast_date = models.DateField()
    
    class Meta:
        ordering = ['forecast_date']
        
class CropRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    crop_name = models.CharField(max_length=100)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    recommendation_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    soil_data = models.JSONField(default=dict)
    weather_data = models.JSONField(default=dict)
    market_data = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-recommendation_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.crop_name}"

class SoilData(models.Model):
    recommendation = models.OneToOneField(CropRecommendation, on_delete=models.CASCADE)
    nitrogen = models.DecimalField(max_digits=5, decimal_places=2)
    phosphorus = models.DecimalField(max_digits=5, decimal_places=2)
    potassium = models.DecimalField(max_digits=5, decimal_places=2)
    temperature = models.DecimalField(max_digits=5, decimal_places=2)
    humidity = models.DecimalField(max_digits=5, decimal_places=2)
    ph = models.DecimalField(max_digits=5, decimal_places=2)
    rainfall = models.DecimalField(max_digits=5, decimal_places=2)
    
    def __str__(self):
        return f"Soil data for {self.recommendation}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    location = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    farm_size = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# In your existing models.py, add these new models at the end of the file

class ActionPlan(models.Model):
    recommendation = models.ForeignKey(CropRecommendation, on_delete=models.CASCADE, related_name='action_plans')
    month = models.IntegerField(help_text="Month number (1, 2, 3)")
    action = models.TextField()
    ai_note = models.TextField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['month']
    
    def __str__(self):
        return f"Month {self.month} plan for {self.recommendation}"

class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='crop_reports')
    recommendation = models.ForeignKey(CropRecommendation, on_delete=models.CASCADE)
    report_file = models.FileField(upload_to='user_reports/', null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_latest = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Report for {self.user.username} - {self.generated_at.date()}"