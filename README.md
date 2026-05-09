# 👮‍♂️ Police Rulebook Assistant

### *AI-Powered RAG Document Intelligence System for Law Enforcement & Public Safety*

<div align="center">

<img src="https://img.shields.io/badge/GENAI-RAG%20Assistant-blue?style=for-the-badge&logo=openai&logoColor=white" />
<img src="https://img.shields.io/badge/FastAPI-Backend-green?style=for-the-badge&logo=fastapi" />
<img src="https://img.shields.io/badge/Streamlit-Frontend-red?style=for-the-badge&logo=streamlit" />
<img src="https://img.shields.io/badge/LangChain-AI%20Framework-yellow?style=for-the-badge" />
<img src="https://img.shields.io/badge/FAISS-Vector%20Database-purple?style=for-the-badge" />
<img src="https://img.shields.io/badge/License-MIT-success?style=for-the-badge" />

<br><br>

# 🚔 Police Rulebook Assistant

### *Project Code: PRJ-005*

### 🧑‍💻 Developed By

## **Barath R K PDKV**

**Reg No:** 411623149004
**Department:** Cyber Security

<br>

### 🌐 Live Project Links

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Visit_Now-red?style=for-the-badge)](https://police-rulebook-assistant.streamlit.app)

[![GitHub Repository](https://img.shields.io/badge/💻_GitHub-Repository-black?style=for-the-badge\&logo=github)](https://github.com/Barath-RK/police-rulebook-assistant-new)

[![MIT License](https://img.shields.io/badge/📜_MIT-License-green?style=for-the-badge)](LICENSE)

</div>

---

# 📌 Project Overview

The **Police Rulebook Assistant** is an advanced **Retrieval-Augmented Generation (RAG)** based AI assistant designed for **law enforcement departments**, **public safety organizations**, and **citizen support systems**.

The platform enables users to upload and search through:

* 📘 Police SOPs
* 📑 IPC/CrPC legal manuals
* 📝 Complaint filing procedures
* 📂 Investigation guidelines
* 📚 Citizen support documentation

Using **Natural Language Processing (NLP)** and **Generative AI**, the assistant provides:

✅ Accurate Answers
✅ Citation-backed Responses
✅ Semantic Document Search
✅ Intelligent Retrieval
✅ Secure Knowledge Base Management

---

# 🎯 Core Objectives

✔ Build an AI-powered legal document assistant
✔ Improve accessibility to police documentation
✔ Reduce manual searching time
✔ Provide citation-backed legal responses
✔ Demonstrate practical implementation of RAG architecture
✔ Deploy a scalable and modern GenAI solution

---

# ✨ Key Features

| 🚀 Feature                | 📖 Description                                               |
| ------------------------- | ------------------------------------------------------------ |
| 📄 Document Upload        | Upload PDFs, SOPs, legal manuals, acts & procedure documents |
| 🧠 AI Semantic Search     | FAISS-powered similarity search using embeddings             |
| 💬 Intelligent Chatbot    | Ask questions in natural language                            |
| 📚 Citation-Based Answers | Every response includes document references                  |
| 🔐 Admin Panel            | Secure admin management & KB refresh                         |
| 🕘 Chat History           | Conversation logging & retrieval                             |
| 🌐 GitHub Auto Loader     | Automatically loads PDFs from repository                     |
| ⚡ Fast Retrieval          | Optimized vector search for quick responses                  |
| 🛡 Access Control         | Basic authentication for admin functionalities               |
| 📊 Scalable Architecture  | Built with modular backend structure                         |

---

# 🧠 System Architecture

```text
                ┌─────────────────────┐
                │     User Query      │
                └─────────┬───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │    Streamlit UI     │
                └─────────┬───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │     FastAPI API     │
                └─────────┬───────────┘
                          │
                          ▼
                ┌─────────────────────┐
                │     LangChain       │
                │  RAG Pipeline Logic │
                └─────────┬───────────┘
                          │
          ┌───────────────┴────────────────┐
          ▼                                ▼
┌──────────────────┐             ┌──────────────────┐
│ HuggingFace Emb. │             │    FAISS DB      │
└──────────────────┘             └──────────────────┘
          │                                │
          └───────────────┬────────────────┘
                          ▼
                ┌─────────────────────┐
                │  Citation Response  │
                └─────────────────────┘
```

---

# 🛠️ Technology Stack

| Technology                 | Purpose                      |
| -------------------------- | ---------------------------- |
| **Python**                 | Core Programming Language    |
| **FastAPI**                | Backend API Framework        |
| **Streamlit**              | Frontend User Interface      |
| **LangChain**              | RAG Pipeline & Orchestration |
| **FAISS**                  | Vector Similarity Search     |
| **HuggingFace Embeddings** | Text Embedding Model         |
| **PyPDFLoader**            | PDF Parsing                  |
| **Sentence Transformers**  | Semantic Embeddings          |
| **GitHub**                 | Version Control              |
| **Streamlit Cloud**        | Deployment                   |

---

# 📸 Project Screenshots

## 🖥 Dashboard Interface

<p align="center">
  <img src="https://github.com/user-attachments/assets/5f69c0f5-6bd5-48ed-a746-d422346dd219" width="700"/>
</p>

---

## 📂 File Upload & Validation

<p align="center">
  <img src="YOUR_IMAGE_LINK_HERE" width="700"/>
</p>

---

## 🔐 Admin Panel & Test Cases

<p align="center">
  <img src="https://github.com/user-attachments/assets/5f69c0f5-6bd5-48ed-a746-d422346dd219" width="350"/>
</p>

---

## 💬 AI Chatbot Interaction

<p align="center">
  <img src="YOUR_IMAGE_LINK_HERE" width="700"/>
</p>

---

## 🕘 Chat History Logging

<p align="center">
  <img src="https://github.com/user-attachments/assets/102d8c0c-680d-4bfd-aecd-28659ae2b5a9" width="450"/>
</p>

---

# 🔍 Sample AI Response

## Query:

> *What is the difference between Theft and Robbery under IPC?*

## Response:

```text
Theft (Section 378-379, IPC):
- Dishonest taking of movable property without consent
- No force or threat involved
- Punishment: Up to 3 years imprisonment or fine or both
- Bailable offence

Robbery (Section 390-392, IPC):
- Theft or extortion accompanied by force or threat
- Involves violence, fear, or instant threat
- Punishment: Rigorous imprisonment up to 10 years + fine
- Non-bailable offence

Key Difference:
Robbery includes force or threat of hurt/death, while theft does not.
```

---

# 📂 Folder Structure

```bash
Police-Rulebook-Assistant/
│
├── backend/
│   ├── main.py
│   ├── rag_pipeline.py
│   ├── vector_store.py
│   └── requirements.txt
│
├── frontend/
│   ├── app.py
│   └── components/
│
├── documents/
│   ├── ipc_manual.pdf
│   ├── sop_guidelines.pdf
│   └── complaint_procedures.pdf
│
├── screenshots/
├── chat_history/
├── tests/
├── LICENSE
├── README.md
└── requirements.txt
```

---

# ⚙️ Installation & Setup

# 📋 Prerequisites

Ensure the following are installed:

| Software | Version |
| -------- | ------- |
| Python   | 3.11+   |
| Git      | Latest  |
| pip      | Latest  |

---

# 🚀 Installation Steps

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Barath-RK/police-rulebook-assistant-new.git

cd police-rulebook-assistant-new
```

---

## 2️⃣ Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
source venv/bin/activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Start FastAPI Backend

```bash
uvicorn main:app --reload
```

---

## 5️⃣ Start Streamlit Frontend

```bash
streamlit run app.py
```

---

# 🌐 Deployment

The application is deployed using **Streamlit Cloud**.

### 🔗 Live URL

👉 [https://police-rulebook-assistant.streamlit.app](https://police-rulebook-assistant.streamlit.app)

---

# 🧪 Testing & Validation

## ✔ Functional Testing

| Test Case            | Status   |
| -------------------- | -------- |
| PDF Upload           | ✅ Passed |
| Document Parsing     | ✅ Passed |
| Chunk Generation     | ✅ Passed |
| Citation Retrieval   | ✅ Passed |
| Semantic Search      | ✅ Passed |
| Admin Authentication | ✅ Passed |
| Chat History Logging | ✅ Passed |

---

# 📈 Project Evaluation Coverage

| Evaluation Component | Status            |
| -------------------- | ----------------- |
| Implementation       | ✅ Completed       |
| Testing & Validation | ✅ Completed       |
| Live Deployment      | ✅ Completed       |
| GitHub Commits       | ✅ Regular Updates |
| README Documentation | ✅ Completed       |
| Viva Preparation     | ✅ Ready           |

---

# 🔒 Security Best Practices

✅ API keys hidden using environment variables
✅ Admin authentication implemented
✅ Sensitive credentials excluded from repository
✅ Secure document handling process
✅ Input validation enabled

---

# 📚 Official References

| Resource       | Link                                                                             |
| -------------- | -------------------------------------------------------------------------------- |
| FastAPI Docs   | [https://fastapi.tiangolo.com/tutorial/](https://fastapi.tiangolo.com/tutorial/) |
| LangChain Docs | [https://docs.langchain.com/](https://docs.langchain.com/)                       |
| Streamlit Docs | [https://docs.streamlit.io/](https://docs.streamlit.io/)                         |
| Chroma Docs    | [https://docs.trychroma.com/](https://docs.trychroma.com/)                       |

---

# 📅 3-Week Development Roadmap

## ✅ Week 1

* Knowledge base setup
* PDF parsing
* Basic chatbot interface

## ✅ Week 2

* Retrieval pipeline
* Citation generation
* Admin refresh workflow

## ✅ Week 3

* Chat history
* Access control
* UI improvements
* Deployment & documentation

---

# 🏆 Project Highlights

⭐ Real-world Public Safety Use Case
⭐ Practical RAG Architecture Implementation
⭐ End-to-End AI Application Deployment
⭐ Modern GenAI Stack Integration
⭐ Legal & Procedural Document Intelligence

---

# 📜 License

This project is licensed under the **MIT License**.

```text
MIT License © 2026 Barath R K PDKV
```

---

# 🙌 Acknowledgements

Special thanks to:

* FastAPI Documentation
* LangChain Community
* Streamlit Team
* HuggingFace
* FAISS Research Team

---

<div align="center">

# 🚔 Police Rulebook Assistant

### *Empowering Public Safety with Generative AI*

⭐ If you like this project, give it a star on GitHub ⭐

</div>
