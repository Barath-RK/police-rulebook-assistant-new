
import os
import tempfile
import requests
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

app = FastAPI(title="Police Rulebook Assistant API", version="2.0.0")

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# GLOBAL VARIABLES
# ============================================================

vector_store = None
all_chunks = []
embeddings = None
pdf_list = []
documents_loaded = False

# IPC Section Mappings for direct answers
IPC_SECTIONS = {
    "murder": {"section": "302", "text": "Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine."},
    "theft": {"section": "379", "text": "Whoever commits theft shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both."},
    "robbery": {"section": "392", "text": "Whoever commits robbery shall be punished with rigorous imprisonment for a term which may extend to ten years, and shall also be liable to fine."},
    "rape": {"section": "376", "text": "Whoever commits rape shall be punished with rigorous imprisonment for a term which shall not be less than ten years, but which may extend to imprisonment for life, and shall also be liable to fine."},
    "cheating": {"section": "420", "text": "Whoever cheats and thereby dishonestly induces delivery of property shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine."},
    "kidnapping": {"section": "363", "text": "Whoever kidnaps any person from India or from lawful guardianship shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine."},
    "dowry death": {"section": "304B", "text": "Whoever commits dowry death shall be punished with imprisonment for a term which shall not be less than seven years but which may extend to imprisonment for life."},
    "criminal breach of trust": {"section": "406", "text": "Whoever commits criminal breach of trust shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both."},
    "defamation": {"section": "500", "text": "Whoever defames another shall be punished with simple imprisonment for a term which may extend to two years, or with fine, or with both."},
    "hurt": {"section": "323", "text": "Whoever voluntarily causes hurt shall be punished with imprisonment of either description for a term which may extend to one year, or with fine which may extend to one thousand rupees, or with both."},
    "grievous hurt": {"section": "325", "text": "Whoever voluntarily causes grievous hurt shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine."},
    "extortion": {"section": "384", "text": "Whoever commits extortion shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both."},
    "dacoity": {"section": "395", "text": "Whoever commits dacoity shall be punished with imprisonment for life, or with rigorous imprisonment for a term which may extend to ten years, and shall also be liable to fine."},
    "forgery": {"section": "465", "text": "Whoever commits forgery shall be punished with imprisonment of either description for a term which may extend to two years, or with fine, or with both."},
    "criminal intimidation": {"section": "506", "text": "Whoever commits criminal intimidation shall be punished with imprisonment of either description for a term which may extend to two years, or with fine, or with both."},
    "waging war": {"section": "121", "text": "Whoever wages war against the Government of India shall be punished with death or imprisonment for life, and shall also be liable to fine."},
}

class Question(BaseModel):
    query: str

class Answer(BaseModel):
    answer: str
    sources: Optional[List[str]] = []
    section: Optional[str] = None

# ============================================================
# API ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {"message": "Police Rulebook Assistant API", "status": "running", "version": "2.0.0"}

@app.get("/status")
def get_status():
    return {
        "documents_loaded": len(pdf_list),
        "chunks": len(all_chunks),
        "pdfs": pdf_list,
        "ready": documents_loaded
    }

@app.post("/refresh")
async def refresh_knowledge_base():
    """Refresh documents from GitHub"""
    global vector_store, all_chunks, pdf_list, documents_loaded, embeddings
    vector_store = None
    all_chunks = []
    pdf_list = []
    documents_loaded = False
    await load_documents()
    return {"status": "refreshed", "documents": len(pdf_list), "chunks": len(all_chunks)}

@app.post("/ask")
async def ask_question(question: Question):
    """Ask a question and get relevant answer"""
    global vector_store, all_chunks, documents_loaded
    
    if not documents_loaded or not all_chunks:
        return Answer(
            answer="No documents loaded. Please refresh the knowledge base.",
            sources=[],
            section=None
        )
    
    query = question.query.lower()
    
    # Step 1: Check IPC Section Mappings first
    for crime, info in IPC_SECTIONS.items():
        if crime in query:
            return Answer(
                answer=f"**Section {info['section']} of the Indian Penal Code:**\n\n{info['text']}",
                sources=["Indian Penal Code"],
                section=info['section']
            )
    
    # Step 2: Search in vector store
    if vector_store:
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        results = retriever.invoke(question.query)
        
        if results:
            best_answer = ""
            best_score = 0
            
            for doc in results:
                content = doc.page_content
                score = 0
                query_words = query.split()
                for word in query_words:
                    if word.lower() in content.lower():
                        score += 1
                
                if score > best_score:
                    best_score = score
                    sentences = re.split(r'[.!?]\s+', content)
                    relevant = []
                    for sentence in sentences:
                        if len(sentence) > 30 and any(word.lower() in sentence.lower() for word in query_words):
                            relevant.append(sentence.strip())
                    
                    if relevant:
                        best_answer = ". ".join(relevant[:3])
                    else:
                        best_answer = content[:600]
            
            if best_answer:
                return Answer(
                    answer=best_answer,
                    sources=list(set([doc.metadata.get("source", "Unknown") for doc in results[:3]])),
                    section=None
                )
    
    # Step 3: Fallback - Search through all chunks directly
    query_words = set(query.split())
    scored_chunks = []
    for chunk in all_chunks:
        content = chunk.page_content.lower()
        score = sum(1 for word in query_words if word in content)
        if score > 0:
            scored_chunks.append((score, chunk))
    
    scored_chunks.sort(reverse=True, key=lambda x: x[0])
    
    if scored_chunks:
        best_chunk = scored_chunks[0][1]
        content = best_chunk.page_content
        sentences = re.split(r'[.!?]\s+', content)
        relevant = [s for s in sentences[:3] if len(s) > 30]
        answer = ". ".join(relevant) if relevant else content[:500]
        return Answer(
            answer=answer,
            sources=[best_chunk.metadata.get("source", "Unknown")],
            section=None
        )
    
    return Answer(
        answer="I couldn't find specific information about that. Please try rephrasing your question.",
        sources=[],
        section=None
    )

# ============================================================
# DOCUMENT LOADING
# ============================================================

def get_pdf_files_from_github():
    try:
        api_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{DOCUMENTS_FOLDER}"
        response = requests.get(api_url)
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
    except Exception as e:
        print(f"Error fetching PDFs: {e}")
        return []

def load_pdf_from_url(url: str, filename: str):
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
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

async def load_documents():
    global vector_store, all_chunks, pdf_list, documents_loaded, embeddings
    
    all_chunks = []
    loaded_files = []
    
    pdf_files = get_pdf_files_from_github()
    
    if not pdf_files:
        print("No PDF files found in GitHub Documents folder")
        documents_loaded = False
        return
    
    if embeddings is None:
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    for pdf_info in pdf_files:
        documents = load_pdf_from_url(pdf_info['raw_url'], pdf_info['name'])
        if documents:
            chunks = splitter.split_documents(documents)
            for j, chunk in enumerate(chunks):
                chunk.metadata["source"] = pdf_info['name']
                chunk.metadata["chunk_id"] = j
                chunk.metadata["total_chunks"] = len(chunks)
            all_chunks.extend(chunks)
            loaded_files.append(pdf_info['name'])
            print(f"Loaded {pdf_info['name']} - {len(chunks)} chunks")
    
    if all_chunks:
        vector_store = FAISS.from_documents(all_chunks, embeddings)
        pdf_list = loaded_files
        documents_loaded = True
        print(f"Total loaded: {len(loaded_files)} files, {len(all_chunks)} chunks")

@app.on_event("startup")
async def startup_event():
    """Load documents when API starts"""
    print("Starting FastAPI server, loading documents from GitHub...")
    await load_documents()
    print(f"Ready! Loaded {len(pdf_list)} documents")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
