import streamlit as st
import requests
import time

# ✅ CHANGE THIS TO YOUR RENDER BACKEND URL AFTER DEPLOYMENT
# For local testing: http://localhost:8000
# For deployed backend: https://your-backend.onrender.com
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Police Rulebook Assistant",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark Theme CSS
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0f1119 100%); }
    .main-header { text-align: center; padding: 2rem; background: linear-gradient(135deg, #0a0e1a 0%, #1a1f2e 100%); border-radius: 20px; margin-bottom: 2rem; border: 1px solid #21262d; position: relative; overflow: hidden; }
    .main-header::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #dc2626, #10b981, #dc2626); }
    .main-header h1 { font-size: 2.2rem; font-weight: 700; margin-bottom: 0.5rem; background: linear-gradient(135deg, #fff 0%, #dc2626 50%, #10b981 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .main-header p { font-size: 0.95rem; color: #8b949e; }
    div[data-testid="stChatMessage"][data-testid*="user"] { background: linear-gradient(135deg, #1a0f0f 0%, #1f1414 100%); border: 1px solid rgba(220,38,38,0.3); color: #f0f0f0 !important; border-radius: 20px 20px 5px 20px; }
    div[data-testid="stChatMessage"][data-testid*="assistant"] { background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%); border: 1px solid rgba(16,185,129,0.3); border-radius: 20px 20px 20px 5px; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0a0e1a 0%, #0d1117 100%); border-right: 1px solid #21262d; }
    .stat-card-red { background: #131823; border-radius: 15px; padding: 1rem; margin: 0.8rem 0; text-align: center; border: 1px solid rgba(220,38,38,0.3); }
    .stat-card-green { background: #131823; border-radius: 15px; padding: 1rem; margin: 0.8rem 0; text-align: center; border: 1px solid rgba(16,185,129,0.3); }
    .stat-number-red { font-size: 2rem; font-weight: 700; color: #dc2626; }
    .stat-number-green { font-size: 2rem; font-weight: 700; color: #10b981; }
    .stat-label { font-size: 0.7rem; color: #8b949e; margin-top: 0.3rem; }
    .doc-badge { background: rgba(16,185,129,0.15); color: #10b981; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; margin: 0.25rem; }
    .stButton button { background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; border: none; border-radius: 10px; padding: 0.5rem 1rem; font-weight: 600; width: 100%; transition: all 0.3s ease; }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(220,38,38,0.4); }
    .answer-section { background: linear-gradient(135deg, #0f1a14 0%, #0d1f18 100%); padding: 1.5rem; border-radius: 15px; margin: 0.5rem 0; line-height: 1.8; border-left: 4px solid #10b981; color: #e6edf3; font-size: 1rem; }
    .footer { text-align: center; padding: 1.5rem; color: #8b949e; font-size: 0.75rem; border-top: 1px solid #21262d; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>Complete Legal Reference for IPC, CrPC, Cyber Laws & Police Procedures</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_connected" not in st.session_state:
    st.session_state.api_connected = False

# Check API connection
def check_api():
    try:
        response = requests.get(f"{API_URL}/", timeout=3)
        if response.status_code == 200:
            st.session_state.api_connected = True
            return True
    except:
        st.session_state.api_connected = False
    return False

# Sidebar
with st.sidebar:
    st.markdown("## 🎯 Knowledge Dashboard")
    
    # Check API status
    api_status = check_api()
    
    if api_status:
        try:
            status = requests.get(f"{API_URL}/status", timeout=5).json()
            st.markdown(f"""
            <div class="stat-card-red">
                <div class="stat-number-red">{status.get('documents_loaded', 0)}</div>
                <div class="stat-label">Documents Loaded</div>
            </div>
            <div class="stat-card-green">
                <div class="stat-number-green">{status.get('chunks', 0)}</div>
                <div class="stat-label">Text Chunks</div>
            </div>
            """, unsafe_allow_html=True)
            
            if status.get('pdfs'):
                st.markdown("### 📚 Document Library")
                for doc in status.get('pdfs', [])[:5]:
                    short_name = doc[:35] + "..." if len(doc) > 35 else doc
                    st.markdown(f'<span class="doc-badge">📄 {short_name}</span>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Status error: {e}")
    else:
        st.warning("⚠️ Backend Not Connected")
        st.info(f"Make sure backend is running at: {API_URL}")
    
    st.markdown("---")
    
    if st.button("🔄 Refresh Knowledge Base", use_container_width=True):
        if api_status:
            with st.spinner("Refreshing documents from GitHub..."):
                try:
                    response = requests.post(f"{API_URL}/refresh", timeout=30)
                    if response.status_code == 200:
                        st.success("✅ Knowledge base refreshed!")
                        st.rerun()
                    else:
                        st.error("Refresh failed")
                except:
                    st.error("Cannot connect to backend")
        else:
            st.error("Backend not connected")
    
    st.markdown("---")
    
    st.markdown("### 💡 Quick IPC References")
    st.markdown("""
    | Section | Offence | Punishment |
    |---------|---------|------------|
    | 302 | Murder | Death/Life imprisonment |
    | 376 | Rape | 10 years to life |
    | 379 | Theft | 3 years imprisonment |
    | 392 | Robbery | 10 years imprisonment |
    | 420 | Cheating | 7 years imprisonment |
    | 304B | Dowry Death | 7 years to life |
    | 363 | Kidnapping | 7 years imprisonment |
    | 406 | Breach of Trust | 3 years imprisonment |
    | 500 | Defamation | 2 years imprisonment |
    """)
    
    st.markdown("---")
    
    if not api_status:
        st.info("💡 **How to start locally:**\n\n```bash\npython -m uvicorn backend:app --reload --port 8000\n```\n```bash\nstreamlit run app.py\n```")

# Main chat area
st.markdown("## 💬 Ask Legal Questions")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
prompt = st.chat_input("Ask about IPC sections, punishments, legal procedures...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        if not st.session_state.api_connected:
            response = "⚠️ Backend not connected.\n\n**To fix this:**\n1. Make sure FastAPI is running: `python -m uvicorn backend:app --reload --port 8000`\n2. Check the URL in `API_URL` variable matches your backend."
            st.markdown(response)
        else:
            with st.spinner("🔍 Searching through legal documents..."):
                try:
                    api_response = requests.post(f"{API_URL}/ask", json={"query": prompt}, timeout=30)
                    
                    if api_response.status_code == 200:
                        result = api_response.json()
                        answer = result.get("answer", "No answer found.")
                        st.markdown(f'<div class="answer-section">{answer}</div>', unsafe_allow_html=True)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        st.error(f"API Error: {api_response.status_code}")
                        
                except requests.exceptions.ConnectionError:
                    st.error(f"Cannot connect to backend at {API_URL}")
                except requests.exceptions.Timeout:
                    st.error("Request timed out. Backend might be waking up (cold start). Try again.")
                except Exception as e:
                    st.error(f"Error: {str(e)[:200]}")

# Footer
st.markdown("""
<div class="footer">
    👮 Police Rulebook Assistant | Project PRJ-005 | Barath R K PDKV | 411623149004
</div>
""", unsafe_allow_html=True)
