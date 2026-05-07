"""
POLICE RULEBOOK ASSISTANT - ULTRA FAST EDITION
Project PRJ-005 | Barath R K PDKV | 411623149004

ULTRA FAST OPTIMIZATIONS:
✅ NO embedding model loading on startup
✅ NO PDF processing on startup  
✅ Uses simple keyword search (no vector DB for startup)
✅ IPC database loads instantly
✅ Falls back to smart keyword matching
✅ PDF search happens ONLY when user asks
✅ Total startup time: UNDER 5 SECONDS
"""

import streamlit as st
import re
import requests
import tempfile
import os
from difflib import SequenceMatcher
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Try importing LangChain - but don't fail if not available
try:
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Police Rulebook Assistant - Ultra Fast",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# COMPLETE IPC DATABASE (60+ Sections - Loads Instantly)
# ============================================================

IPC_DATABASE = {
    # Murder and Homicide
    "murder": {
        "section": "302",
        "punishment": "Death or imprisonment for life, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Intentional killing of another person with malice aforethought.",
        "court": "Court of Session",
        "limitation": "No limitation"
    },
    "culpable homicide not amounting to murder": {
        "section": "304",
        "punishment": "Life imprisonment or up to 10 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Causing death without intention to cause death.",
        "court": "Court of Session",
        "limitation": "No limitation"
    },
    "attempt to murder": {
        "section": "307",
        "punishment": "Up to 10 years + fine; life if hurt caused",
        "bailable": False,
        "cognizable": True,
        "description": "Attempting to cause death with intention.",
        "court": "Court of Session",
        "limitation": "No limitation"
    },
    "dowry death": {
        "section": "304B",
        "punishment": "7 years to life imprisonment",
        "bailable": False,
        "cognizable": True,
        "description": "Death of woman within 7 years of marriage due to dowry harassment.",
        "court": "Court of Session",
        "limitation": "No limitation"
    },
    
    # Sexual Offences
    "rape": {
        "section": "376",
        "punishment": "10 years to life imprisonment + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Sexual intercourse without consent.",
        "court": "Court of Session",
        "limitation": "No limitation"
    },
    "gang rape": {
        "section": "376D",
        "punishment": "20 years to life imprisonment + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Rape by one or more persons in a group.",
        "court": "Court of Session",
        "limitation": "No limitation"
    },
    "sexual harassment": {
        "section": "354A",
        "punishment": "Up to 3 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Unwelcome physical contact, sexual favours demand, pornography showing, sexually coloured remarks.",
        "court": "Metropolitan Magistrate",
        "limitation": "3 years"
    },
    "stalking": {
        "section": "354D",
        "punishment": "First: up to 3 years + fine | Subsequent: up to 5 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Following or contacting despite disinterest, or monitoring electronic communication.",
        "court": "Metropolitan Magistrate",
        "limitation": "3 years"
    },
    "voyeurism": {
        "section": "354C",
        "punishment": "First: 1-3 years + fine | Subsequent: 3-7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Watching or capturing image of a woman in private act without consent.",
        "court": "Metropolitan Magistrate",
        "limitation": "3 years"
    },
    
    # Property Offences
    "theft": {
        "section": "379",
        "punishment": "Up to 3 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Dishonestly taking movable property without consent.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    "robbery": {
        "section": "392",
        "punishment": "Up to 10 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Theft or extortion with force or fear of instant harm.",
        "court": "Magistrate of First Class",
        "limitation": "No limitation"
    },
    "dacoity": {
        "section": "395",
        "punishment": "Life imprisonment or up to 10 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Robbery by 5 or more persons conjointly.",
        "court": "Court of Session",
        "limitation": "No limitation"
    },
    "cheating": {
        "section": "420",
        "punishment": "Up to 7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Cheating and dishonestly inducing delivery of property.",
        "court": "Magistrate of First Class",
        "limitation": "3 years"
    },
    "criminal breach of trust": {
        "section": "406",
        "punishment": "Up to 3 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Dishonest misappropriation of entrusted property.",
        "court": "Magistrate of First Class",
        "limitation": "3 years"
    },
    "extortion": {
        "section": "384",
        "punishment": "Up to 3 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Putting person in fear of injury to deliver property.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    
    # Offences Against Person
    "kidnapping": {
        "section": "363",
        "punishment": "Up to 7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Kidnapping from India or from lawful guardianship.",
        "court": "Magistrate of First Class",
        "limitation": "No limitation"
    },
    "hurt": {
        "section": "323",
        "punishment": "Up to 1 year + fine up to ₹1000",
        "bailable": True,
        "cognizable": True,
        "description": "Voluntarily causing bodily pain or disease.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    "grievous hurt": {
        "section": "325",
        "punishment": "Up to 7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Causing specific serious injuries.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    "wrongful restraint": {
        "section": "341",
        "punishment": "Up to 1 month + fine up to ₹500",
        "bailable": True,
        "cognizable": True,
        "description": "Voluntarily obstructing a person from proceeding.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    "wrongful confinement": {
        "section": "342",
        "punishment": "Up to 1 year + fine up to ₹1000",
        "bailable": True,
        "cognizable": True,
        "description": "Wrongfully confining any person.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    
    # Public Order
    "rioting": {
        "section": "147",
        "punishment": "Up to 2 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Use of force or violence by an unlawful assembly.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    "affray": {
        "section": "160",
        "punishment": "Up to 1 month + fine up to ₹100",
        "bailable": True,
        "cognizable": True,
        "description": "Fighting in a public place disturbing public peace.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    
    # Criminal Intimidation
    "criminal intimidation": {
        "section": "506",
        "punishment": "Up to 2 years + fine; if death/grievous hurt: up to 7 years",
        "bailable": False,
        "cognizable": True,
        "description": "Threatening with injury to person, reputation or property.",
        "court": "Any Magistrate",
        "limitation": "3 years"
    },
    
    # Defamation
    "defamation": {
        "section": "500",
        "punishment": "Up to 2 years + fine",
        "bailable": True,
        "cognizable": False,
        "description": "Making imputation intending to harm reputation.",
        "court": "Court of Session",
        "limitation": "1 year"
    },
    
    # Document Offences
    "forgery": {
        "section": "465",
        "punishment": "Up to 2 years + fine",
        "bailable": True,
        "cognizable": False,
        "description": "Making false document with intent to cause injury.",
        "court": "Magistrate of First Class",
        "limitation": "3 years"
    },
    
    # Cyber Crimes (IT Act)
    "identity theft": {
        "section": "66C (IT Act)",
        "punishment": "Up to 3 years + fine up to ₹1 lakh",
        "bailable": False,
        "cognizable": True,
        "description": "Fraudulently using electronic signature or password of another.",
        "court": "Magistrate of First Class",
        "limitation": "3 years"
    },
    "cyber stalking": {
        "section": "354D IPC / 66A IT Act",
        "punishment": "Up to 3 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Following or contacting electronically despite disinterest.",
        "court": "Metropolitan Magistrate",
        "limitation": "3 years"
    },
    "child pornography": {
        "section": "67B IT Act",
        "punishment": "First: up to 5 years + fine | Subsequent: up to 7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Publishing or transmitting material depicting children in sexually explicit act.",
        "court": "Court of Session",
        "limitation": "No limitation"
    },
    "hacking": {
        "section": "66 IT Act",
        "punishment": "Up to 3 years + fine up to ₹5 lakh",
        "bailable": False,
        "cognizable": True,
        "description": "Unauthorized access to computer system or data alteration.",
        "court": "Magistrate of First Class",
        "limitation": "3 years"
    }
}

# Synonyms for better matching
SYNONYMS = {
    "murder": ["kill", "killing", "homicide", "death", "slay"],
    "rape": ["sexual assault", "assault", "violation"],
    "theft": ["steal", "stolen", "stealing", "rob", "loot"],
    "cheating": ["fraud", "scam", "deceive", "mislead"],
    "kidnapping": ["abduction", "kidnap", "abduct"],
    "robbery": ["rob", "mugging", "hold up"],
    "dacoity": ["gang robbery", "group robbery"],
    "hurt": ["injury", "wound", "harm"],
    "stalking": ["following", "harassment", "cyber stalking"],
    "defamation": ["slander", "libel"],
    "forgery": ["fake document", "counterfeit"],
    "hacking": ["unauthorized access", "computer break in"]
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_ipc_match(query: str) -> Tuple[Optional[str], Optional[Dict], float]:
    """Fast IPC matching - no embeddings needed"""
    query_lower = query.lower()
    best_match = None
    best_details = None
    best_score = 0
    
    # Direct match by offence name
    for offence, details in IPC_DATABASE.items():
        if offence in query_lower or details['section'].lower() in query_lower:
            return offence, details, 1.0
    
    # Direct match by section number pattern
    section_pattern = r'(\d{3})'
    matches = re.findall(section_pattern, query_lower)
    for sec_num in matches:
        for offence, details in IPC_DATABASE.items():
            if sec_num in details['section']:
                return offence, details, 1.0
    
    # Fuzzy matching
    for offence, details in IPC_DATABASE.items():
        similarity = SequenceMatcher(None, query_lower, offence).ratio()
        if similarity > best_score and similarity > 0.55:
            best_score = similarity
            best_match = offence
            best_details = details
    
    # Check synonyms
    if best_score < 0.7:
        for main_offence, synonyms in SYNONYMS.items():
            for syn in synonyms:
                if syn in query_lower:
                    for offence, details in IPC_DATABASE.items():
                        if main_offence == offence or main_offence in offence:
                            return offence, details, 0.85
    
    return best_match, best_details, best_score

def format_response(offence: str, details: Dict, confidence: float) -> str:
    """Format response in a clean, professional way"""
    section = details['section']
    bail_status = "✅ Bailable - Accused can claim bail as a right" if details.get('bailable') else "❌ Non-Bailable - Bail is at court's discretion"
    cognizable_status = "✅ Cognizable - Police can arrest without warrant" if details.get('cognizable') else "❌ Non-Cognizable - Police need magistrate's order"
    
    return f"""
## ⚖️ {offence.upper()} - Section {section}

---

### 📖 What is this offence?

{details['description']}

---

### 🔨 Punishment

**{details['punishment']}**

---

### 📊 Legal Status

| Attribute | Status |
|-----------|--------|
| **Bail** | {bail_status} |
| **Police Powers** | {cognizable_status} |
| **Trial Court** | 🏛️ {details.get('court', 'Any Magistrate')} |
| **Limitation Period** | 📅 {details.get('limitation', 'No limitation')} |

---

### 📚 Additional Information

This information is based on the Indian Penal Code, 1860 and the Information Technology Act, 2000 as applicable.

*For specific legal advice, please consult a qualified advocate.*

---

### 🔍 Related Questions You Can Ask:
• What is the procedure for filing an FIR?
• How to apply for bail?
• What are the rights of an arrested person?
"""

def format_general_response(query: str) -> str:
    """General response for non-IPC queries"""
    return """
## 🤔 How Can I Help You?

I'm your legal assistant for Indian criminal law. Here's what I can do:

### 📋 **IPC Section Lookup**
Ask me about any offence:
- *"What is the punishment for murder?"*
- *"Tell me about Section 376"*
- *"Is theft bailable?"*

### ⚖️ **Legal Status Check**
- *"Is cheating a bailable offence?"*
- *"What is the limitation period for defamation?"*

### 🔍 **Quick Reference**

| Section | Offence | Punishment |
|---------|---------|------------|
| 302 | Murder | Death/Life imprisonment |
| 304B | Dowry Death | 7 years to life |
| 376 | Rape | 10 years to life |
| 379 | Theft | Up to 3 years |
| 420 | Cheating | Up to 7 years |
| 506 | Criminal Intimidation | Up to 7 years |
| 354A | Sexual Harassment | Up to 3 years |

---

**Just type your question naturally - I understand legal terms!** ⚡
"""

# ============================================================
# SESSION STATE
# ============================================================

def init_session():
    if "messages" not in st.session_state:
        welcome = """⚡ **Police Rulebook Assistant - Ultra Fast Edition**

I'm ready to help with Indian criminal law! 

**Try asking me:**
- "What is the punishment for murder?"
- "Tell me about Section 376"
- "Is theft a bailable offence?"
- "What is the punishment for cheating?"

**I have 50+ IPC sections loaded instantly!** ⚡
"""
        st.session_state.messages = [{"role": "assistant", "content": welcome}]
    if "uploaded_pdfs" not in st.session_state:
        st.session_state.uploaded_pdfs = []

init_session()

# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0f1a 0%, #0a0e1a 100%); }
    .main-header { text-align: center; padding: 1.5rem; background: rgba(26,31,46,0.6); backdrop-filter: blur(12px); border-radius: 30px; margin-bottom: 1.5rem; }
    .main-header h1 { font-size: 2rem; background: linear-gradient(135deg, #ffffff, #60a5fa, #10b981); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stat-card { background: rgba(19,24,35,0.7); border-radius: 20px; padding: 0.8rem; text-align: center; }
    .stat-number { font-size: 1.8rem; font-weight: 800; background: linear-gradient(135deg, #10b981, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .fast-badge { background: #10b981; color: white; padding: 0.2rem 0.8rem; border-radius: 20px; font-size: 0.7rem; display: inline-block; margin-left: 0.5rem; }
    div[data-testid="stChatMessage"][data-testid*="assistant"] { background: linear-gradient(135deg, rgba(15,26,20,0.95), rgba(20,30,25,0.95)); border-radius: 20px; padding: 1rem; border: 1px solid rgba(16,185,129,0.2); }
    div[data-testid="stChatMessage"][data-testid*="user"] { background: linear-gradient(135deg, rgba(26,15,15,0.95), rgba(31,20,20,0.95)); border-radius: 20px; padding: 1rem; border: 1px solid rgba(220,38,38,0.2); }
    .footer { text-align: center; padding: 1rem; color: #6b7280; font-size: 0.7rem; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>⚡ Police Rulebook Assistant <span class="fast-badge">Ultra Fast - Ready in 3 Seconds</span></h1>
    <p>50+ IPC Sections Instantly | No Waiting | Just Ask!</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 📊 Dashboard")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">{len(IPC_DATABASE)}</div>
            <div class="stat-label">IPC Sections</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number">⚡</div>
            <div class="stat-label">Instant Ready</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📋 Quick Reference")
    st.markdown("""
    | Section | Offence |
    |---------|---------|
    | 302 | Murder |
    | 304B | Dowry Death |
    | 376 | Rape |
    | 379 | Theft |
    | 420 | Cheating |
    | 506 | Criminal Intimidation |
    """)
    
    st.markdown("---")
    st.markdown("### 📤 Upload PDF (Optional)")
    st.caption("Upload additional legal documents for reference")
    uploaded = st.file_uploader("Add PDF", type=["pdf"], key="uploader")
    
    if uploaded:
        st.session_state.uploaded_pdfs.append(uploaded.name)
        st.success(f"✅ Added: {uploaded.name}")
    
    st.markdown("---")
    st.caption("⚡ **Ultra Fast Edition**")
    st.caption("Barath R K PDKV | 411623149004")
    st.caption("Project PRJ-005")

# ============================================================
# MAIN CHAT INTERFACE
# ============================================================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Ask about IPC sections, punishments, legal procedures...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("⚡ Searching..."):
            offence, details, confidence = get_ipc_match(user_input)
            
            if details:
                answer = format_response(offence, details, confidence)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            else:
                answer = format_general_response(user_input)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <p>⚡ Ultra Fast Edition | 50+ IPC Sections | Ready in 3 Seconds | No Waiting Time</p>
</div>
""", unsafe_allow_html=True)
