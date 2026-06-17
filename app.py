import streamlit as st
import joblib
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Student Placement Prediction",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS FOR MODERN UI ====================
st.markdown("""
    <style>
    /* Main background */
    .main {
        padding: 2rem;
    }
    
    /* Metric card styling */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2.5em;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 1em;
        opacity: 0.9;
    }
    
    /* Title styling */
    h1 {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    h2 {
        color: #2c3e50;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    
    /* Recommendation cards */
    .recommendation {
        background-color: #f0f4ff;
        border-left: 5px solid #667eea;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== LOAD MODEL ====================
model = joblib.load("model.pkl")

# ==================== INITIALIZE SESSION STATE ====================
# Ensures variables persist across app interactions
if "probability" not in st.session_state:
    st.session_state.probability = 0.0
if "prediction_made" not in st.session_state:
    st.session_state.prediction_made = False
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
if "confidence" not in st.session_state:
    st.session_state.confidence = 0.0

# ==================== UTILITY FUNCTIONS ====================

def calculate_confidence(probability):
    """Calculate confidence level based on probability
    High confidence if probability is close to 0% or 100%"""
    return max(abs(probability - 50) * 2, 50)

def generate_recommendations(cgpa, internship, aptitude):
    """Generate personalized recommendations based on student metrics"""
    recommendations = []
    
    # CGPA recommendations
    if cgpa < 7.0:
        recommendations.append({
            "type": "Academic",
            "icon": "📚",
            "title": "Improve CGPA",
            "text": f"Your CGPA is {cgpa:.2f}. Focus on improving academics. Aim for CGPA > 7.5 to increase placement chances by 30-40%."
        })
    
    # Aptitude recommendations
    if aptitude < 60:
        recommendations.append({
            "type": "Aptitude",
            "icon": "🧠",
            "title": "Enhance Aptitude Skills",
            "text": f"Your aptitude score is {aptitude}. Practice quantitative reasoning, logical thinking, and problem-solving daily."
        })
    
    # Internship recommendations
    if internship == 0:
        recommendations.append({
            "type": "Experience",
            "icon": "💼",
            "title": "Pursue Internships",
            "text": "You don't have internship experience. Gain practical experience through internships - it significantly boosts placement chances!"
        })
    
    # Positive reinforcement
    if cgpa >= 8.5 and aptitude >= 75 and internship == 1:
        recommendations.append({
            "type": "Success",
            "icon": "⭐",
            "title": "Excellent Profile",
            "text": "Congratulations! Your profile is very strong. Focus on interviews and soft skills to secure top placements."
        })
    
    return recommendations

def create_gauge_chart(probability):
    """Create an interactive gauge chart for probability visualization"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=probability,
        title={'text': "Placement Probability"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "#ffcccc"},
                {'range': [25, 50], 'color': "#ffe6cc"},
                {'range': [50, 75], 'color': "#e6f3ff"},
                {'range': [75, 100], 'color': "#ccffcc"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        },
        number={'suffix': "%"}
    ))
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=50, b=0))
    return fig

def create_pie_chart(probability):
    """Create a pie chart showing placed vs not placed probability"""
    labels = ["Placement Probability", "Non-Placement Probability"]
    values = [probability, 100 - probability]
    colors_pie = ["#2ecc71", "#e74c3c"]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors_pie),
        textposition='inside',
        textinfo='label+percent'
    )])
    fig.update_layout(height=350, margin=dict(l=0, r=0, t=50, b=0))
    return fig

def create_feature_comparison(cgpa, aptitude, internship_value):
    """Create a radar chart comparing normalized features"""
    # Normalize features to 0-100 scale
    cgpa_norm = (cgpa / 10.0) * 100
    aptitude_norm = aptitude
    internship_norm = internship_value * 100
    
    fig = go.Figure(data=go.Scatterpolar(
        r=[cgpa_norm, aptitude_norm, internship_norm],
        theta=['CGPA (out of 10)', 'Aptitude Score', 'Internship'],
        fill='toself',
        marker=dict(color='#667eea'),
        name='Student Metrics'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=350,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    return fig

def generate_pdf_report(cgpa, internship, aptitude, probability, prediction, confidence, recommendations):
    """Generate a professional PDF report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    elements.append(Paragraph("Student Placement Prediction Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Report Generation Date
    date_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(date_text, styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Student Information Table
    elements.append(Paragraph("Student Information", styles['Heading2']))
    data = [
        ['Metric', 'Value'],
        ['CGPA', f'{cgpa:.2f}/10.0'],
        ['Aptitude Score', f'{aptitude}/100'],
        ['Internship Experience', 'Yes' if internship == 1 else 'No'],
    ]
    table = Table(data, colWidths=[3*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Prediction Results
    elements.append(Paragraph("Prediction Results", styles['Heading2']))
    prediction_text = f"Placement Status: {'PLACED' if prediction == 1 else 'NOT PLACED'}"
    elements.append(Paragraph(prediction_text, styles['Normal']))
    elements.append(Paragraph(f"Placement Probability: {probability:.2f}%", styles['Normal']))
    elements.append(Paragraph(f"Prediction Confidence: {confidence:.2f}%", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Recommendations
    if recommendations:
        elements.append(Paragraph("Personalized Recommendations", styles['Heading2']))
        for rec in recommendations:
            rec_text = f"<b>{rec['icon']} {rec['title']}:</b> {rec['text']}"
            elements.append(Paragraph(rec_text, styles['Normal']))
            elements.append(Spacer(1, 0.1*inch))
    
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("For more information, visit our dashboard or contact placement office.", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==================== MAIN APP LAYOUT ====================

# Header Section
st.markdown("<h1>🎓 Student Placement Prediction System</h1>", unsafe_allow_html=True)
st.markdown("### Predictive Analytics Dashboard for Campus Placements")

# Divider
st.divider()

# ==================== SIDEBAR - INPUT SECTION ====================
st.sidebar.markdown("### 📝 Student Profile")

cgpa = st.sidebar.slider(
    "CGPA",
    min_value=0.0,
    max_value=10.0,
    value=7.0,
    step=0.1,
    help="Your Cumulative Grade Point Average (0.0 - 10.0)"
)

internship = st.sidebar.selectbox(
    "Internship Experience",
    options=[0, 1],
    format_func=lambda x: "Yes ✅" if x == 1 else "No ❌",
    help="Do you have internship experience?"
)

aptitude = st.sidebar.slider(
    "Aptitude Score",
    min_value=0,
    max_value=100,
    value=50,
    step=1,
    help="Your aptitude test score (0 - 100)"
)

# Predict Button
col1, col2 = st.sidebar.columns(2)
with col1:
    predict_button = st.button("🔮 Predict Placement", use_container_width=True)

with col2:
    reset_button = st.button("🔄 Reset", use_container_width=True)

# Reset functionality
if reset_button:
    st.session_state.probability = 0.0
    st.session_state.prediction_made = False
    st.session_state.prediction_result = None
    st.session_state.confidence = 0.0
    st.rerun()

# ==================== PREDICTION LOGIC ====================
if predict_button:
    # Create feature array from user inputs
    features = np.array([[cgpa, internship, aptitude]])
    
    # Get prediction from model
    prediction = model.predict(features)[0]
    
    # Calculate probability using model's predict_proba
    try:
        st.session_state.probability = model.predict_proba(features)[0][1] * 100
    except:
        st.session_state.probability = 80 if prediction == 1 else 20
    
    # Calculate confidence level
    st.session_state.confidence = calculate_confidence(st.session_state.probability)
    
    # Store prediction result
    st.session_state.prediction_result = prediction
    st.session_state.prediction_made = True

# ==================== PREDICTION SUMMARY SECTION ====================
if st.session_state.prediction_made:
    st.success("✅ Prediction completed! View detailed analytics below.")
    st.divider()
    
    # Prediction Result with Status
    col1, col2 = st.columns(2)
    
    with col1:
        if st.session_state.prediction_result == 1:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%); padding: 2rem; border-radius: 10px; color: white; text-align: center;'>
                <h2 style='color: white; margin: 0;'>✅ LIKELY TO BE PLACED</h2>
                <p style='font-size: 1.2em; margin: 0.5rem 0;'>Congratulations! Your profile is competitive.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); padding: 2rem; border-radius: 10px; color: white; text-align: center;'>
                <h2 style='color: white; margin: 0;'>❌ NOT LIKELY PLACED</h2>
                <p style='font-size: 1.2em; margin: 0.5rem 0;'>Work on improving metrics.</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); padding: 2rem; border-radius: 10px; color: white; text-align: center;'>
            <h3 style='color: white; margin: 0;'>Confidence Level</h3>
            <p style='font-size: 2.5em; margin: 0.5rem 0; font-weight: bold;'>{st.session_state.confidence:.1f}%</p>
            <p style='font-size: 0.9em; margin: 0;'>Model Confidence</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ==================== METRICS CARDS SECTION ====================
    st.markdown("### 📊 Student Metrics")
    
    metric_cols = st.columns(4)
    
    with metric_cols[0]:
        cgpa_color = "#2ecc71" if cgpa >= 8.0 else "#f39c12" if cgpa >= 7.0 else "#e74c3c"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {cgpa_color} 0%, {cgpa_color}dd 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center;'>
            <p style='font-size: 0.9em; margin: 0; opacity: 0.9;'>CGPA</p>
            <p style='font-size: 2.2em; margin: 0.5rem 0; font-weight: bold;'>{cgpa:.2f}</p>
            <p style='font-size: 0.8em; margin: 0;'>out of 10</p>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_cols[1]:
        aptitude_color = "#2ecc71" if aptitude >= 75 else "#f39c12" if aptitude >= 60 else "#e74c3c"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {aptitude_color} 0%, {aptitude_color}dd 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center;'>
            <p style='font-size: 0.9em; margin: 0; opacity: 0.9;'>Aptitude</p>
            <p style='font-size: 2.2em; margin: 0.5rem 0; font-weight: bold;'>{aptitude}</p>
            <p style='font-size: 0.8em; margin: 0;'>out of 100</p>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_cols[2]:
        internship_color = "#2ecc71" if internship == 1 else "#e74c3c"
        internship_text = "Yes ✅" if internship == 1 else "No ❌"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {internship_color} 0%, {internship_color}dd 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center;'>
            <p style='font-size: 0.9em; margin: 0; opacity: 0.9;'>Internship</p>
            <p style='font-size: 2.2em; margin: 0.5rem 0; font-weight: bold;'>{internship_text}</p>
            <p style='font-size: 0.8em; margin: 0;'>Experience</p>
        </div>
        """, unsafe_allow_html=True)
    
    with metric_cols[3]:
        prob_color = "#2ecc71" if st.session_state.probability >= 75 else "#f39c12" if st.session_state.probability >= 50 else "#e74c3c"
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {prob_color} 0%, {prob_color}dd 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center;'>
            <p style='font-size: 0.9em; margin: 0; opacity: 0.9;'>Probability</p>
            <p style='font-size: 2.2em; margin: 0.5rem 0; font-weight: bold;'>{st.session_state.probability:.1f}%</p>
            <p style='font-size: 0.8em; margin: 0;'>Placement</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # ==================== PROBABILITY PROGRESS BAR ====================
    st.markdown("### 📈 Placement Probability Progress")
    st.progress(
        min(st.session_state.probability / 100, 1.0),
        text=f"{st.session_state.probability:.2f}%"
    )
    
    st.divider()
    
    # ==================== ADVANCED ANALYTICS SECTION ====================
    st.markdown("### 📊 Advanced Analytics Dashboard")
    
    # Row 1: Gauge and Pie Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Placement Probability Gauge")
        gauge_fig = create_gauge_chart(st.session_state.probability)
        st.plotly_chart(gauge_fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Placement vs Non-Placement")
        pie_fig = create_pie_chart(st.session_state.probability)
        st.plotly_chart(pie_fig, use_container_width=True)
    
    st.divider()
    
    # Row 2: Feature Comparison Radar Chart
    st.markdown("#### Feature Comparison (Normalized to 100)")
    radar_fig = create_feature_comparison(cgpa, aptitude, internship)
    st.plotly_chart(radar_fig, use_container_width=True)
    
    st.divider()
    
    # ==================== RECOMMENDATIONS SECTION ====================
    st.markdown("### 💡 Personalized Recommendations")
    
    recommendations = generate_recommendations(cgpa, internship, aptitude)
    
    if recommendations:
        for rec in recommendations:
            with st.container():
                st.markdown(f"""
                <div style='background-color: #f0f4ff; border-left: 5px solid #667eea; padding: 1rem; border-radius: 5px; margin: 0.5rem 0;'>
                    <h4 style='margin: 0; color: #667eea;'>{rec['icon']} {rec['title']}</h4>
                    <p style='margin: 0.5rem 0; color: #2c3e50;'>{rec['text']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("💫 No specific recommendations at this time. Keep up the great work!")
    
    st.divider()
    
    # ==================== PDF REPORT DOWNLOAD ====================
    st.markdown("### 📄 Download Your Report")
    
    pdf_buffer = generate_pdf_report(
        cgpa, internship, aptitude,
        st.session_state.probability,
        st.session_state.prediction_result,
        st.session_state.confidence,
        recommendations
    )
    
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name=f"placement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
else:
    # Before prediction is made
    st.info("👉 Use the sidebar to enter your details and click 'Predict Placement' to get started!")