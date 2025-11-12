import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import Product

app = FastAPI(title="Rohan Mobile Store API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Rohan Mobile Store Backend is running"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from Rohan's backend API!"}

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

    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

# Seed some sample mobile products if none exist
SAMPLE_MOBILES = [
    {
        "title": "Rohan X1 Pro",
        "description": "6.7\" AMOLED, 120Hz, 108MP camera, 5000mAh",
        "price": 699.0,
        "category": "mobile",
        "in_stock": True,
        "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=800&q=80"
    },
    {
        "title": "Rohan Mini 5G",
        "description": "Compact 5.8\" OLED, 5G, dual camera",
        "price": 499.0,
        "category": "mobile",
        "in_stock": True,
        "image_url": "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?w=800&q=80"
    },
    {
        "title": "Rohan Ultra Max",
        "description": "6.9\" LTPO, 200MP camera, 1TB, 6000mAh",
        "price": 1199.0,
        "category": "mobile",
        "in_stock": True,
        "image_url": "https://images.unsplash.com/photo-1518779578993-ec3579fee39f?w=800&q=80"
    }
]

@app.post("/api/products", response_model=dict)
async def create_product(product: Product):
    try:
        inserted_id = create_document("product", product)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products", response_model=List[dict])
async def list_products(category: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {"category": category} if category else {}
        items = get_documents("product", filter_dict=filter_dict, limit=limit)
        # If no products in DB yet, seed sample mobiles (not persisted unless DB is set up)
        if not items and (category == "mobile" or category is None):
            return SAMPLE_MOBILES
        # Convert ObjectId to string
        for it in items:
            _id = it.get("_id")
            if _id is not None:
                it["id"] = str(_id)
                del it["_id"]
        return items
    except Exception as e:
        # Fallback to sample if DB not available and user asked for mobiles
        if "Database not available" in str(e) and (category == "mobile" or category is None):
            return SAMPLE_MOBILES
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
