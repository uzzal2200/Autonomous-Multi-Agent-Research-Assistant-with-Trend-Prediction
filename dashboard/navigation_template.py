import streamlit as st

# ── 1. SESSION STATE INITIALIZATION ────────────────────────────────
# Always initialize state keys at the very beginning of the app script
if "nav_state" not in st.session_state:
    st.session_state.nav_state = "🏠 Home"

# ── 2. CALLBACKS FOR NAVIGATION ─────────────────────────────────────
# This is the "Safe" way to update session_state.
# Callbacks are executed BEFORE the script body re-runs.
def navigate_to(page_name):
    st.session_state.nav_state = page_name

# ── 3. PAGE CONFIG & STYLES ─────────────────────────────────────────
st.set_page_config(page_title="SafeNav Dashboard ", layout="wide", page_icon="🚀")

# Premium UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter:wght@400;500&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #050505;
        color: #e2e8f0;
    }
    .main-header {
        font-family: 'Outfit', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }
    .nav-card {
        transition: all 0.3s ease;
        cursor: pointer;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.02);
    }
    .nav-card:hover {
        border-color: #6366f1;
        background: rgba(99, 102, 241, 0.05);
        transform: translateY(-5px);
    }
</style>
""", unsafe_allow_html=True)

# ── 4. SIDEBAR NAVIGATION ──────────────────────────────────────────
with st.sidebar:
    st.title("🚀 Navigation")
    
    # Use the session_state key directly in the radio widget.
    # Note: We provide 'on_change' if we need extra logic, but here 
    # letting Streamlit handle the key binding 'nav_state' is safe 
    # as long as we don't try to change it manually later in the script.
    
    options = ["🏠 Home", "🔎 Smart Paper Search", "📊 Reports", "⚙️ Settings"]
    
    # We display the radio but bind it to our session_state key.
    # To handle manual overrides (like clicking a button on the home page),
    # we use the callback pattern.
    
    st.radio(
        "Select Page",
        options,
        key="nav_state",  # This ensures the widget always reflects st.session_state.nav_state
        label_visibility="collapsed"
    )

# ── 5. PAGE RENDERING LOGIC ───────────────────────────────────────
current_page = st.session_state.nav_state

if current_page == "🏠 Home":
    st.markdown('<h1 class="main-header">Welcome to ResearchAI</h1>', unsafe_allow_html=True)
    st.write("Your premium research command center.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="nav-card"><h3>🔎 Search</h3><p>Find papers instantly</p></div>', unsafe_allow_html=True)
        if st.button("Open Search", key="btn_search", use_container_width=True):
            navigate_to("🔎 Smart Paper Search")
            st.rerun()
            
    with col2:
        st.markdown('<div class="nav-card"><h3>📊 Reports</h3><p>Analyze insights</p></div>', unsafe_allow_html=True)
        if st.button("View Reports", key="btn_reports", use_container_width=True):
            navigate_to("📊 Reports")
            st.rerun()
            
    with col3:
        st.markdown('<div class="nav-card"><h3>⚙️ Settings</h3><p>Configure AI</p></div>', unsafe_allow_html=True)
        if st.button("System Settings", key="btn_settings", use_container_width=True):
            navigate_to("⚙️ Settings")
            st.rerun()

elif current_page == "🔎 Smart Paper Search":
    st.markdown('<h1 class="main-header">🔎 Smart Paper Search</h1>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    query = st.text_input("Enter research topic", placeholder="e.g. Quantum Computing, Climate Change...")
    if st.button("Run Deep Search", type="primary"):
        st.info(f"Searching for researchers and papers related to: {query}")
        st.spinner("Analyzing citation networks...")
    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "📊 Reports":
    st.markdown('<h1 class="main-header">📊 Research Reports</h1>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.write("Summary statistics and trend analysis.")
    st.metric("Total Papers", "1,240", "+12 today")
    st.metric("Key Insights", "42", "+3 this week")
    st.markdown('</div>', unsafe_allow_html=True)

elif current_page == "⚙️ Settings":
    st.markdown('<h1 class="main-header">⚙️ System Settings</h1>', unsafe_allow_html=True)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.checkbox("Enable Deep Thinking Mode")
    st.checkbox("Auto-summarize new papers")
    st.slider("AI Confidence Threshold", 0.0, 1.0, 0.85)
    st.markdown('</div>', unsafe_allow_html=True)

# ── 6. GLOBAL FOOTER ──────────────────────────────────────────────
st.markdown("---")
st.caption("Safe Navigation Template • Premium SaaS Aesthetic")
