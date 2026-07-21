from fastapi import FastAPI
from dotenv import load_dotenv
from supabase import create_client, Client
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi import Header
from typing import Optional
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI()
security = HTTPBearer()
class AuthRequest(BaseModel):
    email: str | None = None
    password: str | None = None

@app.on_event("startup")
async def startup_event():
    print("Server running and connected to Supabase")

@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/auth/signup")
async def signup(body: AuthRequest):
    if not body.email or not body.password:
        return JSONResponse(status_code=400, content={"error": "email and password required"})

    try:
        result = supabase.auth.sign_up({"email": body.email, "password": body.password})
        return JSONResponse(status_code=201, content={"user": result.user.model_dump(mode="json")})
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})


@app.post("/auth/login")
async def login(body: AuthRequest):
    if not body.email or not body.password:
        return JSONResponse(status_code=400, content={"error": "email and password required"})

    try:
        result = supabase.auth.sign_in_with_password({"email": body.email, "password": body.password})
        return JSONResponse(status_code=200, content={
            "access_token": result.session.access_token,
            "refresh_token": result.session.refresh_token
        })
    except Exception as e:
        return JSONResponse(status_code=401, content={"error": "Invalid login credentials"})
@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        user_response = supabase.auth.get_user(token)
        return {"user": user_response.user, "token": token}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
@app.get("/protected/profile")
def protected_profile(current=Depends(get_current_user)):
    user = current["user"]
    return {
        "id": user.id,
        "email": user.email,
        "created_at": str(user.created_at)
    }


@app.get("/protected/dashboard")
def protected_dashboard(current=Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {current['user'].email}"}


@app.post("/auth/logout")
def logout(current=Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
        return JSONResponse(status_code=204, content=None)
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
