from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, FileResponse
from urllib3 import request
from .models import CropRecommendation, SoilData, UserProfile, ActionPlan
from .utils.report_generator import CropReportGenerator
from .forms import ImageUploadForm
from ml.predict import predict_disease
import os
import json

@login_required
def user_report(request, recommendation_id):
    """Generate and display user report"""
    recommendation = get_object_or_404(CropRecommendation, 
                                       id=recommendation_id, 
                                       user=request.user)
    
    context = {
        'recommendation': recommendation,
        'soil_data': recommendation.soil_data,
        'actions': ActionPlan.objects.filter(recommendation=recommendation),
    }
    return render(request, 'reports/user_report.html', context)

@login_required
def download_report(request, recommendation_id):
    """Download PDF report"""
    recommendation = get_object_or_404(CropRecommendation, 
                                       id=recommendation_id, 
                                       user=request.user)
    
    generator = CropReportGenerator(request.user, recommendation)
    pdf_buffer = generator.generate_report()
    
    filename = f"crop_report_{request.user.username}_{recommendation.crop_name}.pdf"
    return FileResponse(pdf_buffer, 
                        as_attachment=True, 
                        filename=filename,
                        content_type='application/pdf')

@login_required
def recommendations_list(request):
    """List all user recommendations"""
    recommendations = CropRecommendation.objects.filter(
        user=request.user, 
        is_active=True
    ).order_by('-recommendation_date')
    
    return render(request, 'reports/recommendations_list.html', {
        'recommendations': recommendations
    })

@login_required
def generate_new_recommendation(request):
    """Generate new recommendation based on latest soil data"""
    if request.method == 'POST':
        # Get latest soil data
        latest_soil = SoilData.objects.filter(user=request.user).latest('date_created')
        
        # AI logic to determine best crop (simplified example)
        crop_recommendation = determine_best_crop(latest_soil)
        
        # Create recommendation
        recommendation = CropRecommendation.objects.create(
            user=request.user,
            soil_data=latest_soil,
            crop_name=crop_recommendation['name'],
            confidence_score=crop_recommendation['confidence'],
            expected_yield=crop_recommendation['yield'],
            risk_factor=crop_recommendation['risk']
        )
        
        # Create action plans
        create_action_plans(recommendation)
        
        return redirect('user_report', recommendation_id=recommendation.id)
    
    return render(request, 'reports/generate_recommendation.html')

def determine_best_crop(soil_data):
    """Simplified AI logic for crop recommendation"""
    # This is where your actual AI/ML model would be implemented
    if soil_data.ph_level > 7.0:
        return {
            'name': 'Cotton',
            'confidence': 85,
            'yield': 'High',
            'risk': 'Low'
        }
    else:
        return {
            'name': 'Groundnut',
            'confidence': 78,
            'yield': 'Medium',
            'risk': 'Low'
        }

def create_action_plans(recommendation):
    """Create action plans for the recommendation"""
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
        
        def disease_diagnosis(request):

            result = None

    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            img = request.FILES['image']

            path = "media/" + img.name

            with open(path, 'wb+') as f:
                for chunk in img.chunks():
                    f.write(chunk)

            result = predict_disease(path)

    else:
        form = ImageUploadForm()

    return render(request, "disease_diagnosis.html",
                  {"form": form, "result": result})