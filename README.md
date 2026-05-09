# 👮 Police Rulebook Assistant

<div align="center">

**Project PRJ-005** | **Barath R K PDKV** | **411623149004** | **Department: Cyber**

[![Streamlit App](https://img.shields.io/badge/Streamlit-Live_App-red?style=for-the-badge&logo=streamlit)](https://police-rulebook-assistant-new.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com/Barath-RK/police-rulebook-assistant-new)
[![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

</div>

---

## 📋 Project Overview

A **RAG (Retrieval-Augmented Generation)** document assistant that searches SOPs, complaint filing manuals, and citizen procedure documents for police departments. Built with modern AI technologies to provide accurate, citation-backed answers from uploaded legal documents.

### 🎯 Key Features

| Feature | Description |
|---------|-------------|
| 📄 **PDF Upload** | Upload police documents, SOPs, legal acts |
| 🔍 **Semantic Search** | AI-powered search using FAISS vector database |
| 📚 **Citation-backed Answers** | Every answer includes source document |
| 🔐 **Admin Panel** | Password-protected knowledge base management |
| 💬 **Chat History** | Complete conversation logging |
| 🌐 **Auto-load from GitHub** | PDFs auto-load from `Documents` folder |

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| **Streamlit** | Frontend UI framework |
| **FastAPI** | Backend API server |
| **LangChain** | RAG and document processing |
| **FAISS** | Vector database for similarity search |
| **HuggingFace Embeddings** | Text embeddings (all-MiniLM-L6-v2) |
| **PyPDF** | PDF text extraction |


## 🚀 Live Demo

🔗 **Live Application:** - http://police-rulebook-assistant.streamlit.app/

---

## 📸 Screenshots

### Home Page
![Home Page](https://raw.githubusercontent.com/Barath-RK/police-rulebook-assistant-new/main/screenshots/home.png)

### Chat Interface
![Chat Interface](https://raw.githubusercontent.com/Barath-RK/police-rulebook-assistant-new/main/screenshots/chat.png)

### IPC Section Answer
![IPC Answer](https://raw.githubusercontent.com/Barath-RK/police-rulebook-assistant-new/main/screenshots/answer.png)

### Admin Panel
![Admin Panel](https://raw.githubusercontent.com/Barath-RK/police-rulebook-assistant-new/main/screenshots/admin.png)

---

## 📁 Repository Structure
