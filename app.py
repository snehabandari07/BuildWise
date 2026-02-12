import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import hashlib
import uuid
import random
from huggingface_hub import InferenceClient
from PIL import Image
import io

# --- Data Persistence Helper Functions ---

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    if not os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "w") as f:
            json.dump([], f)

def load_users():
    ensure_data_dir()
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_users(users):
    ensure_data_dir()
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_projects():
    ensure_data_dir()
    try:
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_project_to_db(project_data):
    ensure_data_dir()
    projects = load_projects()
    projects.append(project_data)
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, name, email):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    
    users[username] = {
        "password": hash_password(password),
        "name": name,
        "email": email
    }
    save_users(users)
    return True, "Registration successful! Please login."

def authenticate_user(username, password):
    users = load_users()
    if username in users and users[username]["password"] == hash_password(password):
        return True, users[username]["name"]
    return False, None

# --- Page Config ---
st.set_page_config(
    page_title="AI Construction Plan",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
def load_css():
    st.markdown("""
        <style>
        /* General Body and Background */
        /* Main Container Background */
        .stApp {
            background-color: #f8f9fa !important;
            background: linear-gradient(135deg, #f9f9f9 0%, #e6f7ff 100%) !important;
            font-family: 'Inter', sans-serif !important;
            color: #111111 !important;
        }

        /* Sidebar Background */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #e0e0e0;
        }

        /* Header Background */
        [data-testid="stHeader"] {
            background-color: rgba(255, 255, 255, 0.95) !important;
        }


        /* Typography */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            color: #051928 !important; /* Darker Navy */
            font-weight: 800 !important;
            margin-bottom: 0.8rem !important;
        }
        
        h1 { font-size: 2.5rem !important; }
        h2 { font-size: 1.8rem !important; }
        h3 { font-size: 1.4rem !important; }
        
        /* Streamlit Label Styling */
        .stTextInput label, .stSelectbox label, .stNumberInput label, .stSlider label, .stDateInput label {
            color: #111111 !important; /* Pure Black for Labels */
            font-weight: 700 !important; /* Bolder */
            font-size: 1rem !important;
            margin-bottom: 0.4rem !important;
        }
        
        /* Input Text Color & Weight */
        .stTextInput input, .stNumberInput input, .stDateInput input, 
        .stSelectbox div[data-baseweb="select"] span, 
        div[data-baseweb="base-input"] input {
            color: #000000 !important; /* Pitch Black */
            font-weight: 600 !important;
        }
        
        /* Placeholder color for contrast */
        ::placeholder {
            color: #555555 !important; /* Darker Gray Placeholder */
            font-weight: 500 !important;
        }
        
        p, .stMarkdown, .stMarkdown p {
            color: #222222 !important; /* Dark Gray for Paragraphs */
            font-weight: 500 !important; /* Slightly heavier weight */
            line-height: 1.6 !important;
        }

        /* Navigation Bar */
        .nav-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 2rem;
            background-color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Slightly deeper shadow */
            border-radius: 12px;
            margin-bottom: 2rem;
            border: 1px solid #d0d0d0; /* Darker border */
        }
        .nav-logo {
            font-size: 1.5rem;
            font-weight: 900;
            color: #051928; /* Darker Navy */
        }
        .nav-user {
            font-weight: 700;
            color: #051928;
            margin-right: 15px;
        }

        /* Forms */
        .auth-form {
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border: 1px solid #e0e0e0;
            max_width: 400px;
            margin: auto;
        }

        /* Cards */
        .feature-card {
            background: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #e0e0e0;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            height: 100%;
        }
        .feature-card p {
            color: #333333 !important;
        }
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 20px rgba(0,0,0,0.12);
        }
        .feature-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            color: #00897b; /* Darker Teal */
        }
        .dashboard-card {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.06);
            border: 1px solid #e0e0e0;
            margin-bottom: 2rem;
            height: 100%;
        }
        .stat-value {
            font-size: 2.2rem;
            font-weight: 900;
            color: #051928; /* Darker Navy */
        }
        .ai-suggestion {
            background-color: #e0f2f1;
            color: #004d40; /* Very Dark Teal Text */
            padding: 1rem;
            border-radius: 8px;
            margin-top: 1.5rem;
            font-size: 0.95rem;
            font-weight: 600;
            border-left: 5px solid #00897b;
            line-height: 1.5;
        }

        /* Metric Styling - Make values darker */
        [data-testid="stMetricValue"] {
            color: #000000 !important;
            font-weight: 800 !important;
            font-size: 2.5rem !important; /* Larger for better visibility */
        }
        
        [data-testid="stMetricLabel"] {
             color: #333333 !important;
             font-weight: 600 !important;
        }

        /* Input Styling - General */
        .stTextInput > div > div > input, 
        .stSelectbox > div > div > div, 
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {
            background-color: #F5F5F5 !important; /* Light Gray input bg */
            border: 1px solid #d0d0d0 !important; /* Lighter border for contrast */
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            transition: border-color 0.2s ease;
        }

        /* Specific Text Color & Weight for Inputs - Maximize Contrast */
        
        /* Text Input */
        div[data-testid="stTextInput"] input {
             color: #000000 !important;
             font-weight: 900 !important;
             -webkit-text-fill-color: #000000 !important;
             background-color: #F5F5F5 !important;
             background: #F5F5F5 !important;
        }

        /* Number Input */
        div[data-testid="stNumberInput"] input {
             color: #000000 !important;
             font-weight: 900 !important;
             -webkit-text-fill-color: #000000 !important;
             caret-color: #000000 !important;
             background-color: #F5F5F5 !important;
             background: #F5F5F5 !important;
        }

        /* Date Input */
        div[data-testid="stDateInput"] input {
             color: #000000 !important;
             font-weight: 900 !important;
             -webkit-text-fill-color: #000000 !important;
             background-color: #F5F5F5 !important;
             background: #F5F5F5 !important;
        }

        /* Selectbox - The selected value */
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
             color: #000000 !important;
             font-weight: 900 !important;
             -webkit-text-fill-color: #000000 !important;
             background-color: #F5F5F5 !important;
             background: #F5F5F5 !important;
        }
        
        /* Selectbox - Arrow Icon */
        div[data-testid="stSelectbox"] svg {
             fill: #000000 !important; /* Pitch Black Arrow */
             color: #000000 !important;
        }
        
        /* Selectbox - Dropdown Menu Items */
        div[data-baseweb="menu"] li, div[data-baseweb="menu"] div {
             color: #000000 !important;
             font-weight: 700 !important;
        }
        
        div[data-testid="stTextInput"] > div > div > input:focus, 
        div[data-testid="stSelectbox"] > div > div > div:focus,
        div[data-testid="stNumberInput"] > div > div > input:focus,
        div[data-testid="stDateInput"] > div > div > input:focus {
            border-color: #051928 !important; /* Dark Navy Focus */
            box-shadow: 0 0 0 1px #051928 !important;
        }

        /* Ensure Backgrounds are distinctively lighter (Light Gray) than text (Black) */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input, 
        .stDateInput > div > div > input,
        div[data-baseweb="select"] > div {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
            border: 1px solid #d0d0d0 !important;
            box-shadow: none !important;
        }
        
        /* Specific targeting for Date Input container to remove conflicting styles */
        div[data-testid="stDateInput"] > div > div {
             background-color: #F5F5F5 !important;
             background: #F5F5F5 !important;
             border-color: #d0d0d0 !important;
        }
        
        /* Additional enforcement for Number Input */
        div[data-testid="stNumberInput"] > div > div > input {
             background-color: #F5F5F5 !important;
             background: #F5F5F5 !important;
        }
        
        /* Additional enforcement for Date Input */
        div[data-testid="stDateInput"] > div > div > input {
             background-color: #F5F5F5 !important;
             background: #F5F5F5 !important;
        }

        .stSlider > div > div > div > div {
            background-color: #051928;
        }
        
        /* Buttons */
        .stButton > button {
            background-color: #E3F2FD; /* Light Blue Background */
            color: #0F2A44; /* Dark Navy Text */
            border-radius: 8px;
            border: 2px solid #0F2A44; /* Dark Border for specific definition */
            padding: 0.6rem 2rem;
            font-weight: 700;
            width: 100%;
            transition: background 0.3s ease, transform 0.1s ease;
        }
        .stButton > button:hover {
            background-color: #BBDEFB; /* Slightly darker light blue on hover */
            border: 2px solid #163C5F;
            color: #163C5F;
            transform: translateY(-1px);
        }
        </style>
    """, unsafe_allow_html=True)

# --- Application State and Navigation ---
if 'page' not in st.session_state:
    st.session_state.page = 'home'
if 'user' not in st.session_state:
    st.session_state.user = None
if 'username' not in st.session_state:
    st.session_state.username = None

def navigate_to(page):
    st.session_state.page = page
    st.rerun()

def logout():
    st.session_state.user = None
    st.session_state.username = None
    if 'plan_results' in st.session_state:
        del st.session_state.plan_results
    if 'project_inputs' in st.session_state:
        del st.session_state.project_inputs
    if 'blueprints' in st.session_state:
        del st.session_state.blueprints
    navigate_to('home')

# --- Real AI Generator (Groq) ---
from groq import Groq

# Initialize Groq Client
# In a production app, use st.secrets["GROQ_API_KEY"]
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

def generate_plan(project_details):
    """
    Generates construction plan estimates using Groq API (Llama3-70b).
    Falls back to mock logic on failure.
    """
    try:
        # Construct the prompt
        prompt = f"""
        Act as an expert construction estimator and project manager. 
        Analyze the following project and provide a detailed cost estimate, schedule breakdown, and smart recommendations.
        
        Project Details:
        - Type: {project_details['type']}
        - Subtype: {project_details.get('subtype', 'General')}
        - Location: {project_details['location']}
        - Area: {project_details['area']} sq. ft.
        - Budget: ${project_details['budget']}
        - Duration: {project_details['duration']} months
        - Start Date: {project_details['start_date']}
        
        Output must be strict JSON with this exact schema:
        {{
            "estimated_cost": <number, total estimated cost>,
            "cost_breakdown": {{
                "Materials": <number>,
                "Labor": <number>,
                "Machinery": <number>,
                "Permits/Other": <number>
            }},
            "project_summary": "<string, 2-3 sentence executive summary of the project scope, cost, and timeline>",
            "suggestions": {{
                "cost": "<string, specific cost-saving tip>",
                "schedule": "<string, specific scheduling advice>",
                "resource": "<string, specific resource allocation advice>"
            }},
            "resource_allocation": [
                {{ "item": "<string, name of resource>", "quantity": "<string, amount needed>", "unit_cost": "<string, cost per unit>" }}
            ]
        }}
        
        Ensure the output is valid JSON. Do not include markdown formatting like ```json. Just return the raw JSON string.
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful AI construction assistant that outputs strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )

        # Parse Response
        response_content = completion.choices[0].message.content
        # robustly clean json string just in case
        response_content = response_content.replace("```json", "").replace("```", "").strip()
        data = json.loads(response_content)
        
        return data

    except Exception as e:
        st.error(f"AI Generation Failed: {e}. Falling back to rapid estimation...")
        # Fallback Mock Logic
        import time
        time.sleep(1) 
        
        area = project_details.get('area', 1000)
        base_cost = 1500 if project_details['type'] == 'Residential' else 2200
        estimated_cost = area * base_cost
        
        return {
            "estimated_cost": estimated_cost,
            "cost_breakdown": {
                "Materials": estimated_cost * 0.5,
                "Labor": estimated_cost * 0.3,
                "Machinery": estimated_cost * 0.15,
                "Permits/Other": estimated_cost * 0.05
            },
            "project_summary": f"Estimated construction of {project_details['type']} ({project_details.get('subtype', 'General')}) project covering {area} sq. ft. Total estimated cost is ${estimated_cost:,.2f} with a timeline of {project_details['duration']} months.",
            "suggestions": {
                "cost": "Fallback: Switch to prefabricated panels to save 15%.",
                "schedule": "Fallback: Parallelize electrical and plumbing.",
                "resource": "Fallback: Secure labor early."
            },
            "resource_allocation": [
                { "item": "Project Manager", "quantity": "1", "unit_cost": "$5,000/mo" },
                { "item": "Skilled Laborers", "quantity": "5", "unit_cost": "$200/day" },
                { "item": "Concrete Mix", "quantity": "50 tons", "unit_cost": "$100/ton" },
                { "item": "Steel Reinforcement", "quantity": "5 tons", "unit_cost": "$800/ton" }
            ]
        }

# --- AI Blueprint Generation (Hugging Face) ---
HF_API_KEY = "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"
hf_client = InferenceClient(token=HF_API_KEY)

# Ensure blueprints directory exists
BLUEPRINTS_DIR = os.path.join(DATA_DIR, "blueprints")
os.makedirs(BLUEPRINTS_DIR, exist_ok=True)

def generate_blueprint_image(area, project_type, project_subtype="General", variant=1):
    """
    Generate AI-powered architectural floor plan using Stable Diffusion XL.
    Returns path to saved image or None on failure.
    """
    try:
        # Create unique cache key
        cache_key = hashlib.md5(f"{area}_{project_type}_{project_subtype}_{variant}".encode()).hexdigest()
        image_path = os.path.join(BLUEPRINTS_DIR, f"blueprint_{cache_key}.png")
        
        # Check if already generated
        if os.path.exists(image_path):
            return image_path
        
        # Craft detailed prompt based on project type and subtype
        base_prompt = f"professional architectural floor plan, {project_type} building, specifically {project_subtype}, {area} square feet, top-down view, clean technical drawing, blueprint style, labeled rooms, precise lines, architectural diagram, white background"
        
        # Add variety for different variants
        if variant == 1:
            prompt = base_prompt + ", traditional layout, symmetrical design"
        elif variant == 2:
            prompt = base_prompt + ", modern open floor plan, asymmetrical layout"
        else:
            prompt = base_prompt + ", innovative layout, creative space utilization"
        
        negative_prompt = "3d render, perspective view, people, furniture, decorations, colors, photorealistic, exterior, elevation view, blurry, low quality"
        
        # Generate image using Stable Diffusion XL
        image = hf_client.text_to_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            model="stabilityai/stable-diffusion-xl-base-1.0",
            width=768,
            height=768,
        )
        
        # Save image
        image.save(image_path)
        return image_path
        
    except Exception as e:
        st.warning(f"AI Blueprint generation failed for variant {variant}: {e}")
        return None

# --- Blueprint Generation (Fallback Plotly) ---
def generate_blueprint(area, project_type, seed=None):
    # Create a simplified mock floor plan using Plotly Shapes
    # Logic: Divide area into randomized "rooms"
    
    if seed:
        random.seed(seed)
    
    # Determine canvas size roughly by sqrt of area
    side = int(area**0.5)
    
    fig = go.Figure()

    # Outer wall - Darker but thinner line for precision look
    fig.add_shape(type="rect", x0=0, y0=0, x1=side, y1=side,
        line=dict(color="#1E3A5F", width=3), fillcolor="rgba(0,0,0,0)")

    # Generate some random interior rooms
    # This is a visual Mock-up, not a real architectural algorithm
    
    # Subtler, more desaturated colors for professional blueprint look
    colors = ["#E8EEF2", "#F2F0EB", "#EBF2EB", "#F2EBEF"]
    random.shuffle(colors) # Shuffle colors for variety between options
    
    # Entrance
    fig.add_annotation(x=side/2, y=0, text="Entrance", showarrow=True, arrowhead=2, arrowcolor="#888888",
                       font=dict(color="#888888", size=10))
    
    # Randomized Layout Logic (Simplified)
    # Option 1: Standard layout (as before)
    # Option 2: Flipped layout
    # Option 3: Different ratios
    
    variant = random.randint(1, 3)
    
    room_config = []
    
    if variant == 1:
        room_config = [
            {"name": "Main Hall", "x0": 0, "y0": 0, "x1": 0.6, "y1": 0.5},
            {"name": "Office", "x0": 0.6, "y0": 0, "x1": 1.0, "y1": 0.4},
            {"name": "Utility", "x0": 0, "y0": 0.5, "x1": 0.5, "y1": 1.0},
            {"name": f"{project_type} Zone", "x0": 0.5, "y0": 0.5, "x1": 1.0, "y1": 1.0}
        ]
    elif variant == 2:
        room_config = [
            {"name": "Lobby", "x0": 0.2, "y0": 0, "x1": 0.8, "y1": 0.3},
            {"name": "Main Hall", "x0": 0, "y0": 0.3, "x1": 0.7, "y1": 1.0},
            {"name": "Storage", "x0": 0.7, "y0": 0.3, "x1": 1.0, "y1": 0.7},
            {"name": "Office", "x0": 0.7, "y0": 0.7, "x1": 1.0, "y1": 1.0}
        ]
    else:
        room_config = [
            {"name": "Reception", "x0": 0, "y0": 0, "x1": 0.4, "y1": 0.4},
            {"name": "Corridor", "x0": 0.4, "y0": 0, "x1": 0.6, "y1": 1.0},
            {"name": "Conf Room", "x0": 0.6, "y0": 0, "x1": 1.0, "y1": 0.5},
            {"name": "Workspace", "x0": 0, "y0": 0.4, "x1": 0.4, "y1": 1.0},
            {"name": "Utility", "x0": 0.6, "y0": 0.5, "x1": 1.0, "y1": 1.0}
        ]

    for i, room in enumerate(room_config):
        color = colors[i % len(colors)]
        r_x0 = side * room["x0"]
        r_y0 = side * room["y0"]
        r_x1 = side * room["x1"]
        r_y1 = side * room["y1"]
        
        fig.add_shape(type="rect", 
            x0=r_x0, y0=r_y0, 
            x1=r_x1, y1=r_y1,
            line=dict(color="#B0BCC9", width=1),
            fillcolor=color, opacity=0.6
        )
        
        # Center of room text
        cx = (r_x0 + r_x1) / 2
        cy = (r_y0 + r_y1) / 2
        fig.add_annotation(x=cx, y=cy, text=room["name"], showarrow=False,
                           font=dict(color="#555555", size=10, weight="bold"))

    fig.update_xaxes(range=[-5, side+5], showgrid=False, zeroline=False, visible=False)
    fig.update_yaxes(range=[-5, side+5], showgrid=False, zeroline=False, visible=False)
    
    fig.update_layout(
        title={
            'text': f"Layout Option {random.randint(100,999)}",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(color="#0F2A44", size=16)
        },
        plot_bgcolor="white",
        width=600, height=600,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig



# --- Pages ---

def home_page():
    load_css()
    
    # Navbar
    auth_buttons = """
        <span style="margin-left: 20px; cursor: pointer;" onclick="document.dispatchEvent(new CustomEvent('login_click'))">Login</span>
        <span style="margin-left: 20px; cursor: pointer;" onclick="document.dispatchEvent(new CustomEvent('register_click'))">Register</span>
    """
    
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
         st.markdown('<div class="nav-logo">🏗️ BuildWise AI</div>', unsafe_allow_html=True)
    with col_nav2:
        # Streamlit buttons for navigation since JS injection is tricky for state
        # Using columns to align right
        c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
        with c2:
            if st.button("Login"):
                navigate_to("login")
        with c3:
            if st.button("Register"):
                navigate_to("register")

    # Hero Section
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown('<div class="hero-section">', unsafe_allow_html=True)
        st.markdown('<h1 class="hero-title">AI-Based Construction<br>Planning System</h1>', unsafe_allow_html=True)
        st.markdown("""
            <p class="hero-subtitle">
                Revolutionize your construction projects with AI-driven insights. 
                Get accurate cost estimates, optimized schedules, and smart resource allocation.
            </p>
        """, unsafe_allow_html=True)
        
        if st.button("Get Started 🚀", type="primary"):
            if st.session_state.user:
                navigate_to('dashboard')
            else:
                navigate_to('login')
            
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div style="display: flex; justify-content: center; align-items: center; height: 100%; padding: 2rem;">
                <div style="background: white; padding: 2rem; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.1);">
                    <div style="font-size: 100px; text-align: center;">📊 🏗️ 🤖</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Features
    st.markdown("---")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown('<div class="feature-card"><div class="feature-icon">💰</div><h3>Accurate Cost Estimates</h3></div>', unsafe_allow_html=True)
    with f2:
        st.markdown('<div class="feature-card"><div class="feature-icon">📅</div><h3>Optimized Schedules</h3></div>', unsafe_allow_html=True)
    with f3:
        st.markdown('<div class="feature-card"><div class="feature-icon">🚜</div><h3>Smart Resource Planning</h3></div>', unsafe_allow_html=True)


def login_register_page(mode="login"):
    load_css()
    
    # Centered Container
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown(f"## {mode.capitalize()}")
        st.markdown('<div class="auth-form">', unsafe_allow_html=True)
        
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if mode == "register":
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            if st.button("Register Now"):
                if username and password and name:
                    success, msg = register_user(username, password, name, email)
                    if success:
                        st.success(msg)
                        st.info("Directing to login...")
                        navigate_to("login")
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill all fields.")
            
            if st.button("Already have an account? Login"):
                navigate_to("login")
                
        else: # Login
            if st.button("Login"):
                success, name = authenticate_user(username, password)
                if success:
                    st.session_state.user = name
                    st.session_state.username = username
                    st.success(f"Welcome back, {name}!")
                    navigate_to("dashboard")
                else:
                    st.error("Invalid username or password.")
            
            if st.button("New user? Register"):
                navigate_to("register")
        
        st.markdown('</div>', unsafe_allow_html=True)

def dashboard_page():
    load_css()
    
    # Header
    col_head1, col_head2 = st.columns([3, 1])
    with col_head1:
        st.markdown('<div class="nav-logo">🏗️ BuildWise AI - Dashboard</div>', unsafe_allow_html=True)
    with col_head2:
        st.markdown(f'<span class="nav-user">👤 {st.session_state.user}</span>', unsafe_allow_html=True)
        if st.button("Logout"):
            logout()

    st.markdown("---")

    # Main Layout
    sidebar, content = st.columns([1, 2.5])
    
    with sidebar:
        # Navigation
        st.markdown("### 🧭 Navigation")
        if st.button("🏠 Home", use_container_width=True):
            navigate_to('home')
        if st.button("🗄️ My Projects", use_container_width=True):
            navigate_to('saved_projects')
        
        st.divider()

        st.markdown("### 📝 Project Details")
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        
        project_name = st.text_input("Project Name", "New Residential Tower")
        project_type = st.selectbox("Project Type", ["Residential", "Commercial", "Industrial"])
        
        # Define subtypes for each project type
        subtypes = {
            "Residential": [
                "Independent house",
                "Duplex house",
                "Gated community",
                "Hostel / PG accommodation",
                "Dormitory"
            ],
            "Commercial": [
                "Office building/software park",
                "Shopping mall",
                "Retail store",
                "Hotel",
                "Restaurant",
                "Financial institution"
            ],
            "Industrial": [
                "Manufacturing unit",
                "Warehouse",
                "Power plant",
                "Refinery",
                "Cold storage",
                "Assembly plant",
                "Research & development (R&D) facility",
                "Logistics center"
            ]
        }
        
        # Show subtype dropdown based on selected project type
        project_subtype = st.selectbox("Project Subtype", subtypes[project_type])
        
        location = st.text_input("Location", "New York, NY")
        area = st.number_input("Total Area (sq. ft)", min_value=500, value=2500, step=100)
        
        # Building dimensions
        col_dim1, col_dim2 = st.columns(2)
        with col_dim1:
            length = st.number_input("Length (ft)", min_value=10, value=50, step=5)
        with col_dim2:
            width = st.number_input("Width (ft)", min_value=10, value=50, step=5)
        
        floors = st.number_input("Number of Floors", min_value=1, max_value=100, value=1, step=1)
        
        budget = st.number_input("Budget ($)", min_value=10000, value=500000, step=10000)
        duration = st.slider("Expected Duration (Months)", 1, 36, 12)
        start_date = st.date_input("Start Date", datetime.now())
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✨ Generate", type="primary"):
                st.session_state.project_inputs = {
                    "name": project_name,
                    "type": project_type,
                    "subtype": project_subtype,
                    "location": location,
                    "area": area,
                    "length": length,
                    "width": width,
                    "floors": floors,
                    "budget": budget,
                    "duration": duration,
                    "start_date": str(start_date)
                }
                st.session_state.plan_results = generate_plan(st.session_state.project_inputs)
                # Generate 3 AI blueprint images with loading spinner
                with st.spinner("🎨 Generating AI blueprints... This may take 15-30 seconds..."):
                    blueprint_paths = []
                    for i in range(1, 4):
                        img_path = generate_blueprint_image(area, project_type, project_subtype, variant=i)
                        if img_path:
                            blueprint_paths.append(img_path)
                        else:
                            # Fallback to Plotly if AI fails
                            blueprint_paths.append(generate_blueprint(area, project_type, seed=random.randint(1000*i, 1000*(i+1))))
                    st.session_state.blueprints = blueprint_paths
        
        with col_btn2:
            if st.button("Reset"):
                if 'plan_results' in st.session_state:
                    del st.session_state.plan_results
                if 'blueprints' in st.session_state:
                    del st.session_state.blueprints
                st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

    with content:
        if 'plan_results' in st.session_state:
            render_project_view(
                st.session_state.plan_results, 
                st.session_state.project_inputs, 
                st.session_state.get('blueprints')
            )
        else:
            st.info("👈 Enter project details and click 'Generate' to see the AI Plan & Blueprint.")
            st.markdown("""
                <div style="text-align: center; color: #bdbdbd; margin-top: 50px;">
                    <h2>Welcome to your Dashboard</h2>
                    <p>Start a new project from the sidebar.</p>
                </div>
            """, unsafe_allow_html=True)

def render_project_view(results, project_inputs, blueprints=None, show_save=True):
    """
    Helper function to render the project results (Summary, Charts, Blueprints).
    Used by both Dashboard (live) and Saved Projects (history).
    """
    # Top Stats & Summary Section
    st.markdown("### 📋 Plan Summary")
    
    sum_col1, sum_col2 = st.columns([3, 1])
    
    with sum_col1:
        if "project_summary" in results:
            st.info(f"**Project Overview:** {results['project_summary']}")
        else:
            st.info(f"**Project Overview:** Estimated construction of {project_inputs['type']} project covering {project_inputs['area']} sq. ft. over {project_inputs['duration']} months.")

    with sum_col2:
        if show_save:
            st.markdown("<br>", unsafe_allow_html=True) # Spacer for alignment
            if st.button("💾 Save Project", use_container_width=True, key="save_current_project_btn"):
                project_data = {
                    "id": str(uuid.uuid4()),
                    "user": st.session_state.username,
                    "timestamp": str(datetime.now()),
                    "inputs": project_inputs,
                    "results": results,
                    "blueprints": st.session_state.get('blueprints', [])
                }
                save_project_to_db(project_data)
                st.success("Saved!")

    st.divider()

    # Tabs for View
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📅 Schedule", "📐 Blueprints"])

    with tab1:
        # Top Stats
        r1, r2, r3 = st.columns(3)
        r1.metric("Estimated Cost", f"${results['estimated_cost']:,.0f}", "Within Budget")
        r2.metric("Duration", f"{project_inputs['duration']} Months", "On Track")
        r3.metric("Confidence", "94%", "High")

        # Cost Chart
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### Cost Breakdown")
            df_cost = pd.DataFrame(list(results['cost_breakdown'].items()), columns=['Category', 'Cost'])
            fig_cost = px.pie(df_cost, values='Cost', names='Category', hole=0.4)
            st.plotly_chart(fig_cost, use_container_width=True)
        with c2:
            st.markdown("### 🛠️ Resource Allocation")
            if "resource_allocation" in results:
                st.dataframe(results["resource_allocation"], hide_index=True, use_container_width=True)
            else:
                st.warning("Detailed resource data not available for this plan.")

            st.markdown("### 💡 AI Suggestions")
            st.info(f"**Cost:** {results['suggestions']['cost']}")
            st.info(f"**Resource:** {results['suggestions']['resource']}")

    with tab2:
        st.markdown("### Construction Timeline")
        start = datetime.strptime(project_inputs['start_date'], "%Y-%m-%d")
        duration_days = project_inputs['duration'] * 30
        phases = [
            dict(Task="Planning", Start=start, Finish=start + timedelta(days=duration_days*0.1)),
            dict(Task="Foundation", Start=start + timedelta(days=duration_days*0.1), Finish=start + timedelta(days=duration_days*0.3)),
            dict(Task="Structure", Start=start + timedelta(days=duration_days*0.3), Finish=start + timedelta(days=duration_days*0.6)),
            dict(Task="Finishing", Start=start + timedelta(days=duration_days*0.6), Finish=start + timedelta(days=duration_days))
        ]
        df_gantt = pd.DataFrame(phases)
        fig_gantt = px.timeline(df_gantt, x_start="Start", x_end="Finish", y="Task", color="Task")
        st.plotly_chart(fig_gantt, use_container_width=True)
        st.info(results["suggestions"]["schedule"])
    
    with tab3:
        st.markdown("### 🏠 Architectural Blueprints (AI Generated)")
        st.markdown("Here are the architectural layouts for this plan.")
        
        bp_tab1, bp_tab2, bp_tab3 = st.tabs(["Option A", "Option B", "Option C"])
        
        # blueprints arg can be passed, or fall back to session state if None (for backwards compat)
        current_blueprints = blueprints if blueprints is not None else st.session_state.get('blueprints', [])
        
        if current_blueprints:
            # Helper to display blueprint safely
            def display_bp(bp, caption):
                if isinstance(bp, str):
                    if os.path.exists(bp):
                        st.image(bp, caption=caption, use_container_width=True)
                    else:
                        st.error(f"Image not found: {bp}")
                else:
                    st.plotly_chart(bp, use_container_width=True)

            with bp_tab1:
                if len(current_blueprints) > 0: display_bp(current_blueprints[0], "Option A")
            with bp_tab2:
                if len(current_blueprints) > 1: display_bp(current_blueprints[1], "Option B")
            with bp_tab3:
                if len(current_blueprints) > 2: display_bp(current_blueprints[2], "Option C")
        else:
            st.warning("No blueprints available for this plan.")
        
        st.caption("Note: These are conceptual layouts.")

def saved_projects_page():
    st.title("🗄️ My Saved Projects")
    
    projects = load_projects()
    # Filter for current user
    user_projects = [p for p in projects if p.get('user') == st.session_state.username]
    
    if not user_projects:
        st.info("You haven't saved any projects yet. Go to the **Dashboard** to create one!")
        return

    # Sort by timestamp descending
    user_projects.sort(key=lambda x: x['timestamp'], reverse=True)

    # Master-Detail view
    if 'selected_project_id' not in st.session_state:
        st.session_state.selected_project_id = None

    if st.session_state.selected_project_id:
        # Show Back button and Detail View
        if st.button("← Back to List"):
            st.session_state.selected_project_id = None
            st.rerun()
        
        # Find the selected project
        project = next((p for p in user_projects if p['id'] == st.session_state.selected_project_id), None)
        if project:
            st.markdown(f"## 🏗️ {project['inputs']['name']}")
            st.caption(f"Saved on: {project['timestamp']}")
            
            # Use the shared render function
            render_project_view(
                results=project['results'], 
                project_inputs=project['inputs'], 
                blueprints=project.get('blueprints', []),
                show_save=False
            )
        else:
            st.error("Project not found.")
            st.session_state.selected_project_id = None
            st.rerun()
            
    else:
        # List View
        for project in user_projects:
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 1.5, 1])
                with c1:
                    st.subheader(project['inputs']['name'])
                    st.caption(f"Type: {project['inputs']['type']}")
                with c2:
                    st.write(f"**Date:** {project['timestamp'][:10]}")
                with c3:
                    st.write(f"**Cost:** ${project['results']['estimated_cost']:,.0f}")
                with c4:
                    st.write(f"**Area:** {project['inputs']['area']} sq.ft")
                with c5:
                    if st.button("View", key=f"view_{project['id']}"):
                        st.session_state.selected_project_id = project['id']
                        st.rerun()
                st.divider()


# --- Main Controller ---
def main():
    if st.session_state.page == 'home':
        home_page()
    elif st.session_state.page == 'login':
        login_register_page("login")
    elif st.session_state.page == 'register':
        login_register_page("register")
    elif st.session_state.page == 'dashboard':
        if st.session_state.user:
            dashboard_page()
        else:
            navigate_to('login')
    elif st.session_state.page == 'saved_projects':
        if st.session_state.user:
            # Navigation Sidebar
            with st.sidebar:
                st.markdown(f"### Welcome, {st.session_state.user}!")
                if st.button("🚪 Logout"):
                    st.session_state.user = None
                    navigate_to('home')
                st.divider()
                if st.button("🏠 Home", use_container_width=True):
                    navigate_to('home')
                if st.button("🏗️ Dashboard", use_container_width=True):
                    navigate_to('dashboard')
                if st.button("🗄️ My Projects", use_container_width=True, type="primary"):
                    pass # Already here
            
            saved_projects_page()
        else:
            navigate_to('login')

if __name__ == "__main__":
    ensure_data_dir()
    main()
