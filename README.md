# 🐕 K9MATCH: Ethical Canine Matching Platform

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1%2B-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/License-Academic-lightgrey.svg)](#)
[![Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)](#)

> **K9MATCH** is an ethical, full-stack canine partner discovery, pedigree verification, and localized pet healthcare networking platform. Engineered to replace unverified classifieds and informal breeding networks, K9MATCH enforces biological compatibility, Kennel Club of India (KCI) certification vetting, proximity-based spatial search, and automated legal breeding agreements.

---

## 🌟 Key Features

- **📍 Geospatial Proximity Matchmaking**: 
  - Spherical trigonometric **Haversine Distance Engine** mapped to Indian city coordinates.
  - Interactive radial distance filtering (5 km – 100+ km) with offline in-memory geocoding fallback.
- **🛡️ Strict Biological Compatibility & Guardrails**:
  - Algorithmic self-match prevention (excludes user's own dogs).
  - Mandatory opposite-gender biological gating (Male + Female validation).
  - Pedigree classification (Purebred vs. Crossbreed).
- **📋 KCI Document & Health Vetting**:
  - Human-in-the-loop administrative moderation panel for microchip & KCI certificate approval.
  - Transparent trust tags (`Verified` / `Pending Verification`).
- **💬 Permission-Isolated Real-Time Chat**:
  - Secure two-way match negotiation (Stud Fee, Pick of Litter, Puppy Sharing).
  - Direct messaging threads strictly unlocked upon mutual request acceptance.
- **📄 Automated PDF Document Synthesis (ReportLab)**:
  - **Canine Health Passport**: Complete pedigree lineage, microchip ID, and vaccination log.
  - **Legal Canine Breeding Contract**: Auto-filled binding agreement capturing owner terms and signatures.
- **🏥 Geocoded Veterinary Emergency Directory**:
  - Curated database of 24/7 emergency veterinary clinics, whelping specialists, and canine fertility centers.
- **🩸 Algorithmic Canine Estrus (Heat) Calculator**:
  - Projections for Proestrus, Estrus (standing heat), and optimal mating/progesterone testing windows.

---

## 🏗️ Architecture & Technology Stack

| Component | Technology |
|---|---|
| **Backend Framework** | Python 3.12, Django 5.1+ (Model-View-Template) |
| **Database** | SQLite (Dev) / PostgreSQL 15+ (Production) |
| **Frontend & UI** | Semantic HTML5, CSS3, Tailwind CSS & Glassmorphism |
| **Spatial / Geocoding** | OpenStreetMap Nominatim API + In-Memory Coordinate Cache |
| **Document Synthesis** | ReportLab Canvas Engine (High-throughput PDF compilation) |
| **Authentication** | Django Session Auth, Email OTP Nonces, Role-Based Access Control |
| **Security** | CSRF Tokens, PBKDF2 Password Hashing, XSS Auto-Escaping |

---

## 🚀 Quickstart & Local Installation

### Prerequisites
- Python 3.12+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/Yash-patil-09/K9MATCH.git
cd K9MATCH
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (Admin)
```bash
python manage.py createsuperuser
```

### 7. Start the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 📁 Repository Structure

```
K9MATCH/
├── config/             # Django root configuration & WSGI/ASGI endpoints
├── core/               # Main application (models, views, forms, templates)
│   ├── templates/core/ # Glassmorphic UI templates (Explore, Chat, Heat Calc, etc.)
│   ├── models.py       # Relational models (DogProfile, MatchRequest, ChatMessage)
│   ├── views.py        # Business controllers & spatial query logic
│   └── utils.py        # Haversine distance, ReportLab PDF generators
├── docs/               # Academic Project Documentation & UML Architecture
│   ├── K9MATCHsmallversion.docx   # 74-Page Authoritative Project Report
│   ├── K9Match_Project_Report.docx # Full Project Report (104 Pages)
│   └── generate_small_docx.py      # Automated report generation engine
├── staticfiles/        # CSS, JavaScript, and branding assets
├── media/              # Verified canine pedigree documents & photographs
├── manage.py           # Django execution utility
└── requirements.txt    # Project dependencies
```

---

## 🎓 Academic Project Information

- **Project Title:** K9MATCH: Ethical Canine Matching
- **Candidate:** Mr. Yash Prakash Patil (Roll No: TCS2627093)
- **Degree:** Bachelor of Science in Computer Science (B.Sc. CS)
- **Institution:** S.I.E.S. College of Arts, Science and Commerce (Empowered Autonomous), Sion (West), Mumbai
- **University:** University of Mumbai
- **Project Guide:** Mr. Rajesh Yadav
- **Academic Year:** 2026–2027

---

## 📄 License
This project is developed for academic evaluation and research purposes under the Department of Computer Science, University of Mumbai.
