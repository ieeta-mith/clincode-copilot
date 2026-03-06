# ClinCode Copilot

An intelligent ICD-9 clinical coding system that automatically predicts diagnosis codes from discharge summaries using a hybrid deep learning approach.

## Overview

ClinCode Copilot is a machine learning-powered assistant for medical coding that combines state-of-the-art deep learning with similarity-based prediction to suggest relevant ICD-9 diagnosis codes from clinical text. The system is designed to help medical coders by providing accurate, explainable predictions with attention-based visualization showing which parts of the text influenced each prediction.

### Key Features

- **Hybrid Prediction Model**: Combines Label Attention neural networks with k-Nearest Neighbors (FAISS) for robust predictions
- **Explainable AI**: Attention mechanism highlights which text chunks influenced each code prediction
- **Similar Patient Search**: Find similar cases based on clinical text similarity
- **ICD Code Search**: Interactive search through ICD-9 code descriptions
- **Real-time Predictions**: Fast inference with configurable confidence thresholds
- **Modern Web Interface**: Intuitive React-based UI for clinical text input and results visualization

### Architecture

The system uses a three-component architecture:

1. **Label Attention Model**: Transformer-based (Clinical BERT) end-to-end model that learns to predict ICD codes directly from clinical text with chunk-level attention
2. **k-NN Classifier**: FAISS-powered similarity search against training embeddings for robust predictions on rare codes
3. **Ensemble Scoring**: Configurable weighted combination of both approaches with optimized thresholds

```
Clinical Text → Chunking → Embeddings → LA Model → Ensemble → ICD Codes
                                      ↘ k-NN    ↗
```

## Tech Stack

### Backend
- **FastAPI**: High-performance REST API
- **PyTorch**: Deep learning framework
- **Transformers**: Clinical BERT for medical text encoding
- **FAISS**: Efficient similarity search
- **Pydantic**: Data validation and settings management

### Frontend
- **Next.js 16**: React framework with App Router
- **React 19**: Latest React with concurrent features
- **TypeScript**: Type-safe development
- **Tailwind CSS v4**: Utility-first styling
- **shadcn/ui**: High-quality UI components (Radix UI)
- **TanStack Query**: Async state management
- **Zustand**: Lightweight client state

### ML/Data
- **scikit-learn**: Model evaluation and utilities
- **NumPy & SciPy**: Numerical computing
- **Clinical BERT**: Pre-trained medical language model

## Installation

### Prerequisites

- Python 3.9+ with pip
- Node.js 18+ with npm
- At least 4GB RAM
- (Optional) CUDA-capable GPU for faster inference

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Clincode-copilot
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up model files:
Place your trained models in the `models/` directory with the following structure:
```
models/
├── end_to_end/          # Label Attention model checkpoint
├── knn_chunks/          # FAISS index and embeddings
├── ensemble/            # Ensemble configuration
└── icd_dictionary.json  # ICD-9 code descriptions
```

4. Configure environment (optional):
```bash
export CLINCODE_DEVICE=cuda  # Use GPU (default: cpu)
export CLINCODE_MAX_CHUNKS=256
export CLINCODE_NEIGHBOR_COUNT=10
```

5. Start the backend:
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000 with interactive documentation at http://localhost:8000/docs.

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure API endpoint (optional):
```bash
# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

4. Start development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000.

## Usage

### Web Interface

1. Open http://localhost:3000 in your browser
2. Enter or paste a discharge summary in the text area (minimum 50 characters)
3. Click "Predict Codes" to get ICD-9 predictions
4. View:
   - Predicted codes with confidence scores and descriptions
   - Attention visualization showing influential text chunks
   - Similar patient cases with their codes
5. Use the code search feature to explore ICD-9 descriptions

### API Endpoints

#### Predict ICD Codes
```bash
POST /api/predict/detailed
Content-Type: application/json

{
  "text": "Patient admitted with acute myocardial infarction...",
  "threshold": 0.3,
  "min_freq": 5
}
```

Response includes predicted codes, scores, descriptions, and attention weights.

#### Find Similar Patients
```bash
POST /api/similar-patients
Content-Type: application/json

{
  "text": "Patient admitted with...",
  "k": 5
}
```

#### Search ICD Codes
```bash
GET /api/codes?q=diabetes&limit=10
```

#### Health Check
```bash
GET /health
```

### Configuration

Backend settings can be configured via environment variables with `CLINCODE_` prefix:

- `CLINCODE_MODEL_DIR`: Path to models directory (default: `./models`)
- `CLINCODE_DEVICE`: Computation device: `cuda` or `cpu` (default: `cpu`)
- `CLINCODE_MAX_CHUNKS`: Maximum text chunks to process (default: 256)
- `CLINCODE_MAX_LENGTH`: Maximum tokens per chunk (default: 128)
- `CLINCODE_NEIGHBOR_COUNT`: k-NN neighbors to consider (default: 10)
- `CLINCODE_CORS_ORIGINS`: Allowed CORS origins (default: `http://localhost:3000`)

## Development

### Project Structure

```
Clincode-copilot/
├── app/                    # FastAPI backend
│   ├── main.py            # Application entry point
│   ├── config.py          # Settings and configuration
│   ├── dependencies.py    # Dependency injection
│   ├── routers/           # API route handlers
│   └── services/          # Business logic layer
├── icd_hybrid/            # ML core
│   ├── predictor.py       # Main prediction interface
│   ├── models/            # Neural network architectures
│   ├── classifiers/       # KNN and attention classifiers
│   ├── data/              # Data processing utilities
│   └── embeddings/        # Clinical BERT wrapper
├── frontend/              # Next.js application
│   ├── src/
│   │   ├── app/           # Next.js App Router
│   │   ├── components/    # React components
│   │   ├── lib/           # API client and utilities
│   │   └── stores/        # State management
│   └── public/            # Static assets
├── models/                # Trained models (gitignored)
├── article/               # Research paper
├── requirements.txt       # Python dependencies
└── CLAUDE.md             # Development guidelines
```

### Running Tests

```bash
# Backend tests
pytest

# Frontend linting
cd frontend && npm run lint
```

### Building for Production

Frontend:
```bash
cd frontend
npm run build
npm start
```

Backend:
```bash
# Use a production ASGI server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Model Files

The system requires pre-trained models that are not included in this repository. Models should be placed in the `models/` directory:

- **End-to-End Model**: PyTorch checkpoint for the Label Attention model
- **FAISS Index**: Pre-computed k-NN index with training embeddings
- **Label Encoder**: ICD code to index mapping
- **Ensemble Config**: Optimized weights and thresholds for combining predictions
- **ICD Dictionary**: Code descriptions for all ICD-9 codes

Contact the authors for access to trained models or train your own using the MIMIC-III dataset.

## API Documentation

Full interactive API documentation is available at http://localhost:8000/docs (Swagger UI) or http://localhost:8000/redoc (ReDoc) when the backend is running.

## Important Notes

- The system predicts **ICD-9 codes only** (not ICD-10)
- Clinical text must be at least **50 characters**
- The `min_freq` parameter filters predictions to only codes that occurred frequently in training data
- Attention weights show chunk-level importance, not token-level
- GPU acceleration is recommended for production use (`CLINCODE_DEVICE=cuda`)

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes before submitting a pull request.

## Support

For questions or issues:
- Open a GitHub issue
- Contact the research team at IEETA

## Acknowledgments

This project uses:
- Clinical BERT for medical text understanding
- MIMIC-III dataset for training (access required)
- FastAPI and Next.js frameworks
- shadcn/ui component library
