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

import json
import os
import re
import time
import uuid
import hashlib
import secrets
import smtplib
import ssl
from urllib.parse import quote_plus, unquote_plus

import bcrypt
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load environment variables from .env file in the project root
# Example .env content:
# EMAIL_ADDRESS=yourgmail@gmail.com
# EMAIL_PASSWORD=your_gmail_app_password
# APP_URL=http://localhost:8501
try:
    from dotenv import load_dotenv, find_dotenv

    def load_project_env():
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file)
            return env_file

        fallback_path = find_dotenv(usecwd=True)
        if fallback_path:
            load_dotenv(fallback_path)
            return fallback_path

        load_dotenv()
        return env_file

    dotenv_path = load_project_env()
except ImportError:
    st.error("python-dotenv is not installed. Run: pip install python-dotenv")
    st.stop()

# Email configuration loaded from .env
DOTENV_PATH = dotenv_path
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
APP_URL = os.getenv("APP_URL", "http://localhost:8501")

EMAIL_CONFIGURED = bool(EMAIL_ADDRESS and EMAIL_PASSWORD)

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="AI Placement Analytics Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== MODERN UI STYLING ====================
st.markdown(
    """
    <style>
    :root {
        color-scheme: light;
    }

    .main .block-container {
        padding: 2rem 2rem 3rem;
        background: transparent;
        min-height: 100vh;
    }

    .css-18e3th9 {
        background: transparent;
    }

    body {
        color: #0F172A;
        background: #F8FAFC;
        min-height: 100vh;
    }

    .stApp {
        background: transparent;
    }

    .hero-card,
    .auth-card {
        background: #FFFFFF;
        border: 1px solid rgba(148, 163, 184, 0.16);
        backdrop-filter: blur(20px);
        box-shadow: 0 20px 60px rgba(15, 23, 42, 0.08);
        border-radius: 28px;
        color: #0F172A;
        transition: transform 0.32s ease, box-shadow 0.32s ease, border-color 0.32s ease;
    }

    .stat-card {
        background: rgba(255, 255, 255, 0.98);
        border: 1px solid rgba(15, 23, 42, 0.06);
        box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
        border-radius: 24px;
        color: #0F172A;
        transition: transform 0.32s ease, box-shadow 0.32s ease, border-color 0.32s ease;
    }

    .hero-card:hover,
    .auth-card:hover,
    .stat-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 30px 70px rgba(15, 23, 42, 0.12);
        border-color: rgba(14, 165, 233, 0.22);
    }

    .hero-panel {
        padding: 3rem;
        border-radius: 30px;
        min-height: 560px;
    }

    .hero-title {
        font-size: clamp(2.8rem, 5vw, 4.4rem);
        line-height: 1.02;
        font-weight: 800;
        letter-spacing: -0.05em;
        margin-bottom: 0.9rem;
        color: #0F172A;
    }

    .hero-subtitle {
        font-size: 1.02rem;
        color: #64748B;
        max-width: 38rem;
        margin-bottom: 2rem;
        line-height: 1.75;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.65rem;
        margin-bottom: 2rem;
        padding: 0.8rem 1.1rem;
        border-radius: 999px;
        background: rgba(249, 115, 22, 0.12);
        color: #0F172A;
        font-size: 0.95rem;
        font-weight: 600;
        border: 1px solid rgba(249, 115, 22, 0.24);
    }

    .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 1rem;
        margin-top: 2rem;
    }

    .stat-card {
        padding: 1.3rem 1.35rem;
    }

    .stat-title {
        font-size: 0.85rem;
        color: #64748B;
        margin-bottom: 0.35rem;
        letter-spacing: 0.03em;
    }

    .stat-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0F172A;
    }

    .auth-panel {
        padding: 2.5rem;
        max-width: 520px;
        width: 100%;
    }

    .auth-card-title {
        font-size: 1.85rem;
        font-weight: 800;
        margin-bottom: 0.7rem;
    }

    .auth-card-subtitle {
        color: #64748B;
        margin-bottom: 1.75rem;
        line-height: 1.7;
    }

    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea {
        border-radius: 18px;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        color: #0F172A;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.06);
    }

    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #F97316;
        box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.18);
        outline: none;
    }

    .stTextInput>label,
    .stTextArea>label {
        color: #64748B;
    }

    .stButton>button {
        border-radius: 18px;
        padding: 0.95rem 1.3rem;
        border: none;
        font-weight: 700;
        background: #F97316;
        color: #FFFFFF;
        transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        background: #FB923C;
        box-shadow: 0 18px 32px rgba(249, 115, 22, 0.22);
    }

    .tab-icons {
        display: flex;
        gap: 0.45rem;
        align-items: center;
    }

    .login-footer-text {
        font-size: 0.95rem;
        color: #64748B;
        margin-top: 1rem;
    }

    .stAlert {
        border-radius: 18px;
        border: 1px solid rgba(15, 23, 42, 0.08) !important;
        background: #FFFFFF !important;
        color: #0F172A !important;
        box-shadow: 0 22px 50px rgba(15, 23, 42, 0.08);
    }

    .loading-placeholder {
        display: inline-flex;
        align-items: center;
        gap: 0.8rem;
        color: #0F172A;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    .pulse {
        width: 0.85rem;
        height: 0.85rem;
        border-radius: 999px;
        background: rgba(99, 102, 241, 0.9);
        animation: pulse 1.4s ease-in-out infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(0.85); opacity: 0.9; }
        50% { transform: scale(1.2); opacity: 0.35; }
    }

    @media (max-width: 1050px) {
        .stats-grid {
            grid-template-columns: 1fr;
        }
    }

    @media (max-width: 860px) {
        .hero-panel,
        .auth-panel {
            padding: 1.8rem;
        }
    }

    @media (max-width: 760px) {
        .hero-title {
            font-size: 2.5rem;
        }

        .hero-subtitle {
            max-width: 100%;
        }

        .hero-card,
        .auth-card {
            border-radius: 24px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==================== LOAD MODEL ====================
model = joblib.load("model.pkl")

# ==================== SESSION STATE INITIALIZATION ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "user" not in st.session_state:
    st.session_state.user = None
if "forgot_password" not in st.session_state:
    st.session_state.forgot_password = False
if "reset_required" not in st.session_state:
    st.session_state.reset_required = False
if "probability" not in st.session_state:
    st.session_state.probability = 0.0
if "prediction_made" not in st.session_state:
    st.session_state.prediction_made = False
if "prediction_result" not in st.session_state:
    st.session_state.prediction_result = None
if "confidence" not in st.session_state:
    st.session_state.confidence = 0.0

# Query param helpers (compatible with multiple Streamlit versions)
def get_query_params():
    try:
        if hasattr(st, "experimental_get_query_params"):
            return st.experimental_get_query_params()
        if hasattr(st, "get_query_params"):
            return st.get_query_params()
    except Exception:
        return {}
    return {}


def clear_query_params():
    try:
        if hasattr(st, "experimental_set_query_params"):
            # calling without args clears params in newer APIs
            try:
                st.experimental_set_query_params()
                return
            except TypeError:
                st.experimental_set_query_params(**{})
                return
        if hasattr(st, "set_query_params"):
            try:
                st.set_query_params()
            except TypeError:
                st.set_query_params(**{})
    except Exception:
        return

# Handle incoming query params for verification and reset links
params = get_query_params()
if params:
    # Email verification flow
    if "verify" in params and params.get("email") and params.get("token"):
        q_email = unquote_plus(params.get("email")[0])
        q_token = params.get("token")[0]
        ok = verify_verification_token(q_email, q_token)
        if ok:
            st.success("✅ Email verified successfully. You can now login.")
            # clean params
            clear_query_params()
        else:
            st.error("❌ Verification failed or link expired.")
            clear_query_params()

    # Password reset via token flow (opens a secure reset form)
    if "reset" in params and params.get("email") and params.get("token"):
        q_email = unquote_plus(params.get("email")[0])
        q_token = params.get("token")[0]
        if verify_reset_token(q_email, q_token):
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("<h3>🔒 Reset Your Password</h3>", unsafe_allow_html=True)
            new_pw = st.text_input("New Password", type="password", key="qs_new_password")
            conf_pw = st.text_input("Confirm Password", type="password", key="qs_confirm_password")
            if st.button("Update Password", key="qs_update_password_btn"):
                if not new_pw or not conf_pw:
                    st.error("Enter both password fields.")
                elif new_pw != conf_pw:
                    st.error("Passwords do not match.")
                elif len(new_pw) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    if update_user_password(q_email, new_pw):
                        # clear token
                        users = load_users()
                        user = users.get(q_email.lower())
                        if user:
                            user.pop("reset_token", None)
                            user.pop("reset_expiry", None)
                            users[q_email.lower()] = user
                            save_users(users)
                        st.success("✅ Password updated. You can now login.")
                        clear_query_params()
                    else:
                        st.error("Failed to update password. Try again or request a new reset link.")
            if st.button("Back to Login", key="qs_back_to_login"):
                clear_query_params()
            st.markdown("</div>", unsafe_allow_html=True)
            st.stop()
        else:
            st.error("❌ Invalid or expired reset link.")
            clear_query_params()

# ==================== UTILITY FUNCTIONS ====================

def calculate_confidence(probability):
    return max(abs(probability - 50) * 2, 50)


def generate_recommendations(cgpa, internship, aptitude):
    recommendations = []
    if cgpa < 7.0:
        recommendations.append({
            "icon": "📚",
            "title": "Placement Grade Boost",
            "text": f"Your CGPA is {cgpa:.2f}. Improving by just 0.5 can increase placement chances significantly."
        })
    if aptitude < 65:
        recommendations.append({
            "icon": "🧠",
            "title": "Aptitude Strength",
            "text": "Practice quantitative reasoning and logical puzzles daily to build confidence for placement tests."
        })
    if internship == 0:
        recommendations.append({
            "icon": "💼",
            "title": "Internship Experience",
            "text": "Secure at least one internship to improve your resume and real-world problem-solving skills."
        })
    if cgpa >= 8.5 and aptitude >= 75 and internship == 1:
        recommendations.append({
            "icon": "🚀",
            "title": "Strong Profile",
            "text": "Your profile looks strong. Focus on interview preparation and soft skill polish."
        })
    return recommendations


def create_gauge_chart(probability):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=probability,
        title={"text": "Placement Probability"},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [None, 100]},
            "bar": {"color": "#2563eb"},
            "steps": [
                {"range": [0, 25], "color": "#fee2e2"},
                {"range": [25, 50], "color": "#fef3c7"},
                {"range": [50, 75], "color": "#dbeafe"},
                {"range": [75, 100], "color": "#d1fae5"},
            ],
            "threshold": {
                "line": {"color": "#0f172a", "width": 4},
                "thickness": 0.75,
                "value": 50,
            },
        },
        number={"suffix": "%"},
    ))
    fig.update_layout(height=340, margin={"l": 0, "r": 0, "t": 20, "b": 0})
    return fig


def create_pie_chart(probability):
    fig = go.Figure(data=[go.Pie(
        labels=["Placement", "Non-Placement"],
        values=[probability, 100 - probability],
        marker={"colors": ["#2563eb", "#cbd5e1"]},
        textinfo="label+percent",
        hole=0.4,
    )])
    fig.update_layout(height=340, margin={"l": 0, "r": 0, "t": 20, "b": 0})
    return fig


def create_feature_comparison(cgpa, aptitude, internship_value):
    cgpa_norm = (cgpa / 10.0) * 100
    internship_norm = internship_value * 100
    fig = go.Figure(data=go.Scatterpolar(
        r=[cgpa_norm, aptitude, internship_norm],
        theta=["CGPA", "Aptitude", "Internship"],
        fill="toself",
        marker={"color": "#7c3aed"},
    ))
    fig.update_layout(
        polar={"radialaxis": {"visible": True, "range": [0, 100]}},
        height=360,
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
    )
    return fig


def generate_pdf_report(cgpa, internship, aptitude, probability, prediction, confidence, recommendations):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1f77b4"),
        alignment=1,
        spaceAfter=20,
    )
    elements.append(Paragraph("Student Placement Prediction Report", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    date_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elements.append(Paragraph(date_text, styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Student Information", styles["Heading2"]))
    data = [
        ["Metric", "Value"],
        ["CGPA", f"{cgpa:.2f}/10"],
        ["Aptitude", f"{aptitude}/100"],
        ["Internship", "Yes" if internship == 1 else "No"],
    ]
    table = Table(data, colWidths=[3 * inch, 3 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph("Prediction Results", styles["Heading2"]))
    elements.append(Paragraph(f"Placement Status: {'PLACED' if prediction == 1 else 'NOT PLACED'}", styles["Normal"]))
    elements.append(Paragraph(f"Placement Probability: {probability:.2f}%", styles["Normal"]))
    elements.append(Paragraph(f"Confidence Score: {confidence:.2f}%", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    if recommendations:
        elements.append(Paragraph("Recommendations", styles["Heading2"]))
        for rec in recommendations:
            elements.append(Paragraph(f"• {rec['icon']} {rec['title']}: {rec['text']}", styles["Normal"]))
            elements.append(Spacer(1, 0.1 * inch))
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==================== AUTHENTICATION HELPERS ====================

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def email_exists(email, users=None):
    if users is None:
        users = load_users()
    return email.lower() in users


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    try:
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed.encode("utf-8")
        if hashed.startswith(("$2a$", "$2b$", "$2y$")):
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        legacy_hash = hashlib.sha256(password_bytes).hexdigest()
        return legacy_hash == hashed
    except Exception:
        return False


def generate_temp_password() -> str:
    return secrets.token_urlsafe(10)


def send_email(to_email: str, subject: str, html_content: str, plain_text: str = ""):
    sender = EMAIL_ADDRESS
    password = EMAIL_PASSWORD
    if not sender or not password:
        return False, "Please configure EMAIL_ADDRESS and EMAIL_PASSWORD in .env"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    part1 = MIMEText(plain_text or "", "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls(context=context)
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True, "✅ Email sent successfully."
    except smtplib.SMTPAuthenticationError:
        return False, "❌ SMTP authentication failed. Check EMAIL_ADDRESS and EMAIL_PASSWORD."
    except Exception as exc:
        return False, f"❌ Failed to send email: {exc}"


def create_reset_token(email: str, expire_seconds: int = 3600) -> str:
    token = secrets.token_urlsafe(24)
    users = load_users()
    user = users.get(email.lower())
    if not user:
        return ""
    user["reset_token"] = token
    user["reset_expiry"] = int(time.time()) + expire_seconds
    users[email.lower()] = user
    save_users(users)
    return token


def verify_reset_token(email: str, token: str) -> bool:
    users = load_users()
    user = users.get(email.lower())
    if not user:
        return False
    stored = user.get("reset_token")
    expiry = user.get("reset_expiry", 0)
    if not stored or stored != token:
        return False
    if int(time.time()) > int(expiry):
        return False
    return True


def create_verification_token(email: str, expire_seconds: int = 86400) -> str:
    token = secrets.token_urlsafe(24)
    users = load_users()
    user = users.get(email.lower())
    if not user:
        return ""
    user["verify_token"] = token
    user["verify_expiry"] = int(time.time()) + expire_seconds
    users[email.lower()] = user
    save_users(users)
    return token


def verify_verification_token(email: str, token: str) -> bool:
    users = load_users()
    user = users.get(email.lower())
    if not user:
        return False
    stored = user.get("verify_token")
    expiry = user.get("verify_expiry", 0)
    if not stored or stored != token:
        return False
    if int(time.time()) > int(expiry):
        return False
    # mark verified
    user["verified"] = True
    user.pop("verify_token", None)
    user.pop("verify_expiry", None)
    users[email.lower()] = user
    save_users(users)
    return True


def send_reset_email(email: str, token: str, name: str = ""):
    link = f"{APP_URL}/?reset=1&email={quote_plus(email)}&token={quote_plus(token)}"
    subject = "[AI Placement] Password Reset Instructions"
    html = f"""
    <html>
      <body style='font-family:Arial,Helvetica,sans-serif;color:#0f172a'>
        <div style='padding:20px; max-width:600px; margin:auto; background:#f8fafc; border-radius:12px;'>
          <h2 style='color:#0f172a;'>Password Reset Request</h2>
          <p>Hi {name or 'Student'},</p>
          <p>We received a request to reset your password for your AI Placement Analytics account.</p>
          <p style='text-align:center; margin:24px 0;'>
            <a href='{link}' style='background:#2563eb;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;display:inline-block;'>Reset Password</a>
          </p>
          <p>If the button doesn't work, copy and paste this link into your browser:</p>
          <p style='font-size:12px;color:#475569;word-break:break-all'>{link}</p>
          <p style='color:#475569;'>This link will expire in 1 hour. If you didn't request a password reset, please ignore this email.</p>
          <p style='margin-top:16px;color:#475569;'>Regards,<br/>AI Placement Analytics Team</p>
        </div>
      </body>
    </html>
    """
    plain = f"Password reset link: {link}\nThis link expires in 1 hour."
    return send_email(email, subject, html, plain)


def send_verification_email(email: str, token: str, name: str = ""):
    link = f"{APP_URL}/?verify=1&email={quote_plus(email)}&token={quote_plus(token)}"
    subject = "[AI Placement] Verify your email address"
    html = f"""
    <html>
      <body style='font-family:Arial,Helvetica,sans-serif;color:#0f172a'>
        <div style='padding:20px; max-width:600px; margin:auto; background:#f8fafc; border-radius:12px;'>
          <h2 style='color:#0f172a;'>Verify Your Email</h2>
          <p>Hi {name or 'Student'},</p>
          <p>Thanks for creating an account with AI Placement Analytics. Click the button below to verify your email address.</p>
          <p style='text-align:center; margin:24px 0;'>
            <a href='{link}' style='background:#2563eb;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;display:inline-block;'>Verify Email</a>
          </p>
          <p>If the button doesn't work, copy and paste this link into your browser:</p>
          <p style='font-size:12px;color:#475569;word-break:break-all'>{link}</p>
          <p style='margin-top:16px;color:#475569;'>Regards,<br/>AI Placement Analytics Team</p>
        </div>
      </body>
    </html>
    """
    plain = f"Verify your email: {link}\nThis link expires in 24 hours."
    return send_email(email, subject, html, plain)


def set_temporary_password(email: str, temp_password: str) -> bool:
    users = load_users()
    user = users.get(email.lower())
    if not user:
        return False
    user["password"] = hash_password(temp_password)
    user["reset_required"] = True
    users[email.lower()] = user
    save_users(users)
    return True


def update_user_password(email: str, new_password: str) -> bool:
    users = load_users()
    user = users.get(email.lower())
    if not user:
        return False
    user["password"] = hash_password(new_password)
    user["reset_required"] = False
    users[email.lower()] = user
    save_users(users)
    return True


def register_user(data: dict):
    users = load_users()
    email = data["email"].lower()
    if email in users:
        return False, "❌ Email already registered"
    users[email] = {
        "email": email,
        "name": data.get("name", ""),
        "college": data.get("college", ""),
        "branch": data.get("branch", ""),
        "grad_year": data.get("grad_year", ""),
        "password": hash_password(data.get("password", "")),
        "reset_required": False,
        "verified": False,
        "created_at": time.time(),
    }
    save_users(users)
    return True, "✅ Registration successful"


def authenticate_user(email: str, password: str):
    users = load_users()
    user = users.get(email.lower())
    if not user:
        return False, "Account not found", False
    if not user.get("verified", False):
        if EMAIL_CONFIGURED:
            return False, "Account exists but email not verified. Check your inbox.", False
        user["verified"] = True
        users[email.lower()] = user
        save_users(users)
    if check_password(password, user.get("password", "")):
        return True, user, user.get("reset_required", False)
    return False, "Incorrect password", False


def valid_email(email: str) -> bool:
    return bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))


def render_auth_card():
    st.markdown("<div class='hero-card auth-page'>", unsafe_allow_html=True)
    cols = st.columns([1.35, 1], gap="large")
    with cols[0]:
        st.markdown(
            "<div class='hero-panel'>"
            "<div class='hero-badge'>✨ Premium AI Career Insights</div>"
            "<div class='hero-title'>AI Placement Analytics Dashboard</div>"
            "<div class='hero-subtitle'>Predict student placement success using AI-powered analytics, career readiness scoring, and skill-gap intelligence.</div>"
            "<div class='stats-grid'>"
            "<div class='stat-card'><div class='stat-title'>Prediction Accuracy</div><div class='stat-value'>95%</div></div>"
            "<div class='stat-card'><div class='stat-title'>Students Analyzed</div><div class='stat-value'>10,000+</div></div>"
            "<div class='stat-card'><div class='stat-title'>AI Career Insights</div><div class='stat-value'>Intelligent</div></div>"
            "<div class='stat-card'><div class='stat-title'>Real-Time Analytics</div><div class='stat-value'>Live</div></div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
    with cols[1]:
        st.markdown("<div class='auth-panel glass-card'>", unsafe_allow_html=True)
        st.markdown(
            "<div class='auth-card-title'>Welcome Back</div>"
            "<div class='auth-card-subtitle'>Secure access to the AI Placement Analytics dashboard.</div>",
            unsafe_allow_html=True,
        )
        tabs = st.tabs(["Login", "Register"])
        with tabs[0]:
            if st.session_state.forgot_password:
                st.markdown("<div class='loading-placeholder'><span class='pulse'></span>Reset flow active</div>", unsafe_allow_html=True)
                reset_email = st.text_input("Registered Email", key="reset_email", placeholder="name@example.com")
                reset_new_password = st.text_input(
                    "New Password",
                    type="password",
                    key="reset_new_password",
                    placeholder="Enter a new password",
                )
                reset_confirm_password = st.text_input(
                    "Confirm New Password",
                    type="password",
                    key="reset_confirm_password",
                    placeholder="Confirm your new password",
                )
                if st.button("Send Reset Password", key="reset_password_btn"):
                    if not reset_email:
                        st.error("Enter your registered email address.")
                    elif not valid_email(reset_email):
                        st.error("Enter a valid email address.")
                    elif not email_exists(reset_email):
                        st.error("❌ Email not found")
                    elif not reset_new_password or not reset_confirm_password:
                        st.error("Enter and confirm your new password.")
                    elif reset_new_password != reset_confirm_password:
                        st.error("Passwords do not match.")
                    elif len(reset_new_password) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif not EMAIL_CONFIGURED:
                        if update_user_password(reset_email, reset_new_password):
                            st.success("✅ Password reset successfully. You can now log in with your new password.")
                            st.session_state.forgot_password = False
                        else:
                            st.error("❌ Failed to reset password. Try again later.")
                    else:
                        token = create_reset_token(reset_email)
                        if not token:
                            st.error("❌ Failed to create reset token. Try again later.")
                        else:
                            users = load_users()
                            name = users.get(reset_email.lower(), {}).get("name", "")
                            ok, msg = send_reset_email(reset_email, token, name)
                            if ok:
                                st.success("✅ Password reset email sent successfully. Check your inbox.")
                                st.session_state.forgot_password = False
                            else:
                                st.error(msg)
                if st.button("Back to Login", key="back_to_login_btn"):
                    st.session_state.forgot_password = False
                    st.rerun()
            else:
                with st.form("login_form"):
                    show_password = st.checkbox("Show Password", key="show_password")
                    login_email = st.text_input("Email", key="login_email", placeholder="name@example.com")
                    login_password = st.text_input(
                        "Password",
                        type="default" if show_password else "password",
                        key="login_password",
                        placeholder="Enter your password",
                    )
                    st.checkbox("Remember Me", key="remember_me")
                    submitted = st.form_submit_button("Login", help="Submit your login credentials")

                    if submitted:
                        if not login_email or not login_password:
                            st.error("Enter both email and password.")
                        elif not valid_email(login_email):
                            st.error("Enter a valid email address.")
                        else:
                            ok, res, reset_required = authenticate_user(login_email, login_password)
                            if ok:
                                st.session_state.logged_in = True
                                st.session_state.user_email = login_email.lower()
                                st.session_state.user = res
                                st.session_state.reset_required = reset_required
                                st.success("✅ Login successful! Redirecting to your dashboard...")
                                st.rerun()
                            else:
                                st.error(res)
                if st.button("Forgot Password?", key="forgot_password_btn"):
                    st.session_state.forgot_password = True
                    st.rerun()
                st.markdown("<div class='login-footer-text'>Need help? Click the button to reset your password securely.</div>", unsafe_allow_html=True)
        with tabs[1]:
            with st.form("register_form"):
                reg_name = st.text_input("Full Name", key="reg_name", placeholder="Jane Doe")
                reg_email = st.text_input("Email Address", key="reg_email", placeholder="name@example.com")
                reg_college = st.text_input("College Name", key="reg_college", placeholder="University/College")
                reg_branch = st.text_input("Branch", key="reg_branch", placeholder="Computer Science")
                reg_grad = st.number_input("Graduation Year", key="reg_grad", min_value=1950, max_value=2100, value=2026)
                reg_password = st.text_input(
                    "Password",
                    type="password",
                    key="reg_password",
                    placeholder="Create a secure password",
                )
                reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
                submitted = st.form_submit_button("Create Account")
                if submitted:
                    if not reg_name or not reg_email or not reg_password or not reg_confirm:
                        st.error("All fields are required.")
                    elif not valid_email(reg_email):
                        st.error("Enter a valid email address.")
                    elif len(reg_password) < 8:
                        st.error("Password must be at least 8 characters.")
                    elif reg_password != reg_confirm:
                        st.error("Passwords do not match.")
                    elif email_exists(reg_email):
                        st.error("❌ Email already registered.")
                    else:
                        ok, msg = register_user({
                            "email": reg_email,
                            "password": reg_password,
                            "name": reg_name,
                            "college": reg_college,
                            "branch": reg_branch,
                            "grad_year": reg_grad,
                        })
                        if ok:
                            if EMAIL_CONFIGURED:
                                token = create_verification_token(reg_email)
                                if token:
                                    send_ok, send_msg = send_verification_email(reg_email, token, reg_name)
                                    if send_ok:
                                        st.success("✅ Account created. A verification email has been sent. Check your inbox.")
                                    else:
                                        st.error(send_msg)
                                        st.write("Debug: send_verification_email returned:", send_msg)
                                else:
                                    st.error("❌ Failed to create verification token.")
                            else:
                                users = load_users()
                                users[reg_email.lower()]["verified"] = True
                                save_users(users)
                                st.success("✅ Account created. Email verification skipped because email is not configured.")
                            st.balloons()
                        else:
                            st.error(msg)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_feature_cards():
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:1rem; color:#0f172a;'>Project Features</h3>", unsafe_allow_html=True)
    for title, subtitle, icon in [
        ("📊 Placement Prediction", "Model-driven placement likelihood based on academic inputs.", "📊"),
        ("💼 Career Readiness Score", "Score your profile against industry expectations.", "💼"),
        ("🎯 Skill Gap Analysis", "Understand where to improve your skills quickly.", "🎯"),
        ("📈 Confidence Analytics", "Get confidence metrics for predicted outcomes.", "📈"),
    ]:
        st.markdown(
            f"<div class='feature-card'><h4>{icon} {title}</h4><p>{subtitle}</p></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ==================== DASHBOARD UI ====================

def render_dashboard_header():
    st.markdown(
        "<div class='hero-section'>"
        "<div class='hero-title'>🎓 AI Placement Analytics Dashboard</div>"
        "<div class='hero-subtitle'>Student Career Readiness & Placement Prediction</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_welcome_bar():
    cols = st.columns([3, 1])
    with cols[0]:
        st.write("")
    with cols[1]:
        st.markdown(
            f"<div class='topbar-right'><div class='welcome-tag'>Welcome, <strong>{st.session_state.user_email}</strong></div></div>",
            unsafe_allow_html=True,
        )
        if st.button("Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.session_state.user = None
            st.session_state.reset_required = False
            st.session_state.forgot_password = False
            st.rerun()


def render_footer():
    st.markdown(
        "<div class='footer'><span class='footer-logo'>Powered by AI Placement Analytics</span></div>",
        unsafe_allow_html=True,
    )


# ==================== MAIN LAYOUT ====================

render_dashboard_header()

if not st.session_state.logged_in:
    render_auth_card()
    render_footer()
    st.stop()

render_welcome_bar()

if st.session_state.reset_required:
    st.warning("You must update your temporary password before accessing the dashboard.")
    new_password = st.text_input("New Password", type="password", key="new_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
    if st.button("Update Password", key="update_password_btn"):
        if not new_password or not confirm_password:
            st.error("Enter both password fields.")
        elif new_password != confirm_password:
            st.error("Passwords do not match.")
        elif len(new_password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            if update_user_password(st.session_state.user_email, new_password):
                st.success("✅ Password updated successfully. You can now continue.")
                st.session_state.reset_required = False
                st.rerun()
            else:
                st.error("Failed to update password. Please try again.")
    st.stop()

search = st.text_input(
    "🔍 Search Roles or Companies",
    placeholder="e.g. Software Engineer, TCS, Amazon",
)
if search:
    if "amazon" in search.lower():
        st.success("Amazon Hiring: Focus on DSA, System Design, OOPs")
    elif "tcs" in search.lower():
        st.success("TCS Hiring: Focus on Aptitude, Coding, Communication")
    elif "software engineer" in search.lower():
        st.success("Recommended Skills: Python, DSA, Projects, SQL")
    else:
        st.info(f"Searching opportunities for: {search}")

st.divider()

# ==================== SIDEBAR INPUT ====================
st.sidebar.markdown("### 📝 Student Profile")
student_name = st.sidebar.text_input("Student Name", placeholder="Enter your name")
st.info(f"👋 Welcome, {student_name}!")

cgpa = st.sidebar.slider(
    "CGPA",
    min_value=0.0,
    max_value=10.0,
    value=7.0,
    step=0.1,
    help="Your Cumulative Grade Point Average (0.0 - 10.0)",
)

internship = st.sidebar.selectbox(
    "Internship Experience",
    options=[0, 1],
    format_func=lambda x: "Yes ✅" if x == 1 else "No ❌",
    help="Do you have internship experience?",
)

aptitude = st.sidebar.slider(
    "Aptitude Score",
    min_value=0,
    max_value=100,
    value=50,
    step=1,
    help="Your aptitude test score (0 - 100)",
)

communication = st.sidebar.slider(
    "Communication Skills",
    min_value=0,
    max_value=100,
    value=50,
    step=1,
)

coding = st.sidebar.slider(
    "Coding Skills",
    min_value=0,
    max_value=100,
    value=50,
    step=1,
)

projects = st.sidebar.number_input(
    "Projects Completed",
    min_value=0,
    max_value=20,
    value=2,
)

# Predict and reset buttons
col1, col2 = st.sidebar.columns(2)
with col1:
    predict_button = st.button("🔮 Predict Placement", use_container_width=True)
with col2:
    reset_button = st.button("🔄 Reset", use_container_width=True)

if reset_button:
    st.session_state.probability = 0.0
    st.session_state.prediction_made = False
    st.session_state.prediction_result = None
    st.session_state.confidence = 0.0
    st.rerun()

# ==================== PREDICTION LOGIC ====================
if predict_button:
    features = np.array([[cgpa, internship, aptitude, communication, coding, projects]])
    prediction = model.predict(features)[0]
    try:
        st.session_state.probability = model.predict_proba(features)[0][1] * 100
    except Exception:
        st.session_state.probability = 80 if prediction == 1 else 20
    st.session_state.confidence = calculate_confidence(st.session_state.probability)
    st.session_state.prediction_result = prediction
    st.session_state.prediction_made = True

# ==================== DASHBOARD CONTENT ====================
if st.session_state.prediction_made:
    st.success("✅ Prediction completed. Review the analytics below.")
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.prediction_result == 1:
            st.markdown(
                "<div class='glass-card'>"
                "<h3 style='margin-top:0; color:#0f172a;'>✅ Likely to be Placed</h3>"
                "<p style='color:#334155;'>Your profile has strong placement potential. Keep building projects and preparing for interviews.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='glass-card'>"
                "<h3 style='margin-top:0; color:#b91c1c;'>❌ Not likely placed</h3>"
                "<p style='color:#334155;'>Focus on improving your scores and practical experience to boost placement chances.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
    with col2:
        st.plotly_chart(create_gauge_chart(st.session_state.probability), use_container_width=True)
    st.divider()
    metric_cols = st.columns(4)
    metric_values = [
        ("CGPA", f"{cgpa:.2f}", "#3b82f6"),
        ("Aptitude", f"{aptitude}", "#0ea5e9"),
        ("Internship", "Yes ✅" if internship == 1 else "No ❌", "#10b981"),
        ("Confidence", f"{st.session_state.confidence:.1f}%", "#8b5cf6"),
    ]
    for col, (label, value, color) in zip(metric_cols, metric_values):
        col.markdown(
            f"<div class='glass-card' style='padding:1rem; text-align:center;'>"
            f"<p style='margin:0; color:{color}; font-weight:700;'>{label}</p>"
            f"<p style='margin:0.6rem 0 0; font-size:2rem; font-weight:800; color:#0f172a;'>{value}</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    st.divider()
    graph_cols = st.columns(2)
    with graph_cols[0]:
        st.markdown("#### Feature Comparison")
        st.plotly_chart(create_feature_comparison(cgpa, aptitude, internship), use_container_width=True)
    with graph_cols[1]:
        st.markdown("#### Placement vs Non-Placement")
        st.plotly_chart(create_pie_chart(st.session_state.probability), use_container_width=True)
    st.divider()
    recommendations = generate_recommendations(cgpa, internship, aptitude)
    if recommendations:
        st.markdown("### 💡 Personalized Recommendations")
        for rec in recommendations:
            st.markdown(
                f"<div class='feature-card'><strong>{rec['icon']} {rec['title']}</strong><p>{rec['text']}</p></div>",
                unsafe_allow_html=True,
            )
    pdf_buffer = generate_pdf_report(
        cgpa,
        internship,
        aptitude,
        st.session_state.probability,
        st.session_state.prediction_result,
        st.session_state.confidence,
        recommendations,
    )
    st.download_button(
        label="📥 Download PDF Report",
        data=pdf_buffer,
        file_name=f"placement_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
else:
    st.info("👉 Use the sidebar to enter student details and click Predict Placement.")

render_footer()
