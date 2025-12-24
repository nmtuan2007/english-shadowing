# 🎙️ English Shadowing System

An AI-powered application designed to help learners practice English speaking through the **Shadowing Technique**. The system automatically fetches YouTube videos, generates synchronized transcripts, creates shadowing guides using AI, and provides an interactive practice interface.

![Tech Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20Next.js%20%7C%20OpenAI%20%7C%20Whisper-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Features

- **Automated Content Pipeline**: Fetches suitable videos from YouTube based on category and level (A1-C2).
- **AI Transcription**: Uses **Whisper** (or YouTube captions) for high-accuracy subtitles.
- **Intelligent Processing**: Uses **LLMs (Llama 3 / OpenAI)** to:
  - Translate content to Vietnamese.
  - Generate specific shadowing guides/tips for difficult phrases.
- **Interactive Dashboard**:
  - Track progress across different categories (Business, Daily Life, Science, etc.).
  - "Netflix-style" learning interface with theater mode.
  - Syncs text with video playback for precise practice.
- **CLI Management**: Robust command-line tools to manage content generation.

## 🛠️ Prerequisites

Before running the project, ensure you have the following installed:

1.  **Python 3.10+**
2.  **Node.js 18+** & **npm**
3.  **FFmpeg** (Required for audio processing)
    - *Windows*: `winget install ffmpeg`
    - *Mac*: `brew install ffmpeg`
    - *Linux*: `sudo apt install ffmpeg`

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/english-shadowing.git
cd english-shadowing
```

### 2. Backend Setup
Create a virtual environment and install Python dependencies.

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Frontend Setup
Install the Next.js dependencies.

```bash
cd frontend
npm install
cd ..
```

### 4. Configuration (.env) 🔐
**Important:** You must create a `.env` file in the root directory to store your API keys.

1.  Copy the example format:
    ```bash
    # Create .env file
    touch .env
    ```
2.  Add your keys to `.env`:
    ```properties
    # AI Provider (Groq, OpenAI, etc.)
    AI_API_KEY=your_api_key_here
    AI_BASE_URL=https://api.groq.com/openai/v1
    AI_MODEL=llama-3.3-70b-versatile

    # Whisper Settings (tiny, base, small, medium, large)
    WHISPER_MODEL=base
    ```

## 🏃‍♂️ Usage

### Option A: Quick Start (Recommended)
Run the full stack (Backend + Frontend) with a single command:

```bash
python run.py
```
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

---

### Option B: Manual CLI Workflow
You can generate lessons manually using the CLI tool `app.py`.

**1. Generate Source List**
Fetches metadata from configured YouTube channels (defined in `config.py`).
```bash
python app.py generate-sources
```

**2. Generate Lessons**
Downloads videos, transcribes audio, and runs AI processing.
```bash
# Generate everything
python app.py generate-lessons

# Generate specific category
python app.py generate-lessons --category business

# Generate specific video
python app.py generate-lessons --category business --lesson how_to_speak
```

**3. Check Status**
```bash
python app.py status
```

## 📂 Project Structure

```text
├── app.py                 # Main CLI tool
├── config.py              # Configuration & Settings
├── run.py                 # Master script to run full stack
├── server.py              # FastAPI Backend
├── .env                   # Secrets (Not committed)
├── requirements.txt       # Python dependencies
├── sources.json           # Generated video database
├── lessons/               # Downloaded media & processed data
│   └── business/
│       └── lesson_id/
│           ├── video.mp4
│           ├── audio.mp3
│           ├── transcript_timed.json
│           └── shadowing_final.txt
├── scripts/               # Processing logic
│   ├── download.py
│   ├── asr_whisper.py
│   └── process_transcript.py
└── frontend/              # Next.js Application
```

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

[MIT](https://choosealicense.com/licenses/mit/)
