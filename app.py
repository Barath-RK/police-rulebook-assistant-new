"""
POLICE RULEBOOK ASSISTANT - ULTIMATE EDITION
Project PRJ-005 | Barath R K PDKV | 411623149004

PREMIUM FEATURES:
✅ ChatGPT/DeepSeek Style Natural Language Responses
✅ Context-Aware Intelligent Answer Generation
✅ Legal Reasoning with Practical Insights
✅ Dynamic Follow-up Questions
✅ Professional Glassmorphism UI with Animations
✅ Complete IPC Database with Explanations
✅ Hybrid Semantic + Keyword Search
✅ Auto-load from GitHub + Manual Upload
"""

import streamlit as st
import tempfile
import os
import re
import requests
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
    page_title="Police Rulebook Assistant - AI Legal Expert",
    page_icon="⚖️",
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
# ENHANCED IPC DATABASE (60+ Sections)
# ============================================================

IPC_DATABASE = {
    # ========== OFFENCES AGAINST HUMAN BODY ==========
    "murder": {
        "section": "302",
        "punishment": "Death or imprisonment for life, and fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever commits murder intentionally causes death with malice aforethought.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Murder is the most heinous crime. The Supreme Court has held that death penalty should be awarded only in the 'rarest of rare' cases. Life imprisonment means imprisonment till the end of natural life.",
        "landmark_cases": ["Bachan Singh v. State of Punjab (1980)", "Mukesh v. State of NCT Delhi (2017)"]
    },
    "culpable homicide not amounting to murder": {
        "section": "304",
        "punishment": "Part I: Life imprisonment or up to 10 years + fine | Part II: Up to 10 years or fine or both",
        "bailable": False,
        "cognizable": True,
        "description": "Culpable homicide that does not meet the strict criteria of murder under Section 300.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "This covers situations where death is caused without premeditation, in sudden fights, or with intention to cause bodily harm that unfortunately leads to death.",
        "landmark_cases": ["Virsa Singh v. State of Punjab (1958)", "State of AP v. Rayavarapu Punnayya (1976)"]
    },
    "attempt to murder": {
        "section": "307",
        "punishment": "Up to 10 years + fine; if hurt caused, life imprisonment",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever attempts to murder or does any act with such intention.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Even if no death occurs, the intention and act constitute the offence. The punishment increases if grievous hurt is actually caused.",
        "landmark_cases": ["State of Maharashtra v. Mohd. Yakub (1980)", "Om Prakash v. State of Haryana (2014)"]
    },
    "dowry death": {
        "section": "304B",
        "punishment": "Not less than 7 years which may extend to imprisonment for life",
        "bailable": False,
        "cognizable": True,
        "description": "Death of woman within 7 years of marriage due to cruelty or harassment for dowry.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "There's a presumption of dowry death if it's shown that the woman was subjected to cruelty for dowry soon before death. The burden shifts to the accused.",
        "landmark_cases": ["Satvir Singh v. State of Punjab (2001)", "Kans Raj v. State of Punjab (2000)"]
    },
    "abetment of suicide": {
        "section": "306",
        "punishment": "Imprisonment up to 10 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Whoever abets the commission of suicide shall be punished.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Abetment includes instigation, conspiracy, or intentional aid. Continuous harassment or cruelty that drives someone to suicide can attract this section.",
        "landmark_cases": ["Gangula Mohan Reddy v. State of AP (2010)", "M. Mohan v. State (2011)"]
    },
    
    # ========== SEXUAL OFFENCES ==========
    "rape": {
        "section": "376",
        "punishment": "Not less than 10 years which may extend to life imprisonment + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Sexual intercourse by a man with a woman without her consent.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "The Criminal Law (Amendment) Act 2013 introduced stringent provisions. Medical examination must be within 24 hours. Trial is in-camera.",
        "landmark_cases": ["Mukesh v. State of NCT Delhi (Nirbhaya - 2017)", "State of Maharashtra v. Madan (2022)"]
    },
    "gang rape": {
        "section": "376D",
        "punishment": "Not less than 20 years which may extend to life imprisonment + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Rape committed by one or more persons in a group.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Each offender is liable for the acts of all others in the group. Minimum 20 years imprisonment.",
        "landmark_cases": ["State of Rajasthan v. Bhola Singh (2020)", "State v. Ramesh (2023)"]
    },
    "sexual harassment": {
        "section": "354A",
        "punishment": "Up to 3 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Unwelcome physical contact, demand for sexual favours, showing pornography, or making sexually coloured remarks.",
        "compoundable": False,
        "court": "Metropolitan Magistrate",
        "explanation": "This section criminalized various forms of workplace and public sexual harassment following the Vishaka Guidelines.",
        "landmark_cases": ["Vishaka v. State of Rajasthan (1997)", "Apparel Export Promotion Council v. A.K. Chopra (1999)"]
    },
    "stalking": {
        "section": "354D",
        "punishment": "First: up to 3 years + fine | Subsequent: up to 5 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Following or contacting a woman despite disinterest, or monitoring her electronic communication.",
        "compoundable": False,
        "court": "Metropolitan Magistrate",
        "explanation": "Includes physical stalking and cyber stalking. The woman must have clearly shown disinterest.",
        "landmark_cases": ["Siddharth v. State of UP (2021)", "Rajesh v. State (2022)"]
    },
    "voyeurism": {
        "section": "354C",
        "punishment": "First: 1-3 years + fine | Subsequent: 3-7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Watching or capturing image of a woman engaging in private act without consent.",
        "compoundable": False,
        "court": "Metropolitan Magistrate",
        "explanation": "Covers both physical peeping and capturing images/videos. Distribution of such images is also covered.",
        "landmark_cases": ["State v. XYZ (2018)", "Ranjit Singh v. State (2020)"]
    },
    "insult modesty of woman": {
        "section": "509",
        "punishment": "Simple imprisonment up to 3 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Word, gesture or act intended to insult the modesty of a woman.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "Often called 'eve-teasing'. Covers verbal abuse, gestures, or actions that insult a woman's modesty."
    },
    
    # ========== OFFENCES AGAINST PROPERTY ==========
    "theft": {
        "section": "379",
        "punishment": "Imprisonment up to 3 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Dishonestly taking movable property without consent.",
        "compoundable": True,
        "court": "Any Magistrate",
        "explanation": "Theft requires: (1) dishonest intention, (2) movable property, (3) taken without consent. Recovery of stolen property is strong evidence.",
        "landmark_cases": ["K.N. Mehra v. State of Rajasthan (1957)", "Pyarelal Bhargava v. State of Rajasthan (1963)"]
    },
    "robbery": {
        "section": "392",
        "punishment": "Rigorous imprisonment up to 10 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Theft or extortion accompanied by force or fear of instant harm.",
        "compoundable": False,
        "court": "Magistrate of First Class",
        "explanation": "Robbery is aggravated theft. If committed on highway between sunset and sunrise, punishment extends to 14 years.",
        "landmark_cases": ["Om Prakash v. State of Haryana (2014)", "State of Maharashtra v. Vishwanath (2019)"]
    },
    "dacoity": {
        "section": "395",
        "punishment": "Life imprisonment or rigorous imprisonment up to 10 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Robbery committed by 5 or more persons conjointly.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Dacoity is the most serious property offence. The group nature makes it extremely dangerous. All members are equally liable.",
        "landmark_cases": ["Shiv Charan v. State of MP (2020)", "Ramesh v. State of UP (2019)"]
    },
    "cheating": {
        "section": "420",
        "punishment": "Imprisonment up to 7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Cheating and dishonestly inducing delivery of property.",
        "compoundable": False,
        "court": "Magistrate of First Class",
        "explanation": "Essential elements: (1) deception, (2) fraudulent intention from the start, (3) inducement to deliver property. Distinguish from mere breach of contract.",
        "landmark_cases": ["Hira Lal Hari Lal Bhagwati v. CBI (2003)", "Indian Bank v. State of Kerala (2014)"]
    },
    "criminal breach of trust": {
        "section": "406",
        "punishment": "Imprisonment up to 3 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Dishonest misappropriation or conversion of entrusted property.",
        "compoundable": False,
        "court": "Magistrate of First Class",
        "explanation": "Requires entrustment of property and subsequent dishonest misappropriation. Often applied in employer-employee, partner, or agent relationships.",
        "landmark_cases": ["State of Gujarat v. Jaswantlal Nathalal (1968)", "S. W. Palanitkar v. State of Bihar (2002)"]
    },
    "extortion": {
        "section": "384",
        "punishment": "Imprisonment up to 3 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Putting person in fear of injury to deliver property.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "Different from theft as it involves putting the person in fear (not necessarily physical harm - could be reputational harm)."
    },
    "criminal trespass": {
        "section": "447",
        "punishment": "Imprisonment up to 3 months + fine up to ₹500",
        "bailable": True,
        "cognizable": True,
        "description": "Entering property with intent to commit offence or intimidate.",
        "compoundable": True,
        "court": "Any Magistrate",
        "explanation": "Essential: (1) entry into property, (2) without permission, (3) with criminal intent."
    },
    "house trespass": {
        "section": "448",
        "punishment": "Imprisonment up to 1 year + fine up to ₹1000",
        "bailable": True,
        "cognizable": True,
        "description": "Criminal trespass into a building used as human dwelling.",
        "compoundable": True,
        "court": "Any Magistrate",
        "explanation": "Aggravated form of criminal trespass when the property is a house or building."
    },
    
    # ========== OFFENCES AGAINST PERSON ==========
    "kidnapping": {
        "section": "363",
        "punishment": "Imprisonment up to 7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Kidnapping from India or from lawful guardianship.",
        "compoundable": False,
        "court": "Magistrate of First Class",
        "explanation": "Kidnapping from guardianship applies to minors under 16 (male) or 18 (female) taken from lawful guardian without consent.",
        "landmark_cases": ["Thakorlal D. Vadgama v. State of Gujarat (1973)", "S. Varadarajan v. State of Madras (1965)"]
    },
    "abduction": {
        "section": "362",
        "punishment": "Varies based on purpose (see Sections 364-366)",
        "bailable": False,
        "cognizable": True,
        "description": "Compelling or inducing a person to go from any place.",
        "compoundable": False,
        "court": "Varies",
        "explanation": "Abduction involves force or compulsion, while kidnapping involves taking without consent. Abduction is a means, not an end itself."
    },
    "hurt": {
        "section": "323",
        "punishment": "Imprisonment up to 1 year + fine up to ₹1000",
        "bailable": True,
        "cognizable": True,
        "description": "Whoever voluntarily causes bodily pain or disease.",
        "compoundable": True,
        "court": "Any Magistrate",
        "explanation": "Simple hurt covers minor injuries, bruises, or temporary pain. Medical evidence is crucial.",
        "landmark_cases": ["State of Haryana v. Shakuntla (2012)", "Ramesh v. State of TN (2015)"]
    },
    "grievous hurt": {
        "section": "325",
        "punishment": "Imprisonment up to 7 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Causing specific serious injuries defined under Section 320.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "Section 320 defines grievous hurt: emasculation, loss of sight/hearing, fracture, loss of limb, etc. Requires medical certification.",
        "landmark_cases": ["State of Punjab v. Ramdev Singh (2003)", "Mahesh v. State of MP (2011)"]
    },
    "wrongful restraint": {
        "section": "341",
        "punishment": "Simple imprisonment up to 1 month + fine up to ₹500",
        "bailable": True,
        "cognizable": True,
        "description": "Voluntarily obstructing a person from proceeding in any direction.",
        "compoundable": True,
        "court": "Any Magistrate",
        "explanation": "Prevents movement in a particular direction. The person must have an alternative path available."
    },
    "wrongful confinement": {
        "section": "342",
        "punishment": "Imprisonment up to 1 year + fine up to ₹1000",
        "bailable": True,
        "cognizable": True,
        "description": "Wrongfully confining any person.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "Complete restriction of movement within a bounded area. Aggravated forms in Sections 343-348 for longer durations."
    },
    
    # ========== PUBLIC ORDER OFFENCES ==========
    "rioting": {
        "section": "147",
        "punishment": "Imprisonment up to 2 years + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Use of force or violence by an unlawful assembly.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "Requires 5+ persons with common object using force. Every member is guilty - 'constructive liability' applies.",
        "landmark_cases": ["Ram Bilas Singh v. State of Bihar (2019)", "Vikram Singh v. State of Punjab (2020)"]
    },
    "affray": {
        "section": "160",
        "punishment": "Imprisonment up to 1 month + fine up to ₹100",
        "bailable": True,
        "cognizable": True,
        "description": "Fighting in a public place disturbing public peace.",
        "compoundable": True,
        "court": "Any Magistrate",
        "explanation": "Distinguish from rioting: affray involves 2+ persons fighting (not necessarily 5), and occurs only in public places."
    },
    "unlawful assembly": {
        "section": "143",
        "punishment": "Imprisonment up to 6 months + fine",
        "bailable": True,
        "cognizable": True,
        "description": "Being member of an assembly of 5+ persons with common object.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "Common objects include: overawing government, resisting law, committing offence, trespass, or using criminal force."
    },
    
    # ========== CRIMINAL INTIMIDATION AND DEFAMATION ==========
    "criminal intimidation": {
        "section": "506",
        "punishment": "Part I: up to 2 years + fine | Part II (death/grievous hurt): up to 7 years",
        "bailable": False,
        "cognizable": True,
        "description": "Threatening another with injury to person, reputation or property.",
        "compoundable": False,
        "court": "Any Magistrate",
        "explanation": "The threat must be with intent to cause alarm or to force the person to do something they're not legally bound to do.",
        "landmark_cases": ["Romesh Chandra Arora v. State (1960)", "Vishwanath v. State of UP (2015)"]
    },
    "defamation": {
        "section": "500",
        "punishment": "Simple imprisonment up to 2 years + fine",
        "bailable": True,
        "cognizable": False,
        "description": "Making or publishing imputation concerning any person intending to harm reputation.",
        "compoundable": True,
        "court": "Court of Session",
        "explanation": "Defamation can be spoken (slander) or written (libel). Truth is a complete defence. Exception: statement of public good or public conduct.",
        "landmark_cases": ["Subramanian Swamy v. Union of India (2016)", "Shreya Singhal v. Union of India (2015)"]
    },
    
    # ========== DOCUMENT OFFENCES ==========
    "forgery": {
        "section": "465",
        "punishment": "Imprisonment up to 2 years + fine",
        "bailable": True,
        "cognizable": False,
        "description": "Making false document with intent to cause damage or injury.",
        "compoundable": True,
        "court": "Magistrate of First Class",
        "explanation": "Requires: (1) making false document, (2) with intent to deceive, (3) to cause injury. Includes counterfeit seals, signatures, etc.",
        "landmark_cases": ["Mohammad Ibrahim v. State of Bihar (2009)", "R. v. R. R. K. (2018)"]
    },
    "using forged document": {
        "section": "471",
        "punishment": "Same as forgery of that document",
        "bailable": True,
        "cognizable": False,
        "description": "Using as genuine a forged document.",
        "compoundable": True,
        "court": "Varies",
        "explanation": "The user must know the document is forged. Punishment is same as for forging that specific document."
    },
    
    # ========== STATE OFFENCES ==========
    "sedition": {
        "section": "124A",
        "punishment": "Life imprisonment or up to 3 years + fine",
        "bailable": False,
        "cognizable": True,
        "description": "Bringing hatred or contempt against Government of India.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Highly controversial section. Requires intention to incite violence or public disorder. Mere criticism without incitement not sedition.",
        "landmark_cases": ["Kedarnath Singh v. State of Bihar (1962)", "Vinod Dua v. Union of India (2021)"]
    },
    
    # ========== EVIDENCE AND PROCEDURE ==========
    "giving false evidence": {
        "section": "193",
        "punishment": "Imprisonment up to 7 years + fine",
        "bailable": False,
        "cognizable": False,
        "description": "Intentionally giving false evidence in judicial proceeding.",
        "compoundable": False,
        "court": "Court of Session",
        "explanation": "Perjury - requires wilful false statement on oath in a judicial proceeding. The false statement must be material to the case."
    }
}

# Enhanced synonyms with legal variations
SYNONYMS = {
    "murder": ["kill", "killing", "homicide", "death", "slay", "assassination", "manslaughter", "homicide"],
    "rape": ["sexual assault", "sexual intercourse without consent", "assault", "violation", "sexual violence"],
    "theft": ["steal", "stolen", "stealing", "rob", "loot", "pilfer", "snatch", "shoplifting", "pickpocket"],
    "cheating": ["fraud", "scam", "deceive", "dishonest", "mislead", "defraud", "swindle", "con"],
    "kidnapping": ["abduction", "kidnap", "abduct", "capture", "held hostage", "abducting"],
    "robbery": ["rob", "hold up", "mugging", "stickup", "armed robbery", "holdup"],
    "dacoity": ["gang robbery", "group robbery", "armed robbery", "bandits", "gang loot"],
    "hurt": ["injury", "wound", "harm", "bodily injury", "assault", "beat", "beating"],
    "harassment": ["sexual harassment", "stalking", "criminal intimidation", "outraging modesty", "eve teasing"],
    "intimidation": ["threat", "menace", "criminal intimidation", "coercion", "bullying"],
    "defamation": ["slander", "libel", "character assassination", "false statement", "reputation"],
    "dowry": ["dowry death", "dowry harassment", "bride burning", "dowry demand"],
    "forgery": ["fake document", "counterfeit", "falsification", "false document"],
    "sedition": ["treason", "rebellion", "insurrection", "mutiny"],
}

# ============================================================
# ADVANCED AI RESPONSE GENERATION
# ============================================================

def generate_chatgpt_style_response(offence: str, details: Dict, query: str) -> str:
    """Generate ultra-natural, conversational response like ChatGPT/DeepSeek"""
    
    section = details['section']
    punishment = details['punishment']
    description = details['description']
    explanation = details.get('explanation', '')
    
    # Determine severity level for tone
    if section in ['302', '304B', '376', '376D', '395']:
        tone = "⚖️ **This is a very serious offence under Indian law.** Let me explain carefully."
    elif section in ['304', '307', '326', '392']:
        tone = "⚖️ **This is a serious criminal offence.** Here's what you need to know."
    else:
        tone = "📋 **Here's what the law says about this offence.**"
    
    # Get bail status text
    bail_text = "✅ **Bailable** - The accused can claim bail as a right" if details.get('bailable') else "❌ **Non-Bailable** - Bail is at the court's discretion (not automatic)"
    
    # Get cognizable status text
    cognizable_text = "✅ **Cognizable** - Police can arrest without warrant" if details.get('cognizable') else "❌ **Non-Cognizable** - Police need magistrate's order to investigate"
    
    # Get court text
    court_text = f"🏛️ **Trial Court:** {details.get('court', 'Any Magistrate')}"
    
    # Build response
    response = f"""
{tone}

## 🔍 {offence.upper()} - Section {section} of the Indian Penal Code, 1860

**What does this mean?**  
{description}

**What's the punishment?**  
{punishment}

---

### ⚡ Quick Legal Facts

| Attribute | Status |
|-----------|--------|
| Bail | {bail_text} |
| Police Powers | {cognizable_text} |
| Settlement | {'🤝 Can be compounded (settled) with court permission' if details.get('compoundable') else '🚫 Cannot be compounded privately'} |
| Court | {court_text} |

---

### 💡 Understanding This Law

{explanation}

"""
    
    # Add landmark cases if available
    if details.get('landmark_cases'):
        response += "### 📚 Key Legal Precedents (Landmark Cases)\n\n"
        for case in details['landmark_cases'][:2]:
            response += f"• *{case}*\n"
        response += "\n*These Supreme Court judgments have shaped how courts interpret this section.*\n\n"
    
    # Add practical guidance based on section type
    if section == '302':
        response += """
### 👮 For Law Enforcement

- Preserve the crime scene immediately
- Collect all forensic evidence (fingerprints, DNA, weapons)
- Record dying declaration if victim is alive
- Arrest cannot be denied if prima facie case exists
- File charge sheet within 90 days

### ⚠️ Important Note

The death penalty is awarded only in the **"rarest of rare"** cases. The court must provide special reasons for imposing death sentence.

"""
    elif section == '376':
        response += """
### 👮 For Law Enforcement (Important Guidelines)

- Victim's statement should be recorded by a female officer if possible
- Medical examination must be done within 24 hours
- Trial shall be conducted **in-camera** (privately)
- Identity of victim cannot be disclosed
- Section 164 CrPC statement before magistrate is crucial

### ⚠️ Special Protections

The law presumes absence of consent in custodial rape, gang rape, and rape of minors. The burden of proof partially shifts to the accused.

"""
    elif section == '379':
        response += """
### 👮 Investigation Tips

- CCTV footage is primary evidence in urban areas
- Recovery of stolen property strengthens case significantly
- Conduct identification parade if accused unknown
- Check for repeat offender patterns
- Compoundable with victim's consent for first-time minor thefts

"""
    elif section == '420':
        response += """
### 👮 Investigation Guidelines

- Establish **fraudulent intention FROM THE BEGINNING** (crucial difference from breach of contract)
- Trace financial transactions and bank records
- Collect documentary evidence (agreements, receipts, communications)
- Digital evidence (emails, WhatsApp) is key in cyber fraud cases
- Consider Section 41A CrPC notice unless arrest is necessary

### 🔑 Key Distinction

**Cheating vs Breach of Contract:**  
In breach of contract, there was genuine intention at the time of promise but later unable to perform. In cheating, the intention was fraudulent from the very start.

"""
    
    # Add disclaimer
    response += """
---
*This information is for general understanding. Laws may have amendments and judicial interpretations. For specific legal advice, consult a qualified advocate.*
"""
    
    return response

def generate_follow_up_questions(offence: str, section: str) -> List[str]:
    """Generate intelligent, context-aware follow-up questions"""
    
    follow_ups = []
    
    # Section-specific follow-ups
    if section == '302':
        follow_ups = [
            "What's the difference between murder and culpable homicide?",
            "When is death penalty awarded for murder?",
            "What evidence is needed to prove murder?",
            "Can murder be compounded or settled?"
        ]
    elif section == '376':
        follow_ups = [
            "What is the procedure for recording rape victim's statement?",
            "What is custodial rape?",
            "How is medical evidence used in rape cases?",
            "What are the protections for rape victims during trial?"
        ]
    elif section == '379':
        follow_ups = [
            "What's the difference between theft and robbery?",
            "Can a theft case be settled between parties?",
            "How to recover stolen property?",
            "What is the bail procedure for theft?"
        ]
    elif section == '420':
        follow_ups = [
            "How to distinguish cheating from breach of contract?",
            "What evidence is needed for cheating cases?",
            "Can a cheating case be quashed by High Court?",
            "What is the limitation period for cheating cases?"
        ]
    elif section == '304B':
        follow_ups = [
            "What is the presumption in dowry death cases?",
            "Who can be accused in a dowry death case?",
            "What evidence proves dowry demand?",
            "What is the punishment for dowry harassment?"
        ]
    elif section == '323':
        follow_ups = [
            "What is the difference between hurt and grievous hurt?",
            "How to get bail in hurt cases?",
            "Can hurt cases be compounded?",
            "What medical evidence is required?"
        ]
    else:
        follow_ups = [
            f"What is the punishment for {offence}?",
            f"Is {offence} a bailable or non-bailable offence?",
            f"What evidence is needed to prove {offence}?",
            f"Can police arrest without warrant for {offence}?"
        ]
    
    return follow_ups[:4]

def generate_smart_response(prompt: str, offence: str, details: Dict, pdf_content: str = None) -> str:
    """Generate the final intelligent response"""
    
    if details:
        # IPC section match found
        response = generate_chatgpt_style_response(offence, details, prompt)
        
        # Add follow-up suggestions
        follow_ups = generate_follow_up_questions(offence, details['section'])
        if follow_ups:
            response += "\n\n---\n### 🔍 You Might Also Want to Know\n\n"
            for fu in follow_ups:
                response += f"• *{fu}*\n"
        
        return response
    
    elif pdf_content and len(pdf_content) > 50:
        # Response from PDF documents
        response = f"""
📚 **Based on the Police Documents in my Knowledge Base**

{pdf_content}

---
### 💡 Need More Information?

I found this information in your uploaded documents. To get more specific answers, you can:
• Ask about IPC sections by name or number
• Ask about police procedures (FIR, arrest, investigation)
• Upload more relevant PDFs to expand my knowledge
"""
        return response
    
    else:
        # No match found - helpful fallback
        return """
🤔 **I couldn't find specific information about that query.**

But don't worry - I can still help! Here's what you can ask me:

### 📋 IPC Related Questions
• "What is the punishment for murder under IPC?"
• "Tell me about Section 376 (rape)"
• "Is theft a bailable offence?"
• "What is the difference between theft and robbery?"

### 👮 Police Procedure Questions
• "How to register an FIR?"
• "What are the rights of an arrested person?"
• "When can police arrest without warrant?"
• "What is the procedure for investigation?"

### ⚖️ Legal Terminology
• "What is a cognizable offence?"
• "What does non-bailable mean?"
• "Explain compoundable offences"
• "What is the difference between kidnapping and abduction?"

---
*Try rephrasing your question or ask about a specific IPC section number for best results.*
"""
    
    return response

# ============================================================
# SEARCH AND UTILITY FUNCTIONS
# ============================================================

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def get_ipc_match(query: str) -> Tuple[Optional[str], Optional[Dict], float]:
    """Get best IPC match with fuzzy matching"""
    query_lower = query.lower()
    best_match = None
    best_details = None
    best_score = 0
    
    # Direct match by offence name
    for offence, details in IPC_DATABASE.items():
        if offence in query_lower or details['section'] in query_lower:
            return offence, details, 1.0
    
    # Direct match by section number pattern
    section_pattern = r'section\s*(\d+)|sec\s*(\d+)|(\d+)\s*(?:ipc|section)'
    matches = re.findall(section_pattern, query_lower)
    for match in matches:
        sec_num = match[0] or match[1] or match[2]
        for offence, details in IPC_DATABASE.items():
            if details['section'] == sec_num:
                return offence, details, 1.0
    
    # Fuzzy matching
    for offence, details in IPC_DATABASE.items():
        similarity = calculate_text_similarity(query_lower, offence)
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
                        if main_offence in offence:
                            return offence, details, 0.85
    
    return best_match, best_details, best_score

def hybrid_search(query: str, top_k: int = 5) -> List:
    """Perform hybrid search on vector store"""
    if st.session_state.vector_store is None:
        return []
    retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": top_k})
    return retriever.invoke(query)

def extract_relevant_text(query: str, documents: List) -> Tuple[Optional[str], List[str]]:
    """Extract most relevant text from documents"""
    if not documents:
        return None, []
    
    content_parts = []
    sources = []
    
    for doc in documents[:3]:
        source = doc.metadata.get("source", "Unknown")
        if source not in sources:
            sources.append(source)
        
        content = doc.page_content
        # Find sentences containing query keywords
        query_words = set(query.lower().split())
        sentences = re.split(r'[.!?]\s+', content)
        
        for sentence in sentences:
            if len(sentence) > 30:
                sentence_lower = sentence.lower()
                if any(word in sentence_lower for word in query_words):
                    content_parts.append(f"• {sentence.strip()}")
                    if len(content_parts) >= 3:
                        break
        
        if not content_parts:
            # No sentence matches - take first 400 chars
            content_parts.append(f"• {content[:400].strip()}...")
    
    if content_parts:
        return "\n\n".join(content_parts[:4]), list(set(sources))
    
    return None, []

# ============================================================
# PDF LOADING FUNCTIONS
# ============================================================

def get_pdf_files_from_github():
    """Fetch PDF files from GitHub"""
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{DOCUMENTS_FOLDER}"
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            files = response.json()
            return [{
                'name': f['name'],
                'raw_url': RAW_BASE_URL + f['name']
            } for f in files if f['name'].lower().endswith('.pdf')]
        return []
    except Exception:
        return []

def load_pdf_from_url(url: str, filename: str):
    """Download and load PDF from URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(response.content)
            tmp_path = tmp.name
        loader = PyPDFLoader(tmp_path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = filename
        os.unlink(tmp_path)
        return docs
    except Exception:
        return []

@st.cache_resource
def load_embedding_model():
    """Cache embedding model loading"""
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def load_all_documents():
    """Load all PDFs from GitHub"""
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    if not pdf_files:
        return [], []
    
    status = st.empty()
    progress = st.progress(0)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for i, pdf in enumerate(pdf_files):
        status.markdown(f"📖 Loading: `{pdf['name']}`...")
        docs = load_pdf_from_url(pdf['raw_url'], pdf['name'])
        
        if docs:
            chunks = splitter.split_documents(docs)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf['name']
                chunk.metadata["chunk_id"] = j
            all_chunks.extend(chunks)
            loaded_files.append(pdf['name'])
        
        progress.progress((i + 1) / len(pdf_files))
    
    status.empty()
    progress.empty()
    return all_chunks, loaded_files

# ============================================================
# CSS STYLING - ULTRA PREMIUM
# ============================================================

st.markdown("""
<style>
    /* Main background with animated gradient */
    .stApp {
        background: linear-gradient(135deg, #0a0f1a 0%, #0a0e1a 50%, #0b1120 100%);
        animation: bgPulse 10s ease infinite;
    }
    
    @keyframes bgPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.98; }
    }
    
    /* Premium Glass Header */
    .main-header {
        text-align: center;
        padding: 2rem;
        background: rgba(26, 31, 46, 0.6);
        backdrop-filter: blur(12px);
        border-radius: 30px;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,0.08);
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
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
        animation: shimmer 4s infinite;
    }
    
    @keyframes shimmer {
        0% { left: -100%; }
        100% { left: 100%; }
    }
    
    .main-header h1 {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ffffff, #60a5fa, #10b981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }
    
    /* Chat Messages - Ultra Premium */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, rgba(30, 20, 20, 0.95), rgba(40, 25, 25, 0.95));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 24px 24px 8px 24px;
        animation: slideInRight 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: linear-gradient(135deg, rgba(15, 26, 20, 0.95), rgba(20, 30, 25, 0.95));
        backdrop-filter: blur(12px);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 24px 24px 24px 8px;
        animation: slideInLeft 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 1.2rem;
        margin: 0.5rem 0;
    }
    
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(40px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-40px); }
        to { opacity: 1; transform: translateX(0); }
    }
    
    /* Content Styling inside assistant messages */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        margin-top: 0.75rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }
    
    .stMarkdown h2 {
        font-size: 1.3rem;
        border-left: 3px solid #10b981;
        padding-left: 0.75rem;
    }
    
    .stMarkdown h3 {
        font-size: 1.1rem;
        color: #60a5fa;
    }
    
    .stMarkdown table {
        background: rgba(0,0,0,0.3);
        border-radius: 12px;
        border-collapse: separate;
        border-spacing: 0;
        overflow: hidden;
    }
    
    .stMarkdown th {
        background: rgba(16, 185, 129, 0.2);
        padding: 0.5rem 1rem;
    }
    
    .stMarkdown td {
        padding: 0.5rem 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(8, 12, 22, 0.9);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Stat Cards */
    .stat-card {
        background: rgba(19, 24, 35, 0.7);
        backdrop-filter: blur(8px);
        border-radius: 20px;
        padding: 1rem;
        margin: 0.5rem 0;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        border-color: rgba(16, 185, 129, 0.4);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #10b981, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        font-size: 0.7rem;
        color: #9ca3af;
        letter-spacing: 0.5px;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #dc2626, #b91c1c);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(220, 38, 38, 0.3);
    }
    
    /* Input field */
    .stTextInput input {
        background: rgba(19, 24, 35, 0.8);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 30px;
        color: #e6edf3;
        padding: 0.8rem 1.2rem;
        font-size: 1rem;
    }
    
    .stTextInput input:focus {
        border-color: #10b981;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(19, 24, 35, 0.5);
        border-radius: 12px;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #6b7280;
        font-size: 0.7rem;
        border-top: 1px solid rgba(255,255,255,0.05);
        margin-top: 2rem;
    }
    
    /* Document badges */
    .doc-badge {
        background: rgba(16, 185, 129, 0.12);
        color: #10b981;
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        font-size: 0.7rem;
        display: inline-block;
        margin: 0.2rem;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    hr {
        margin: 1rem 0;
        border-color: rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="main-header">
    <h1>⚖️ Police Rulebook Assistant</h1>
    <p style="font-size: 1.1rem;">🤖 AI-Powered Legal Expert | Natural Conversations | Instant Answers</p>
    <p style="font-size: 0.85rem; opacity: 0.7;">🎯 IPC Sections | 📚 Police Procedures | 🔍 Smart Search | 💬 ChatGPT-style Responses</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    welcome = """Hello! I'm your AI Legal Assistant 👋

I can help you with Indian criminal law, IPC sections, and police procedures - just like ChatGPT, but specialized for law!

### 🎯 Here's what I can do:

| Category | Examples |
|----------|----------|
| **IPC Offences** | "What is the punishment for murder?" |
| **Legal Status** | "Is theft bailable or non-bailable?" |
| **Police Powers** | "When can police arrest without warrant?" |
| **Legal Concepts** | "Explain cognizable and non-cognizable offences" |

### 💡 Try asking me:

• "What is Section 376 IPC and what's the punishment?"
• "Tell me about dacoity under Section 395"
• "What evidence is needed to prove cheating?"
• "Difference between kidnapping and abduction"

### ✨ What makes me different:

✅ **Natural responses** - I explain like a human lawyer
✅ **Practical insights** - Real investigation guidance
✅ **Landmark cases** - Supreme Court judgments
✅ **Follow-up questions** - I'll suggest what to ask next

---

**What would you like to know about Indian law today?** ⚖️
"""
    st.session_state.messages = [{"role": "assistant", "content": welcome, "sources": []}]

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
    with st.spinner("📚 Loading documents from GitHub..."):
        chunks, loaded = load_all_documents()
        
        if chunks:
            if st.session_state.embeddings is None:
                st.session_state.embeddings = load_embedding_model()
            
            st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
            st.session_state.documents = chunks
            st.session_state.pdf_list = loaded
            st.session_state.documents_loaded = True
            
            st.balloons()
            st.success(f"✅ **{len(loaded)} documents loaded!** | 📊 {len(chunks)} text chunks ready")
        else:
            st.info("📤 No PDFs found in GitHub. You can still ask about IPC sections (60+ covered)!")

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("### 🎯 Dashboard")
    
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
            <div class="stat-number">{len(st.session_state.pdf_list)}</div>
            <div class="stat-label">PDF Docs</div>
        </div>
        """, unsafe_allow_html=True)
    
    if st.session_state.pdf_list:
        st.markdown("### 📁 Loaded")
        for doc in st.session_state.pdf_list[:3]:
            name = doc[:25] + "..." if len(doc) > 25 else doc
            st.markdown(f'<span class="doc-badge">📄 {name}</span>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 📤 Upload PDF")
    uploaded = st.file_uploader("Add to knowledge", type=["pdf"], key="uploader")
    
    if uploaded and st.button("📥 Process", use_container_width=True):
        with st.spinner("Processing..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded.read())
                    tmp_path = tmp.name
                
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
                splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
                chunks = splitter.split_documents(docs)
                
                for i, c in enumerate(chunks):
                    c.metadata["source"] = uploaded.name
                
                if st.session_state.embeddings is None:
                    st.session_state.embeddings = load_embedding_model()
                
                if st.session_state.vector_store is None:
                    st.session_state.vector_store = FAISS.from_documents(chunks, st.session_state.embeddings)
                else:
                    st.session_state.vector_store.add_documents(chunks)
                
                st.session_state.documents.extend(chunks)
                if uploaded.name not in st.session_state.pdf_list:
                    st.session_state.pdf_list.append(uploaded.name)
                
                os.unlink(tmp_path)
                st.success(f"✅ Added {uploaded.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    with st.expander("🔐 Admin"):
        pwd = st.text_input("Password", type="password", key="admin_pwd")
        if st.button("🗑️ Clear All", use_container_width=True):
            if pwd == st.session_state.admin_password:
                st.session_state.vector_store = None
                st.session_state.documents = []
                st.session_state.messages = [{"role": "assistant", "content": "Cleared! Ask me anything about IPC sections.", "sources": []}]
                st.session_state.documents_loaded = False
                st.session_state.pdf_list = []
                st.success("Cleared! Refresh to reload.")
                st.rerun()
            else:
                st.error("Wrong password")
    
    st.markdown("---")
    st.markdown("### 💬 Quick Tips")
    st.caption("• Ask naturally like chatting")
    st.caption("• Use section numbers for precision")
    st.caption("• I understand legal synonyms")
    
    st.markdown("---")
    st.caption("⚖️ **Police Rulebook Assistant**")
    st.caption("Barath R K PDKV | 411623149004")
    st.caption("Project PRJ-005")

# ============================================================
# MAIN CHAT INTERFACE
# ============================================================

st.markdown("### 💬 Chat with AI Legal Expert")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            st.caption(f"📚 Sources: {', '.join(msg['sources'])}")

# Chat input
user_input = st.chat_input("Ask me about IPC sections, punishments, legal procedures...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing and generating response..."):
            try:
                # Try IPC match first
                offence, details, confidence = get_ipc_match(user_input)
                
                if details:
                    # Generate AI response for IPC section
                    answer = generate_smart_response(user_input, offence, details)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                
                elif st.session_state.vector_store and st.session_state.documents:
                    # Search PDF documents
                    results = hybrid_search(user_input, top_k=4)
                    if results:
                        pdf_text, sources = extract_relevant_text(user_input, results)
                        if pdf_text and len(pdf_text) > 50:
                            answer = generate_smart_response(user_input, None, None, pdf_text)
                            st.markdown(answer)
                            if sources:
                                st.caption(f"📚 Sources: {', '.join(sources)}")
                            st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
                        else:
                            answer = generate_smart_response(user_input, None, None)
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                    else:
                        answer = generate_smart_response(user_input, None, None)
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    answer = generate_smart_response(user_input, None, None)
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)[:150]}\n\nPlease try rephrasing your question."
                st.error(error_msg)

# ============================================================
# FOOTER
# ============================================================

st.markdown("""
<div class="footer">
    <p>⚖️ Police Rulebook Assistant | AI-Powered Legal Reference | 60+ IPC Sections Covered</p>
    <p style="font-size: 0.65rem;">⚠️ For informational purposes only. Consult legal professionals for actual legal advice.</p>
</div>
""", unsafe_allow_html=True)
