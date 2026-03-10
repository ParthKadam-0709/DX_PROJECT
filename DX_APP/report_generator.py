from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
from django.conf import settings
from io import BytesIO
from django.core.files import File

class CropReportGenerator:
    def __init__(self, user, recommendation):
        self.user = user
        self.recommendation = recommendation
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=30,
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#1B5E20'),
            spaceAfter=12,
            spaceBefore=20,
        ))
    
    def generate_report(self):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        story = []
        
        # Header
        story.append(Paragraph("🌾 Your Personalized Crop Advisory Report", self.styles['CustomTitle']))
        story.append(Paragraph(f"Prepared for: {self.user.get_full_name() or self.user.username}", self.styles['Normal']))
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        # 1. Input Snapshot
        story.append(Paragraph("1. Your Input Snapshot", self.styles['SectionHeader']))
        
        soil_data = self.recommendation.soil_data
        profile = UserProfile.objects.get(user=self.user)
        
        data = [
            ['Parameter', 'Your Value', 'Status'],
            ['Soil Type', profile.get_soil_type_display(), '✓ Good'],
            ['Nitrogen (N)', f"{soil_data.nitrogen} kg/ha", self.get_status(soil_data.nitrogen, 'n')],
            ['Phosphorus (P)', f"{soil_data.phosphorus} kg/ha", self.get_status(soil_data.phosphorus, 'p')],
            ['Potassium (K)', f"{soil_data.potassium} kg/ha", self.get_status(soil_data.potassium, 'k')],
            ['pH Level', str(soil_data.ph_level), self.get_ph_status(soil_data.ph_level)],
            ['Rainfall', f"{soil_data.rainfall} mm", '✓ Recorded'],
            ['Location', profile.location, '✓ Set'],
        ]
        
        table = Table(data, colWidths=[120, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 20))
        
        # 2. Recommendations
        story.append(Paragraph("2. Top Crop Recommendations", self.styles['SectionHeader']))
        
        rec_data = [
            ['Rank', 'Crop', 'Expected Yield', 'Risk Factor'],
            ['🥇 Top Pick', self.recommendation.crop_name, 
             self.recommendation.expected_yield, self.recommendation.risk_factor],
        ]
        
        rec_table = Table(rec_data, colWidths=[80, 120, 120, 100])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFA000')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#FFF3E0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        story.append(rec_table)
        story.append(Spacer(1, 20))
        
        # 3. Action Plan
        story.append(Paragraph("3. Recommended Action Plan", self.styles['SectionHeader']))
        
        actions = ActionPlan.objects.filter(recommendation=self.recommendation)
        
        for action in actions:
            action_text = f"<b>Month {action.month}:</b> {action.action}"
            story.append(Paragraph(action_text, self.styles['Normal']))
            story.append(Paragraph(f"💡 <i>{action.ai_note}</i>", self.styles['Italic']))
            story.append(Spacer(1, 10))
        
        # 4. Summary
        story.append(Paragraph("4. Summary & Insights", self.styles['SectionHeader']))
        
        summary = f"""
        <para>
        <b>Efficiency Score:</b> {self.recommendation.confidence_score}% efficient for {self.recommendation.crop_name}<br/><br/>
        <b>Sustainability Tip:</b> Based on your soil analysis, consider crop rotation to maintain soil health.<br/><br/>
        <b>Next Steps:</b> Prepare your field according to Month 1 actions above.
        </para>
        """
        story.append(Paragraph(summary, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def get_status(self, value, nutrient):
        # Simplified status logic
        if nutrient == 'n':
            return 'Optimal' if 250 <= value <= 350 else 'Adjust Needed'
        elif nutrient == 'p':
            return 'Optimal' if 50 <= value <= 70 else 'Adjust Needed'
        elif nutrient == 'k':
            return 'Optimal' if 200 <= value <= 300 else 'Adjust Needed'
        return 'Unknown'
    
    def get_ph_status(self, ph):
        return 'Optimal' if 6.0 <= ph <= 7.5 else 'Adjust Needed'