"""
FastAPI Backend for NewsCollect
Exposes REST API endpoints for Next.js frontend
"""
import os
import requests
import threading
from typing import List, Optional, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from .ai_writer_functions import generate_prewrite_summary, generate_ai_suggestion, improve_paragraph

# Load environment variables
load_dotenv()

app = FastAPI(title="NewsCollect API")

SUGARCLASS_API_URL = os.getenv("SUGARCLASS_API_URL", "http://backend:8000/api/v1")

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        print("[Auth] No authorization header provided")
        return None  # Or raise 401 if you want to force auth

    try:
        # Verify with Sugarclass
        response = requests.get(
            f"{SUGARCLASS_API_URL}/auth/me",
            headers={"Authorization": authorization},
            timeout=5
        )
        if response.status_code == 200:
            user_data = response.json()
            print(f"[Auth] User authenticated: {user_data.get('id', 'unknown')}")
            return user_data
        else:
            print(f"[Auth] Failed to validate credentials: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"[Auth] Error response: {error_data}")
            except:
                print(f"[Auth] Error response: {response.text}")
    except requests.exceptions.Timeout:
        print("[Auth] Timeout connecting to Sugarclass API")
    except requests.exceptions.ConnectionError:
        print(f"[Auth] Connection error to Sugarclass API at {SUGARCLASS_API_URL}")
    except Exception as e:
        print(f"[Auth] Unexpected error: {e}")

    return None

def report_activity(service: str, activity_type: str, token: str, metadata: dict = None):
    if not token:
        return
    try:
        requests.post(
            f"{SUGARCLASS_API_URL}/progress/",
            json={
                "service": service,
                "activity_type": activity_type,
                "metadata_json": metadata or {},
                "score": 100
            },
            headers={"Authorization": token},
            timeout=2
        )
    except Exception as e:
        print(f"Failed to report activity: {e}")

# Enable CORS for Next.js frontend
# Get CORS origins from environment variable, with fallback to localhost for development
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3400,http://localhost:3401,http://localhost:3403")
allow_origins_list = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Tasks to run on startup"""
    if os.getenv("ENABLE_SCHEDULER", "false").lower() == "true":
        try:
            from collector.scheduler import start_scheduler
            start_scheduler()
            print("[Startup] News collection scheduler started")
        except Exception as e:
            print(f"[Startup Error] Failed to start scheduler: {e}")

# Pydantic models
class Article(BaseModel):
    id: int
    title: str
    url: str | None = None
    source: str | None = None
    category: str | None = None
    age_group: str | None = None
    full_text: str | None = None
    image_url: str | None = None
    published_at: datetime | str | None = None
    word_count: int | None = None

class PrewriteRequest(BaseModel):
    title: str
    text: str
    year_level: str | int  # Accept both "Year 7" and 7

class SuggestionRequest(BaseModel):
    user_text: str
    title: str
    article_text: str
    year_level: str | int  # Accept both "Year 7" and 7
    prewrite_summary: str | None = None  # Optional writing plan from Plan tab

class ImprovementRequest(BaseModel):
    text: str
    article_text: str
    year_level: str | int  # Accept both "Year 7" and 7


@app.get("/")
def read_root():
    return {
        "message": "NewsCollect API",
        "version": "1.0",
        "endpoints": [
            "/articles",
            "/articles/{id}",
            "/ai/prewrite",
            "/ai/suggest",
            "/ai/improve"
        ]
    }

@app.get("/health")
def health_check():
    """Health check endpoint for Docker health checks and monitoring"""
    from .database import health_check as db_health_check
    db_status = db_health_check()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "online" if db_status else "offline",
        "service": "NewsCollect API",
        "version": "1.0"
    }

@app.get("/articles", response_model=List[Article])
def get_articles(
    category: Optional[str] = None,
    age_group: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get list of articles with optional filtering"""
    from .database import get_articles as db_get_articles
    articles = db_get_articles(category=category, age_group=age_group, limit=limit, offset=offset)
    
    # Ensure word_count is present for each article
    for article in articles:
        if not article.get('word_count') and article.get('full_text'):
            article['word_count'] = len(article['full_text'].split())
    
    return articles

@app.get("/articles/{article_id}", response_model=Article)
def get_article(article_id: int):
    """Get single article by ID"""
    from .database import get_article_by_id
    article = get_article_by_id(article_id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Ensure word_count is present
    if not article.get('word_count') and article.get('full_text'):
        article['word_count'] = len(article['full_text'].split())
    
    return article

@app.post("/ai/prewrite")
def generate_prewrite(request: PrewriteRequest, authorization: Optional[str] = Header(None), user: Optional[dict] = Depends(get_current_user)):
    """Generate prewrite summary for an article"""
    try:
        summary = generate_prewrite_summary(
            request.title,
            request.text,
            request.year_level
        )
        if user and authorization:
            report_activity("writer", "prewrite", authorization, {"title": request.title})
        return {"summary": summary, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}

@app.post("/ai/suggest")
def generate_suggestion(request: SuggestionRequest, authorization: Optional[str] = Header(None), user: Optional[dict] = Depends(get_current_user)):
    """Generate AI writing suggestion"""
    try:
        suggestion = generate_ai_suggestion(
            request.user_text,
            request.title,
            request.article_text,
            request.year_level,
            request.prewrite_summary
        )
        if user and authorization:
            report_activity("writer", "suggestion", authorization, {"title": request.title})
        return {"suggestion": suggestion, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}

@app.post("/ai/improve")
def improve_text(request: ImprovementRequest, authorization: Optional[str] = Header(None), user: Optional[dict] = Depends(get_current_user)):
    """Improve user's writing"""
    try:
        improved = improve_paragraph(
            request.text,
            request.article_text,
            request.year_level
        )
        if user and authorization:
            report_activity("writer", "improvement", authorization, {})
        return {"improved": improved, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}

class WritingSaveRequest(BaseModel):
    article_id: int
    title: str
    content: str
    content_html: Optional[str] = None
    content_json: Optional[str] = None
    word_count: int
    year_level: str
    milestone_message: Optional[str] = None


@app.post("/ai/save-writing")
def save_writing(request: WritingSaveRequest, authorization: Optional[str] = Header(None), user: Optional[dict] = Depends(get_current_user)):
    """Save user's news writing progress"""
    from .database import save_user_writing
    
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to save progress")
    
    try:
        user_id = str(user.get("id"))
        writing_id = save_user_writing(
            user_id=user_id,
            article_id=request.article_id,
            title=request.title,
            content=request.content,
            content_html=request.content_html,
            content_json=request.content_json,
            word_count=request.word_count,
            year_level=request.year_level,
            milestone_message=request.milestone_message
        )
        
        # Report progress to Sugarclass
        if authorization:
            report_activity(
                service="writer",
                activity_type="article_completion" if request.word_count >= 200 else "draft_save",
                token=authorization,
                metadata={
                    "article_id": request.article_id,
                    "title": request.title,
                    "word_count": request.word_count,
                    "writing_id": writing_id
                }
            )
            
        return {"success": True, "writing_id": writing_id}
    except Exception as e:
        print(f"Save writing error: {e}")
        return {"error": str(e), "success": False}


@app.get("/ai/my-writings")
def get_my_writings(user: Optional[dict] = Depends(get_current_user)):
    """Get all writings for the current user"""
    from .database import get_user_writings

    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_id = str(user.get("id"))
        writings = get_user_writings(user_id)
        return {"writings": writings, "success": True}
    except Exception as e:
        return {"error": str(e), "success": False}


@app.delete("/ai/writings/{writing_id}")
def delete_writing(writing_id: int, user: Optional[dict] = Depends(get_current_user)):
    """Delete a specific writing for the current user"""
    from .database import delete_user_writing

    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        user_id = str(user.get("id"))
        success = delete_user_writing(writing_id, user_id)
        if success:
            return {"success": True}
        else:
            return {"error": "Writing not found or you don't have permission", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


@app.get("/stats")
def get_stats():
    """Get database statistics"""
    from .database import get_stats
    return get_stats()

# Background collection status tracking
_collection_status = {
    "running": False,
    "last_started": None,
    "last_completed": None,
    "last_error": None,
    "last_results": None,
}
_collection_lock = threading.Lock()


def _run_collection_background():
    """Run collection in background thread"""
    from collector.collector import collect_all

    try:
        print("[Collect] Background collection started")
        results = collect_all()

        with _collection_lock:
            _collection_status["running"] = False
            _collection_status["last_completed"] = datetime.utcnow().isoformat()
            _collection_status["last_results"] = results
            _collection_status["last_error"] = None

        print(f"[Collect] Background collection completed: {len(results)} sources processed")
    except Exception as e:
        print(f"[Collect] Background collection error: {e}")
        with _collection_lock:
            _collection_status["running"] = False
            _collection_status["last_error"] = str(e)


@app.post("/collect")
def collect():
    """Trigger the news collection process in background"""
    with _collection_lock:
        if _collection_status["running"]:
            return {
                "status": "already_running",
                "message": "Collection is already running",
                "last_started": _collection_status["last_started"],
            }

        _collection_status["running"] = True
        _collection_status["last_started"] = datetime.utcnow().isoformat()
        _collection_status["last_error"] = None

    # Start collection in background thread
    thread = threading.Thread(target=_run_collection_background, daemon=True)
    thread.start()

    return {
        "status": "started",
        "message": "Collection started in background",
        "started_at": _collection_status["last_started"],
    }


@app.get("/collect/status")
def collect_status():
    """Get the status of background collection"""
    with _collection_lock:
        return {
            "running": _collection_status["running"],
            "last_started": _collection_status["last_started"],
            "last_completed": _collection_status["last_completed"],
            "last_error": _collection_status["last_error"],
            "last_results": _collection_status["last_results"],
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
