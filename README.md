# ComradeAi AI 🤖

ComradeAi AI is a professional, multi-modal AI chat application built with **Streamlit**, featuring a premium "ChatGPT-style" interface, robust session management, and a flexible backend supporting both Cloud (Supabase) and Local (SQLite) environments.

## 🚀 Key Features

- **Multi-Modal Intelligence**: Seamlessly switch between **Anthropic Claude Sonnet 4** and **Google Gemini 2.5 Flash**.
- **File Context Analysis**: Upload PDF, DOCX, CSV, or TXT files. ComradeAi extracts the text and uses it as context for AI responses.
- **Image Generation**: Integrated with **Stability AI** to generate high-quality images directly from the chat.
- **Project Organization**: Group your chats into "Projects" for better workflow management.
- **Premium UI/UX**: Professional dark/light themes, sticky chat controls, and responsive sidebar.
- **Admin Dashboard**: Full control over users, chat history exports, and system logs.

---

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python-based interactive UI)
- **AI Processing**: Anthropic API, Google Generative AI SDK
- **Database**: Supabase (PostgreSQL) for production; SQLite for local development
- **Auth**: Custom OTP, Google OAuth, and Email/Password flows
- **Image Generation**: Stability AI API

---

## 🔄 Internal Workflow

### 1. Authentication & Security
Handled via `src/auth.py`. 
- Supports **Google OAuth** and **OTP** via a fragment-to-query workaround in `app.py`.
- Session state manages user roles (`user` vs `admin`) and persistence.

### 2. Intelligent Routing
The core AI logic in `src/helper.py` follows a priority-based routing:
1. **Claude Sonnet 4** is the primary engine.
2. **Gemini 2.5 Flash** acts as an automatic fallback if Claude fails or is unavailable.
3. System prepends extracted file text to prompts to enable document-aware chatting.

### 3. Data Persistence
`src/db.py` uses a **polymorphic design**:
- It checks for Supabase credentials in `secrets.toml`. If present, it uses the Supabase cloud database.
- If credentials are missing, it automatically falls back to a local `ComradeAi.db` (SQLite), ensuring the app works out-of-the-box.

---

## 📦 Setup & Installation

### Prerequisites
- Python 3.10+
- (Optional) Supabase Project, Anthropic API Key, Gemini API Key.

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/ComradeAi-ai.git
   cd ComradeAi-ai
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
   STABILITY_API_KEY = "your_key"

   # Supabase (Optional)
   SUPABASE_URL = "your_url"
   SUPABASE_KEY = "your_key"
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

---

## 📜 License
Internal use only. Part of the ComradeAi project suite.
Developed by ANKIT DAHIYA
