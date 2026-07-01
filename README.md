# User Analytics Semantic Search System

This project tracks user activity, stores events in a database, generates embeddings, and enables semantic search over user behavior data.


## Project Objective

The goal of this project is to track user behavioral events (e.g., page views, button clicks) and enable rich analytics alongside semantic similarity search. By translating user actions into vector embeddings and storing them in a similarity index, we can easily find related actions or identify users with similar behavioral footprints.

---

## Tech Stack

**Backend:**
- **FastAPI**: Used for building the API endpoints.
- **Python**: Core programming language.
- **PostgreSQL**: Relational database to persist users, events, and vector indices mappings.
- **SQLAlchemy**: Object-Relational Mapper (ORM) with asyncpg driver.

**AI Layer:**
- **SentenceTransformers** (`all-MiniLM-L6-v2`): Generates 384-dimensional vector embeddings of text.
- **FAISS**: Performs vector similarity search.

**Frontend:**
- **React**: Simple dashboard interface.
- **TypeScript**: Typed language support.
- **Vite**: Build tool and dev server.

**Deployment:**
- **Docker & Docker Compose**: Optional local container orchestration.

---

## API Endpoints

### `POST /api/v1/track`
Accepts a tracking payload. Updates user activity totals, logs the event to PostgreSQL, and schedules a background task to generate embeddings and index them in FAISS.
- **Sample Request Body:**
  ```json
  {
    "userId": "user_001",
    "event": "user clicked pricing button",
    "metadata": {
      "page": "/home"
    }
  }
  ```
- **Sample Response (202 Accepted):**
  ```json
  {
    "success": true,
    "eventId": "a7b3b3a3-a7ba-4e8c-8fdf-7db722de8f55",
    "message": "Event accepted. Embedding generation scheduled."
  }
  ```

### `GET /api/v1/analytics`
Aggregates statistics from the events table, returning event count totals, distribution per user, and a list of active users.
- **Sample Response (200 OK):**
  ```json
  {
    "totalEvents": 42,
    "eventsPerUser": {
      "user_001": 15,
      "user_002": 27
    },
    "mostActiveUsers": [
      {
        "userId": "user_002",
        "count": 27
      },
      {
        "userId": "user_001",
        "count": 15
      }
    ]
  }
  ```

### `GET /api/v1/search`
Translates a text query into an embedding vector, queries the FAISS index for similarity, retrieves the corresponding events from the PostgreSQL database, and returns them ranked by score.
- **Sample Request:** `GET /api/v1/search?query=pricing&limit=5`
- **Sample Response (200 OK):**
  ```json
  {
    "results": [
      {
        "id": "a7b3b3a3-a7ba-4e8c-8fdf-7db722de8f55",
        "userId": "user_001",
        "event": "user clicked pricing button",
        "metadata": {
          "page": "/home"
        },
        "timestamp": "2026-07-01T12:00:00Z",
        "similarity_score": 0.8951
      }
    ]
  }
  ```

### `GET /api/v1/similar-users`
Finds profiles exhibiting similar behavioral patterns. Compiles user centroids by averaging their individual event vectors, then computes cosine similarity metrics against other profiles in the system.
- **Sample Request:** `GET /api/v1/similar-users?userId=user_001`
- **Sample Response (200 OK):**
  ```json
  [
    {
      "userId": "user_002",
      "similarity_score": 0.8214,
      "total_events": 27,
      "last_active": "2026-07-01T12:30:00Z"
    }
  ]
  ```

### `GET /api/v1/health`
Checks database connectivity and responds with the connection latency.
- **Sample Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "postgres": "connected (1.20ms)",
    "timestamp": 1782847920
  }
  ```

---

## Local Setup

### Database Setup
Create a PostgreSQL database locally and configure credentials in backend/.env.

### Backend Setup
1. Navigate to the backend directory and set up a virtual environment:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize environment variables. Create a `backend/.env` file:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/insightflow
   FAISS_INDEX_PATH=data/faiss_index.bin
   EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
   ENVIRONMENT=development
   CORS_ORIGINS=http://localhost:5173,http://localhost
   ```
4. Run the seeder script to initialize database tables and seed test data:
   ```bash
   python app/utils/seeder.py
   ```
5. Start the FastAPI application server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Access the interactive documentation at `http://127.0.0.1:8000/docs`.

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install client dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development client:
   ```bash
   npm run dev
   ```
   Access the React application UI at `http://localhost:5173`.

### Alternative Setup (Docker Compose)
If you prefer Docker:
```bash
docker compose up --build
```
This spins up PostgreSQL, Backend, and Frontend containers automatically. Run the seeder inside the running backend container to generate mock data if needed:
```bash
docker compose exec backend python app/utils/seeder.py
```

---

## Design Decisions

- **Why PostgreSQL**: PostgreSQL stores user and event data in structured tables and handles JSONB columns easily, allowing us to store arbitrary event metadata structures without a rigid schema.
- **Why FAISS**: FAISS helps quickly compare stored vector embeddings. Rather than relying on slow database loops or overhead-heavy plugins, it computes searches very fast.
- **Why Embeddings for Semantic Search**: Relying solely on keyword searches fails when users describe similar actions with different words (e.g., "pricing plan" vs "billing page"). Generating embeddings helps find similar user actions even when exact words differ.
- **Why Async Background Tasks**: Generating text embeddings and updating FAISS indices can introduce latency. Offloading these tasks to FastAPI background workers allows the application to ingest events immediately with a `202 Accepted` response while keeping API response times fast and consistent.
