# AI App Builder v2

**AI App Builder v2** is a sophisticated, web-based AI IDE designed to dynamically scaffold, generate, and iteratively update full-stack web applications (React + Express). It provides a VS Code-like interface featuring a file explorer, a live code editor (Monaco), an integrated terminal, and an AI chat assistant.

The core objective of the system is to solve LLM quota and formatting issues by utilizing an iterative generation pipeline. It employs domain-specific planning, automatic dependency detection, and a self-correcting build loop to ensure the generated code compiles successfully.

---

##  Technical Stack

### 1. The IDE Application Itself
* **Frontend:** React, Vite, Tailwind CSS, Monaco Editor (`@monaco-editor/react`), Lucide React (icons), `react-resizable-panels`.
* **Backend:** Python, FastAPI (API layer), Uvicorn (server), Google GenAI SDK (`google-generativeai`).

### 2. The Generated Applications
* **Frontend:** React (Vite-based), Inline styles / CSS.
* **Backend:** Node.js, Express, CORS.
* **Database:** In-memory data structures (mock data).

---

##  Getting Started

### Prerequisites
* Node.js and npm
* Python 3.10+
* A valid Google Gemini API Key

### Installation

1. **Clone the repository**
2. **Setup the Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables**
   Create a `.env` file in the `backend` directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```
4. **Setup the Frontend**
   ```bash
   cd frontend
   npm install
   ```

### Running the Application

You need to run both the FastAPI backend and the React frontend.

1. **Start the Backend Server**
   ```bash
   cd backend
   python server.py
   ```
   *The API will be available at `http://localhost:8000`*

2. **Start the Frontend Development Server**
   ```bash
   cd frontend
   npm run dev
   ```
   *The IDE will be available at `http://localhost:5173`*

---

##  Execution Flow (How it Works)

1. **User Prompt:** The user types an app idea into the AI Builder panel (e.g., "Build a fitness tracker").
2. **Domain Detection & Planning (`planner.py`):**
   * The AI first detects the specific domain and UI requirements.
   * It generates a detailed JSON implementation plan (features, layout, tech stack, color palette, API routes).
   * The plan is strictly validated for specificity to prevent the LLM from generating generic apps.
3. **Project Scaffolding (`agent.py`):**
   * The backend runs `npx create-vite` to initialize a React workspace.
4. **Code Generation:**
   * **Backend:** Generates `server.js` with Express endpoints matching the plan.
   * **Frontend:** Generates a comprehensive `App.jsx` applying premium UI/UX design.
5. **Dependency Management:** The AI scans the generated code, identifies missing imports, and runs `npm install`.
6. **Self-Healing Build Loop:** 
   * The system runs `npm run build`. 
   * If errors occur, the LLM reads the error logs and rewrites the broken code, retrying up to 2 times.
7. **Iterative Development:** The user can interact with the app via the Monaco Editor, run the dev server, or chat with the AI to perform targeted file edits.

---

##  AI Models Used

The system exclusively utilizes **Google's Gemini** models through the `google-generativeai` SDK. 
To prevent quota exhaustion and ensure reliability, `call_llm()` implements a **model-fallback logic array**. It attempts to generate content using the highest-tier models first and steps down sequentially if it encounters API errors (starting from `gemini-3.7-flash` down to `gemini-pro-latest`).
