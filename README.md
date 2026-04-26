# Comrade Ai 🤖

![Comrade Ai Banner](file:///Users/aman/.gemini/antigravity/brain/8334f255-9b44-4309-ba3d-d329feb42903/comrade_ai_logo_1775202021004.png)

Comrade Ai is a professional, multi-modal AI chat application built with **Streamlit**, featuring a premium "GPT-style" interface, robust session management, and a flexible backend supporting both Cloud (Supabase) and Local (SQLite) environments.

## 🚀 Key Features

- **Multi-Modal Intelligence**: Seamlessly switch between **Anthropic Claude 4.5** and **Google Gemini 1.5 Flash**.
- **Indian Equity Research Pipeline**: Built-in modules for Indian stock analysis, including FMP fundamentals, Zerodha Kite integration, and macro-sectoral growth trends.
- **File Context Analysis**: Upload PDF, DOCX, CSV, or TXT files. Comrade Ai extracts text and uses it as context for AI responses.
- **Image Generation**: Integrated **Stability AI** for high-quality image generation directly from the chat.
- **Project Organization**: Group your chats into "Projects" for better workflow management and modular research.
- **Premium UI/UX**: Professional dark/light themes, glassmorphism design, and fluid animations.
- **Enterprise Authentication**: Secure login via **Email**, **Google OAuth**, and **Mobile OTP (Twilio)**.
- **Admin Dashboard**: Full control over users, chat history exports, and system logs.

---

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python-based interactive UI)
- **AI Processing**: Anthropic API, Google Generative AI SDK, Stability AI
- **Database**: Supabase (PostgreSQL) for production; SQLite for local development
- **Auth**: Secure Email/Password & Twilio OTP
- **Communication**: Twilio SMS API for OTP verification

---

## 🔄 Internal Workflow

### 1. Authentication & Security
Handled via `src/auth.py`. 
- Supports **Email/Password** authentication with live strength monitoring.
- Session state manages user roles (`user` vs `admin`) and persistence.

### 2. Intelligent Routing
The core AI logic in `src/helper.py` follows a priority-based routing:
1. **Claude** is the primary engine.
2. **Gemini** acts as an automatic fallback if Claude fails or is unavailable.
3. System prepends extracted file text to prompts to enable document-aware chatting.

### 3. Data Persistence
`src/db.py` uses a **polymorphic design**:
- It checks for Supabase credentials in `secrets.toml`. If present, it uses the Supabase cloud database.
- If credentials are missing, it automatically falls back to a local `comrade.db` (SQLite), ensuring the app works out-of-the-box.

---

## 📦 Setup & Installation

### Prerequisites
- Python 3.11+
- (Optional) Supabase Project, Anthropic API Key, Gemini API Key.

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/name_of_repo.git
   cd name_of_repo
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv projectenv
   source projectenv/bin/activate  # On Windows: projectenv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Secrets**:
   Create `.streamlit/secrets.toml` and add your keys:
   ```toml
   # AI Keys
   ANTHROPIC_API_KEY = "your_key"
   GEMINI_API_KEY = "your_key"

   # Supabase (Optional)
   SUPABASE_URL = "your_url"
   SUPABASE_KEY = "your_key"
   ```

5. **Initialize Admin**:
   Run the utility script to create the first admin user:
   ```bash
   python scripts/create_admin.py
   ```

6. **Run the application**:
   ```bash
   streamlit run app.py
   ```

---

## 📜 License
Internal use only. Part of the Wingman project suite.
