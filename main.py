import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import Portfolio, Education, ProjectItem

app = FastAPI(title="Portfolio API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def serialize_doc(doc):
    if not doc:
        return doc
    doc = dict(doc)
    if "_id" in doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def read_root():
    return {"message": "Portfolio Backend Running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# -------- Portfolio Endpoints --------
DEFAULT_PORTFOLIO = Portfolio(
    name="Sunny Kumar",
    tagline="B.Tech in ECE • Frontend & Backend Developer",
    education=Education(
        degree="B.Tech",
        branch="Electronics & Communication Engineering",
        college="Gandhi Institute for Education and Technology",
        location="Bhubaneswar, Bainitang, Odisha"
    ),
    projects=[
        ProjectItem(title="Study Care Park Website", description="Educational portal with modern UI", link=""),
        ProjectItem(title="Tech Wave Shree Website", description="Tech service website with responsive layout", link="")
    ],
    skills=[
        "HTML", "CSS", "JavaScript", "Python", "C", "Node.js", "React", "MongoDB"
    ],
    email=None,
    phone=None,
    location="Bhubaneswar, Odisha"
)


def get_portfolio_doc():
    # We treat this as a singleton collection; return first doc or create default
    docs = get_documents("portfolio", limit=1)
    if docs:
        return docs[0]
    # create default
    create_document("portfolio", DEFAULT_PORTFOLIO)
    docs = get_documents("portfolio", limit=1)
    return docs[0] if docs else None


@app.get("/api/portfolio")
def get_portfolio():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = get_portfolio_doc()
    return serialize_doc(doc)


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    tagline: Optional[str] = None
    education: Optional[Education] = None
    projects: Optional[list[ProjectItem]] = None
    skills: Optional[list[str]] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None


@app.put("/api/portfolio")
def update_portfolio(payload: PortfolioUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    doc = get_portfolio_doc()
    if not doc:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    from datetime import datetime, timezone
    update_data = {k: v for k, v in payload.model_dump(exclude_none=True).items()}
    update_data["updated_at"] = datetime.now(timezone.utc)
    db["portfolio"].update_one({"_id": doc["_id"]}, {"$set": update_data})
    new_doc = db["portfolio"].find_one({"_id": doc["_id"]})
    return serialize_doc(new_doc)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
