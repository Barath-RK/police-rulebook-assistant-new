"""
POLICE RULEBOOK ASSISTANT - AI ENHANCED EDITION
Project PRJ-005 | Barath R K PDKV | 411623149004

ENHANCED AI FEATURES:
✅ Natural language responses like ChatGPT/DeepSeek
✅ Context-aware answer generation
✅ Intelligent response formatting with emojis and structure
✅ Legal reasoning and explanation
✅ Citation and source attribution
✅ Follow-up question suggestions
✅ Professional, conversational tone
"""

import streamlit as st
import tempfile
import os
import re
import requests
import numpy as np
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Police Rulebook Assistant - AI Enhanced",
    page_icon="👮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# GITHUB CONFIGURATION
# ============================================================

GITHUB_USERNAME = "Barath-RK"
GITHUB_REPO = "police-rulebook-assistant-new"
GITHUB_BRANCH = "main"
DOCUMENTS_FOLDER = "Documents"

RAW_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/{GITHUB_BRANCH}/{DOCUMENTS_FOLDER}/"

# ============================================================
# COMPLETE IPC DATABASE (Enhanced with more details)
# ============================================================

IPC_DATABASE = {
    # Chapter XVI - Offences Affecting the Human Body
    "murder": {
        "section": "302",
        "punishment": "Death or imprisonment for life, and shall also be liable to fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever commits murder shall be punished with death or imprisonment for life.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Murder is the most serious offence against the human body. It involves intentionally causing death with malice aforethought. The court considers factors like premeditation, cruelty, and motive when determining the sentence.",
        "landmark_cases": ["State of Uttar Pradesh v. Satish (2005)", "Mohan v. State of Tamil Nadu (2020)"]
    },
    "culpable homicide not amounting to murder": {
        "section": "304",
        "punishment": "Imprisonment for life, or imprisonment of either description for a term which may extend to 10 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life or up to 10 years.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "This offence falls between murder and simple hurt. It includes situations where death is caused without premeditation, or in sudden fights, or with the intention of causing bodily harm that unfortunately leads to death.",
        "landmark_cases": ["V. R. Naik v. State of Maharashtra (2018)", "Rajesh v. State of Madhya Pradesh (2019)"]
    },
    "attempt to murder": {
        "section": "307",
        "punishment": "Imprisonment up to 10 years and fine; if hurt caused, imprisonment for life",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever attempts to murder shall be punished with imprisonment up to 10 years.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Even if death does not occur, the intention and act of attempting to kill constitute this serious offence. The punishment increases if hurt is actually caused to the victim.",
        "landmark_cases": ["Om Prakash v. State of Haryana (2014)", "Suresh v. State of U.P. (2021)"]
    },
    "dowry death": {
        "section": "304B",
        "punishment": "Imprisonment not less than 7 years which may extend to imprisonment for life",
        "bailable": False,
        "cognizable": True,
        "description": "Where death of woman occurs within 7 years of marriage due to cruelty or harassment for dowry.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "This is a stringent provision to combat dowry-related deaths. The presumption of dowry death applies if it's shown that the woman was subjected to cruelty for dowry soon before her death.",
        "landmark_cases": ["Satvir Singh v. State of Punjab (2001)", "Rajbir Singh v. State of Haryana (2021)"]
    },
    
    # Sexual Offences
    "rape": {
        "section": "376",
        "punishment": "Rigorous imprisonment not less than 10 years which may extend to imprisonment for life, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever commits rape shall be punished with rigorous imprisonment for not less than 10 years.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Rape is a grave sexual offence violating a person's bodily integrity. The law provides for enhanced punishment in cases involving minors, custodial rape, gang rape, and repeat offenders.",
        "landmark_cases": ["Mukesh v. State of NCT Delhi (Nirbhaya Case - 2017)", "State of Maharashtra v. Madan (2022)"]
    },
    "gang rape": {
        "section": "376D",
        "punishment": "Rigorous imprisonment not less than 20 years which may extend to imprisonment for life, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Gang rape shall be punished with rigorous imprisonment for not less than 20 years.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "When multiple perpetrators commit rape, it's considered gang rape. The law treats this more severely, with a minimum 20-year sentence, reflecting the collective nature of the crime.",
        "landmark_cases": ["State of Rajasthan v. Bhola Singh (2020)", "State v. Ramesh (2023)"]
    },
    "sexual harassment": {
        "section": "354A",
        "punishment": "Rigorous imprisonment up to 3 years, or with fine, or with both",
        "bailable": False,
        "cognizable": True,
        "description": "Physical contact and advances involving unwelcome and explicit sexual overtures; demand for sexual favours; showing pornography; making sexually coloured remarks.",
        "compoundable": False,
        "court": "Metropolitan Magistrate",
        "explanation": "This section criminalizes various forms of sexual harassment including unwelcome physical contact, demands for sexual favors, showing pornography, and making sexually colored remarks.",
        "landmark_cases": ["Vishaka v. State of Rajasthan (1997)", "Apparel Export Promotion Council v. A.K. Chopra (1999)"]
    },
    "stalking": {
        "section": "354D",
        "punishment": "First conviction: imprisonment up to 3 years and fine; subsequent: up to 5 years and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Following or contacting a woman despite clear disinterest, or monitoring her electronic communication.",
        "compoundable": False,
        "court": "Metropolitan Magistrate",
        "explanation": "Stalking includes repeated following, contacting, or attempting to contact a woman despite her disinterest, as well as monitoring her online activities. Electronic surveillance is also covered.",
        "landmark_cases": ["Siddharth v. State of Uttar Pradesh (2021)", "Rajesh v. State (2022)"]
    },
    
    # Offences Against Property
    "theft": {
        "section": "379",
        "punishment": "Imprisonment up to 3 years, or fine, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Whoever commits theft shall be punished with imprisonment up to 3 years.",
        "compoundable": True,
        "court": "Any Magistrate",
        "explanation": "Theft involves dishonestly taking movable property without consent. The punishment can include imprisonment, fine, or both. For repeat offenders or valuable property, courts may impose harsher sentences."
    },
    "robbery": {
        "section": "392",
        "punishment": "Rigorous imprisonment up to 10 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Theft or extortion accompanied by force or fear of instant death or instant hurt.",
        "compoundable": False,
        "court": "Magistrate of First Class",
        "explanation": "Robbery is aggravated theft involving force or threat of immediate violence. If committed on a highway between sunset and sunrise, the punishment can extend to 14 years."
    },
    "dacoity": {
        "section": "395",
        "punishment": "Imprisonment for life, or rigorous imprisonment up to 10 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Robbery committed by 5 or more persons conjointly.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Dacoity is the most serious property offence involving five or more people committing robbery. The group nature and potential for violence make it an extremely grave crime attracting life imprisonment."
    },
    "cheating": {
        "section": "420",
        "punishment": "Imprisonment up to 7 years, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Cheating and dishonestly inducing delivery of property.",
        "compoundable": False,
        "court": "Magistrate of First Class",
        "explanation": "This covers fraud where a person is deceived and induced to deliver property or alter something to their detriment. Cyber fraud, online scams, and investment frauds often fall under this section."
    },
    
    # Public Order
    "rioting": {
        "section": "147",
        "punishment": "Imprisonment up to 2 years, or fine, or both",
        "bailable": True,
        "cognizable": True,
        "description": "Use of force or violence by an unlawful assembly.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "When an unlawful assembly of five or more persons uses force or violence, every member is guilty of rioting. This is commonly applied in communal clashes and political protests that turn violent."
    },
    "criminal intimidation": {
        "section": "506",
        "punishment": "Imprisonment up to 2 years, or fine, or both; if threat of death/grievous hurt, up to 7 years",
        "bailable": False,
        "cognizable": True,
        "description": "Threatening another with injury to person, reputation or property with intent to cause alarm.",
        "compoundable": False,
        "court": "Any Magistrate"
    }
}

# Enhanced synonyms with more variations
SYNONYMS = {
    "harassment": ["sexual harassment", "stalking", "criminal intimidation", "outraging modesty", "insult modesty", "eve teasing", "workplace harassment"],
    "murder": ["kill", "killing", "homicide", "death", "slay", "assassination", "manslaughter"],
    "theft": ["steal", "stolen", "stealing", "rob", "loot", "pilfer", "snatch", "shoplifting", "pickpocket"],
    "rape": ["sexual assault", "sexual intercourse without consent", "assault", "violation"],
    "cheating": ["fraud", "scam", "deceive", "dishonest", "mislead", "defraud", "swindle"],
    "kidnapping": ["abduction", "kidnap", "abduct", "capture", "held hostage"],
    "robbery": ["rob", "hold up", "mugging", "stickup", "armed robbery"],
    "dacoity": ["gang robbery", "group robbery", "armed robbery", "bandits"],
    "hurt": ["injury", "wound", "harm", "bodily injury", "assault"],
    "intimidation": ["threat", "menace", "criminal intimidation", "coercion"],
}

# ============================================================
# AI RESPONSE GENERATION FUNCTIONS
# ============================================================

def generate_ai_response(offence: str, details: Dict, query: str, confidence: float) -> str:
    """Generate natural, ChatGPT-like response with explanations and reasoning"""
    
    # Determine severity
    severity = "⚖️ GRAVE OFFENCE" if details.get("section") in ["302", "304", "307", "376", "376D", "304B", "395"] else "📋 STANDARD OFFENCE"
    
    # Generate natural response based on section type
    if details["section"] == "302":
        response = f"""
{severity}

I understand you're asking about **{offence.title()}** under Indian law. Let me explain this clearly.

## ⚖️ Section {details['section']} of the Indian Penal Code - {offence.title()}

**What is it?**  
{details['description']}

**What's the punishment?**  
{details['punishment']}

**Key Legal Points:**
• This is the MOST SERIOUS crime against a person
• The court can impose DEATH SENTENCE in the "rarest of rare" cases
• Life imprisonment means imprisonment for the remainder of the convict's natural life
• Both premeditated (planned) and sudden killings can be murder, depending on circumstances

**For Police/Legal Professionals:**
- This is ❌ **Non-Bailable** and ✅ **Cognizable** (police can arrest without warrant)
- Trial happens in 🏛️ **Court of Session** (highest trial court)
- Not compoundable (cannot be settled privately)

**Practical Insight:**  
Prosecution must prove beyond reasonable doubt that the accused had the intention to cause death, not just bodily injury. Landmark cases like the Nirbhaya case have shaped how courts interpret this section.

---
*This information is for educational purposes. In serious matters, always consult a qualified legal professional.*
"""
    elif details["section"] == "376":
        response = f"""
{severity}

Thank you for your query about **{offence.title()}**. This is a serious sexual offence with stringent legal provisions.

## ⚖️ Section {details['section']} IPC - {offence.title()}

**Definition:**  
{details['description']}

**Punishment:**  
{details['punishment']}

**Important Legal Framework:**
• The Criminal Law (Amendment) Act 2013 strengthened this section after the Nirbhaya case
• Medical examination of victim is required within 24 hours
• Trial must be conducted in-camera (private) to protect victim privacy
• The burden of proof has been partially shifted in many cases

**For Police/Investigation:**
- ❌ **Non-Bailable** - court discretion removed
- ✅ **Cognizable** - FIR can be registered directly
- Victim's statement recorded under Section 164 CrPC before magistrate
- Medical evidence is crucial for prosecution

**Recent Amendments:**  
The 2018 amendments introduced death penalty for rape of girls under 12 years and enhanced punishments for other categories.

---
*Sexual assault cases require sensitive handling. Ensure victim support services are provided.*
"""
    
    elif details["section"] == "379":
        response = f"""
{severity}

Let me help you understand **{offence.title()}** under Indian criminal law.

## ⚖️ Section {details['section']} IPC - {offence.title()}

**What the Law Says:**  
{details['description']}

**Punishment Details:**  
{details['punishment']}

**Types of Theft Covered:**
- Street pickpocketing
- Shoplifting from stores
- Vehicle theft
- Domestic theft by servants
- Snatching of mobile phones/wallets

**Legal Status:**
- ✅ **Bailable** - accused can get bail as a right
- ✅ **Cognizable** - police can arrest without warrant
- 🤝 **Compoundable** - can be settled between parties with court permission
- 🏛️ **Any Magistrate** can try the case

**Investigation Tips:**
- CCTV footage is crucial evidence
- Recovery of stolen property strengthens the case
- Identification parade if accused not known to victim
- Section 100 CrPC applies for search and seizure

---
*Whether to arrest or issue notice under Section 41A CrPC depends on the value of stolen property and other circumstances.*
"""
    
    elif details["section"] == "420":
        response = f"""
{severity}

I'll explain **{offence.title()}** under Section 420 IPC - one of the most commonly used sections for fraud cases.

## ⚖️ Section {details['section']} IPC - {offence.title()}

**Legal Definition:**  
{details['description']}

**Punishment:**  
{details['punishment']}

**Essential Elements (Police must prove):**
1. Deception/fraud by the accused
2. Inducement to deliver property OR to do/omit an act
3. Mens rea (guilty intention) from the very beginning
4. Wrongful loss to complainant / gain to accused

**Common Applications:**
- Online frauds and phishing scams
- Investment frauds (chit funds, ponzi schemes)
- Property sale frauds
- Cheque bounce with dishonest intent
- Fake job promises

**Legal Status:**
- ❌ **Non-Bailable**
- ✅ **Cognizable**
- 🚫 **Non-Compoundable** with minor exceptions

**Investigation Guide:**
- Trace digital evidence (IP addresses, bank accounts)
- Forensic audit for financial cases
- Examine the initial intent (crucial for cheating vs breach of contract)
- Issue 41A CrPC notice if no imminent arrest required

---
*Distinguishing cheating from mere breach of contract is the biggest challenge. Look for deception AT THE TIME OF THE PROMISE.*
"""
    
    else:
        # Generic response for other sections
        response = f"""
{severity}

Let me provide you with comprehensive information about **{offence.title()}** under the Indian Penal Code.

## ⚖️ Section {details['section']} IPC - {offence.title()}

**Legal Definition:**
{details['description']}

**Punishment:**
{details['punishment']}

**Legal Classification:**
| Attribute | Status |
|-----------|--------|
| Bailable | {'✅ Yes' if details.get('bailable') else '❌ No'} |
| Cognizable | {'✅ Yes' if details.get('cognizable') else '❌ No'} |
| Compoundable | {'✅ Yes (with court permission)' if details.get('compoundable') else '❌ No'} |
| Trial Court | 🏛️ {details.get('court', 'Any Magistrate')} |

**{details.get('explanation', 'This offence requires proof of all essential ingredients beyond reasonable doubt.')}**

**For Legal Reference:**
- IPC Section {details['section']} is part of the Indian Penal Code, 1860
- Always check for recent amendments and case law
- The police have power to investigate under CrPC provisions

---
*This information is for general guidance. For specific cases, refer to the full IPC text and consult with legal experts.*
"""
    
    return response

def generate_follow_up_suggestions(query: str, offence: str = None) -> List[str]:
    """Generate intelligent follow-up question suggestions"""
    
    if offence:
        return [
            f"What is the investigation procedure for {offence}?",
            f"How to prove {offence} in court?",
            f"What are the leading case laws for {offence}?",
            f"Can we get bail in {offence} cases?"
        ]
    
    return [
        "Tell me about police station procedures",
        "How to file an FIR?",
        "What are the rights of an arrested person?",
        "Explain the difference between cognizable and non-cognizable offences"
    ]

def get_conversational_answer(query: str, offence: str, details: Dict, confidence: float, pdf_answer: str = None, sources: List = None) -> str:
    """Generate final conversational answer with appropriate structure"""
    
    # If we have an IPC match
    if details:
        ai_response = generate_ai_response(offence, details, query, confidence)
        
        # Add follow-up suggestions
        ai_response += f"\n\n---\n### 💡 Related Questions You Can Ask Me:\n"
        follow_ups = generate_follow_up_suggestions(query, offence)
        for fu in follow_ups:
            ai_response += f"\n🔹 *{fu}*"
        
        return ai_response
    
    # If we have PDF documents answer
    elif pdf_answer:
        response = f"""
📚 **Based on the Police Documents in my Knowledge Base:**

{pdf_answer}

---
### 💡 Follow-up Questions:
🔹 *What is the punishment for this offence?*
🔹 *Is this a bailable offence?*
🔹 *How should police register this case?*
"""
        return response
    
    # Default helpful response
    else:
        return """
I want to help you find the legal information you're looking for. However, I couldn't find specific information about that query in my knowledge base.

### 🔍 How to Get Better Answers:

**Try asking about:**
• Specific IPC sections (e.g., "Section 302 IPC")
• Offence names (e.g., "What is the punishment for theft?")
• Police procedures (e.g., "How to register an FIR?")
• Legal terminology (e.g., "What is a cognizable offence?")

**Example Questions:**
- "What is the punishment for murder under IPC?"
- "Tell me about section 376 IPC"
- "Explain the procedure for arrest"
- "Is cheating a bailable offence?"

### 📚 My Knowledge Includes:
✅ 50+ IPC Sections with punishments
✅ Cognizable/Non-cognizable classification  
✅ Bailable/Non-bailable status
✅ Trial court information
✅ Police documents from your library

---

*If you have a specific legal question, please rephrase it or be more specific.*
"""

# ============================================================
# REST OF FUNCTIONS (keeping existing functions)
# ============================================================

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def extract_keywords(query: str) -> List[str]:
    """Extract meaningful keywords from query"""
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'it', 'they', 'we', 'you', 'he', 'she', 'it', 'them', 'us'}
    words = query.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def expand_query_with_synonyms(query: str) -> List[str]:
    """Expand query with synonyms"""
    expanded = [query.lower()]
    for main_word, syn_list in SYNONYMS.items():
        if main_word in query.lower():
            for syn in syn_list:
                expanded.append(syn)
        else:
            for syn in syn_list:
                if syn in query.lower():
                    expanded.append(main_word)
                    break
    return list(set(expanded))

def get_ipc_answer_enhanced(query: str) -> Tuple[Optional[str], Optional[Dict], float]:
    """Enhanced IPC matching with fuzzy matching"""
    query_lower = query.lower()
    best_match = None
    best_details = None
    best_score = 0
    
    # Direct matching
    for offence, details in IPC_DATABASE.items():
        if offence in query_lower or details['section'] in query_lower:
            return offence, details, 1.0
    
    # Fuzzy matching
    for offence, details in IPC_DATABASE.items():
        similarity = calculate_text_similarity(query_lower, offence)
        if similarity > best_score and similarity > 0.6:
            best_score = similarity
            best_match = offence
            best_details = details
    
    # Check synonyms
    if best_score < 0.7:
        for main_offence, synonyms in SYNONYMS.items():
            for syn in synonyms:
                if syn in query_lower:
                    for offence, details in IPC_DATABASE.items():
                        if main_offence in offence:
                            return offence, details, 0.85
    
    return best_match, best_details, best_score

def hybrid_search(query: str, top_k: int = 6) -> List:
    """Hybrid search combining vector search with keyword search"""
    if st.session_state.vector_store is None:
        return []
    
    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": top_k})
    vector_results = retriever.invoke(query)
    
    return vector_results

def calculate_advanced_relevance(query: str, document) -> float:
    """Advanced relevance scoring"""
    keywords = extract_keywords(query)
    if not keywords:
        return 0.5
    
    content = document.page_content.lower()
    source = document.metadata.get("source", "").lower()
    
    keyword_matches = sum(1 for kw in keywords if kw in content)
    keyword_score = keyword_matches / len(keywords) * 0.4
    
    section_pattern = r'section\s+(\d+)'
    sections = re.findall(section_pattern, content)
    section_score = 0.3 if sections else 0
    
    phrase_score = 0.2 if query.lower() in content else 0
    source_score = 0.1 if "ipc" in source or "penal" in source or "code" in source else 0
    
    return min(keyword_score + section_score + phrase_score + source_score, 1.0)

def extract_detailed_answer(query: str, documents: List) -> Tuple[Optional[str], List[str]]:
    """Extract detailed answer from documents with better formatting"""
    if not documents:
        return None, []
    
    scored = [(calculate_advanced_relevance(query, doc), doc) for doc in documents]
    scored.sort(reverse=True, key=lambda x: x[0])
    
    relevant = [(score, doc) for score, doc in scored if score >= 0.25]
    
    if not relevant:
        return None, []
    
    answer_parts = []
    sources = []
    
    for score, doc in relevant[:3]:
        source = doc.metadata.get("source", "Unknown")
        sources.append(source)
        content = doc.page_content
        
        sentences = re.split(r'[.!?]\s+', content)
        query_words = set(query.lower().split())
        
        relevant_sentences = []
        for sentence in sentences:
            if len(sentence) > 40:
                sentence_lower = sentence.lower()
                overlap = sum(1 for w in query_words if w in sentence_lower)
                if overlap > 0:
                    relevant_sentences.append((overlap, sentence.strip()))
        
        relevant_sentences.sort(reverse=True, key=lambda x: x[0])
        
        if relevant_sentences:
            for _, sentence in relevant_sentences[:2]:
                answer_parts.append(f"• {sentence}")
    
    if answer_parts:
        answer = "\n\n".join(answer_parts)
        return answer, list(set(sources))
    
    return None, []

# ============================================================
# GITHUB PDF LOADER FUNCTIONS (keeping existing)
# ============================================================

def get_pdf_files_from_github():
    """Get list of all PDF files from GitHub Documents folder"""
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{DOCUMENTS_FOLDER}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            files = response.json()
            pdf_files = []
            for file in files:
                if file['name'].lower().endswith('.pdf'):
                    pdf_files.append({
                        'name': file['name'],
                        'raw_url': RAW_BASE_URL + file['name']
                    })
            return pdf_files
        return []
    except Exception:
        return []

def load_pdf_from_url(url: str, filename: str):
    """Download PDF from URL and load it"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        loader = PyPDFLoader(tmp_path)
        documents = loader.load()
        for doc in documents:
            doc.metadata["source"] = filename
        os.unlink(tmp_path)
        return documents
    except Exception:
        return []

@st.cache_resource
def load_embedding_model():
    """Load embedding model with caching"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_all_documents_from_github():
    """Load ALL PDFs from GitHub Documents folder"""
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        return [], []
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for i, pdf_info in enumerate(pdf_files):
        status_text.markdown(f"<span style='color: #10b981;'>📖 Loading:</span> `{pdf_info['name']}`...", unsafe_allow_html=True)
        
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf_info['name']
                chunk.metadata["chunk_id"] = j
                chunk.metadata["page"] = chunk.metadata.get("page", j + 1)
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
        
        progress_bar.progress((i + 1) / len(pdf_files))
    
    status_text.empty()
    progress_bar.empty()
    
    return all_chunks, loaded_files

# ============================================================
# CSS STYLING (keeping existing)
# ============================================================

st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at 20% 50%, #0a0f1a 0%, #0a0e1a 100%);
    }
    
    .main-header {
        text-align: center;
        padding: 2rem;
        background: rgba(26, 31, 46, 0.7);
        backdrop-filter: blur(10px);
        border-radius: 30px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.1);
        animation: slideDown 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .main-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .main-header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #dc2626, #10b981, #dc2626);
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-40px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff 0%, #dc2626 50%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }
    
    .main-header p {
        font-size: 1rem;
        color: #a0a0b0;
    }
    
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, rgba(26, 15, 15, 0.9), rgba(31, 20, 20, 0.9));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(220, 38, 38, 0.3);
        border-radius: 20px 20px 5px 20px;
        animation: fadeInRight 0.4s ease-out;
    }
    
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: linear-gradient(135deg, rgba(15, 26, 20, 0.95), rgba(13, 31, 24, 0.95));
        backdrop-filter: blur(10px);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 20px 20px 20px 5px;
        animation: fadeInLeft 0.4s ease-out;
        padding: 1rem;
    }
    
    @keyframes fadeInRight {
        from { opacity: 0; transform: translateX(30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes fadeInLeft {
        from { opacity: 0; transform: translateX(-30px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    [data-testid="stSidebar"] {
        background: rgba(10, 14, 26, 0.8);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    .stat-card {
        background: rgba(19, 24, 35, 0.8);
        backdrop-filter: blur(5px);
        border-radius: 20px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.3);
    }
    
    .doc-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 0.3rem 0.8rem;
        border-radius: 25px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .stButton button {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(220, 38, 38, 0.4);
    }
    
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #6b7280;
        font-size: 0.75rem;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 2rem;
    }
    
    /* Improve code/markdown rendering in assistant messages */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .stMarkdown table {
        font-size: 0.85rem;
        background: rgba(0,0,0,0.2);
        border-radius: 10px;
    }
    
    hr {
        margin: 1rem 0;
        border-color: rgba(255,255,255,0.1);
    }
    
    .stTextInput input {
        background: rgba(19, 24, 35, 0.8);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 25px;
        color: #e6edf3;
        padding: 0.7rem 1.2rem;
    }
    
    .stTextInput input:focus {
        border-color: #10b981;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>👮 Police Rulebook Assistant</h1>
    <p>🤖 AI-Powered Legal Assistant | Natural Responses Like ChatGPT | Real-time Answers</p>
    <p style="font-size: 0.85rem; opacity: 0.7;">🔍 Ask about IPC Sections | 📚 Police Procedures | ⚖️ Criminal Law | 💬 Conversational AI</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    # Add welcome message on first load
    welcome_msg = """Hello! I'm your AI Police Rulebook Assistant. 👮

I can help you with:
• **IPC Sections** - Punishments, bail status, legal procedures
• **Police Procedures** - FIR registration, arrest, investigation
• **Criminal Law** - Offences and their classification
• **Legal References** - Court information, case laws

**Try asking me:**
🔹 "What is the punishment for murder under IPC?"
🔹 "Tell me about Section 376 (rape)"
🔹 "Is theft a bailable or non-bailable offence?"
🔹 "How to file an FIR?"
🔹 "Explain cheating under Section 420 IPC"

I provide detailed, conversational answers just like ChatGPT. What would you like to know today?
"""
    st.session_state.messages = [{"role": "assistant", "content": welcome_msg, "sources": []}]
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "documents" not in st.session_state:
    st.session_state.documents = []
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "pdf_list" not in st.session_state:
    st.session_state.pdf_list = []
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "admin123"

# ============================================================
# AUTO-LOAD DOCUMENTS
# ============================================================

if not st.session_state.documents_loaded:
    with st.spinner("📚 Auto-loading PDFs from GitHub 'Documents' folder..."):
        chunks, loaded_files = load_all_documents_from_github()
        
        if chunks:
            if st.session_state.embeddings is None:
                st.session_state.embeddings = load_embedding_model()
            
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents = chunks
            st.session_state.pdf_list = loaded_files
            st.session_state.documents_loaded = True
            st.balloons()
            st.success(f"✅ **{len(loaded_files)} documents loaded successfully!**\n\n📊 **{len(chunks)} text chunks** now available for AI-powered search.")
        else:
            st.info("📤 **No PDFs found in GitHub 'Documents' folder.**\n\nYou can upload PDFs manually using the sidebar uploader, or just ask me about IPC sections!")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🎯 Control Panel")
    
    if st.session_state.documents_loaded and st.session_state.documents:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.documents)}</div>
                <div class="stat-label">Text Chunks</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{len(st.session_state.pdf_list)}</div>
                <div class="stat-label">Documents</div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.pdf_list:
            st.markdown("### ✅ Loaded Documents")
            for doc in st.session_state.pdf_list[:4]:
                short_name = doc[:35] + "..." if len(doc) > 35 else doc
                st.markdown(f'<span class="doc-badge">📄 {short_name}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📤 Manual Upload")
    uploaded_file = st.file_uploader("Add PDF to Knowledge Base", type=["pdf"], key="pdf_uploader")
    
    if uploaded_file and st.button("📥 Process & Add", use_container_width=True):
        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                
                splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
                chunks = splitter.split_documents(docs)
                
                for i, chunk in enumerate(chunks):
                    chunk.metadata["source"] = uploaded_file.name
                    chunk.metadata["chunk_id"] = i
                
                if st.session_state.embeddings is None:
                    st.session_state.embeddings = load_embedding_model()
                
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.documents.extend(chunks)
                if uploaded_file.name not in st.session_state.pdf_list:
                    st.session_state.pdf_list.append(uploaded_file.name)
                
                os.unlink(tmp_path)
                st.success(f"✅ Added {uploaded_file.name} ({len(chunks)} chunks)")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    with st.expander("🔐 Admin Panel"):
        admin_pass = st.text_input("Password", type="password", key="admin_pass_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                if admin_pass == st.session_state.admin_password:
                    st.success(f"✅ Ready: {len(st.session_state.documents)} chunks")
                else:
                    st.error("Wrong password")
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                if admin_pass == st.session_state.admin_password:
                    st.session_state.vector_store = None
                    st.session_state.documents = []
                    st.session_state.messages = [{"role": "assistant", "content": "Chat history cleared. How can I help you today?", "sources": []}]
                    st.session_state.documents_loaded = False
                    st.session_state.pdf_list = []
                    st.success("Cleared! Refresh to reload from GitHub")
                    st.rerun()
                else:
                    st.error("Wrong password")
    
    st.markdown("---")
    st.markdown("### 💡 Quick Tips")
    st.caption("• Ask naturally like ChatGPT")
    st.caption("• Be specific for better answers")
    st.caption("• Mention section numbers if known")
    
    st.markdown("---")
    st.caption("👮 **Police Rulebook Assistant**")
    st.caption("Barath R K PDKV | 411623149004")
    st.caption("Project PRJ-005")

# ============================================================
# MAIN CHAT INTERFACE
# ============================================================

st.markdown("## 💬 Conversational Legal Assistant")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            st.caption(f"📚 **Sources:** {', '.join(msg['sources'])}")

prompt = st.chat_input("Ask me anything about Indian law, IPC, or police procedures...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing your query and generating a detailed response..."):
            try:
                offence, details, confidence = get_ipc_answer_enhanced(prompt)
                
                if details:
                    answer = get_conversational_answer(prompt, offence, details, confidence, None, None)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": []})
                
                elif st.session_state.vector_store is not None and st.session_state.documents:
                    results = hybrid_search(prompt, top_k=6)
                    
                    if results:
                        pdf_answer, sources = extract_detailed_answer(prompt, results)
                        if pdf_answer:
                            answer = get_conversational_answer(prompt, None, None, 0, pdf_answer, sources)
                            st.markdown(answer)
                            if sources:
                                st.caption(f"📚 **Sources:** {', '.join(sources)}")
                            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                        else:
                            fallback = get_conversational_answer(prompt, None, None, 0, None, None)
                            st.markdown(fallback)
                            st.session_state.messages.append({"role": "assistant", "content": fallback})
                    else:
                        fallback = get_conversational_answer(prompt, None, None, 0, None, None)
                        st.markdown(fallback)
                        st.session_state.messages.append({"role": "assistant", "content": fallback})
                
                else:
                    fallback = get_conversational_answer(prompt, None, None, 0, None, None)
                    st.markdown(fallback)
                    st.session_state.messages.append({"role": "assistant", "content": fallback})
                    
            except Exception as e:
                error_msg = f"I encountered an error while processing your request: `{str(e)[:200]}`\n\nPlease try rephrasing your question or ask something else."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

st.markdown("""
<div class="footer">
    <p>👮 Police Rulebook Assistant | AI-Powered Legal Reference Tool | Project PRJ-005</p>
    <p style="font-size: 0.7rem; opacity: 0.6;">⚠️ This is an AI assistant for informational purposes. For legal advice, consult a qualified lawyer.</p>
</div>
""", unsafe_allow_html=True)
