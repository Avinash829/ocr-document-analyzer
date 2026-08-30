# VedaAI - Assessment Extraction & Answer Mapping

![VedaAI Banner](https://vedaai-answermapping829.vercel.app/assets/logo.png)

A production-grade, AI-powered web application designed for teachers to automate the extraction, mapping, and grading of student answer sheets against question papers.

**🚀 Live Demo:** [https://vedaai-answermapping829.vercel.app/](https://vedaai-answermapping829.vercel.app/)

## ✨ Features

- **Intelligent Extraction:** Automatically extracts questions from uploaded question papers (PDFs/Images) in their correct printed order, preserving numbering and handling sub-parts (e.g., 1a, 1b).
- **Semantic Answer Mapping:** Maps handwritten student answers to the correct questions using Gemini 1.5 Flash, even if the student answered out of order.
- **Interactive Document Viewer:** Clicking a question instantly highlights the exact region of the student's handwritten answer on the uploaded document using precise bounding boxes.
- **AI Grading & Feedback:** Automatically grades mapped answers, assigns scores based on extracted maximum marks, and provides personalized, single-line AI feedback for each question.
- **Final Report Generation:** Generates a comprehensive "Report Card" modal with a circular progress indicator and a dynamic AI-generated summary of the student's overall performance.
- **Edge-Case Handling:** Gracefully handles unmatched extra answers, unanswered questions, and multi-page spanning answers.
- **Premium UI/UX:** Built with Next.js and Tailwind CSS, featuring glassmorphism, smooth micro-animations, and full mobile responsiveness.

## 🛠️ Technology Stack

**Frontend:**
- [Next.js](https://nextjs.org/) (React Framework)
- [Tailwind CSS](https://tailwindcss.com/) (Styling & Animations)
- [Lucide React](https://lucide.dev/) (Icons)

**Backend:**
- [FastAPI](https://fastapi.tiangolo.com/) (High-performance Python web framework)
- [Google Gemini API](https://aistudio.google.com/) (Multimodal LLM for OCR, semantic mapping, and grading)
- [PyMuPDF](https://pymupdf.readthedocs.io/en/latest/) (PDF processing and rendering)

## 🚀 Running Locally

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- A Google Gemini API Key

### 1. Setup the Backend
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements-core.txt
```

Create a `.env` file in the `backend` directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Start the backend server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Setup the Frontend
```bash
cd frontend
npm install
```

Create a `.env.local` file in the `frontend` directory:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

Start the frontend development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📐 Architecture & Approach

This application uses an asynchronous, job-based architecture.
1. **Upload Phase:** The frontend uploads the Question Paper and Answer Sheet to the FastAPI backend.
2. **Processing Pipeline (Background):** The backend immediately returns a `jobId` and begins a multi-stage background process:
   - Converting PDFs to high-res images.
   - Sending images to Gemini to extract structured JSON (Questions).
   - Sending images to Gemini to extract structured JSON (Answers & Bounding Boxes).
   - Mapping the Answers to the Questions semantically.
3. **Polling:** The frontend polls the job status, displaying a real-time progress UI to the user.
4. **Interactive Grading:** Once complete, the frontend queries specific endpoints (`/api/assessments/{id}/grade`) on-demand when the teacher expands a question, triggering Gemini to grade the specific answer based on context.

## 📝 License
This project was built as a hiring assignment submission.
