import os
import hashlib
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from starlette.middleware.sessions import SessionMiddleware
from openai import OpenAI

# ==========================================================
# SAFE IMPORTS
# ==========================================================

try:
    import models
    from models import Base
except Exception:
    models = None
    Base = None

# ==========================================================
# APP INIT
# ==========================================================

app = FastAPI(title="Enterprise Brain SaaS")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "supersecretkey")
)

# ==========================================================
# STATIC + TEMPLATE SAFE LOAD
# ==========================================================

if os.path.exists("static"):
    app.mount(
        "/static",
        StaticFiles(directory="static"),
        name="static"
    )

templates = None
if os.path.exists("templates"):
    templates = Jinja2Templates(directory="templates")

# ==========================================================
# DATABASE SAFE CONFIG (Docker + HF Safe)
# ==========================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1
    )

engine = None
SessionLocal = None

if DATABASE_URL and Base:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True
        )

        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        Base.metadata.create_all(bind=engine)

        print("Database connected successfully")

    except Exception as e:
        print("Database connection failed:", str(e))

# ==========================================================
# UTILITIES
# ==========================================================

def get_db():
    if not SessionLocal:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================================
# HEALTH CHECK ROUTES (VERY IMPORTANT)
# ==========================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Health check passed 🚀"
    }


@app.get("/ping")
def ping():
    return {
        "message": "Enterprise Brain Running Successfully 🚀"
    }

# ==========================================================
# AUTO CREATE ADMIN (SAFE)
# ==========================================================

def create_default_admin():
    if not SessionLocal or not models:
        print("Skipping admin creation")
        return

    db = SessionLocal()

    try:
        admin_email = os.getenv(
            "ADMIN_EMAIL",
            "admin@enterprise.com"
        )

        admin_password = hash_password(
            os.getenv(
                "ADMIN_PASSWORD",
                "admin123"
            )
        )

        existing = db.query(models.User).filter(
            models.User.email == admin_email
        ).first()

        if not existing:
            admin = models.User(
                email=admin_email,
                password=admin_password,
                role="admin"
            )

            db.add(admin)
            db.commit()

            print("Default admin created")

    except Exception as e:
        print("Admin creation error:", str(e))

    finally:
        db.close()


create_default_admin()

# ==========================================================
# ROOT ROUTE
# ==========================================================

@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    if templates:
        try:
            return templates.TemplateResponse(
                "landing.html",
                {"request": request}
            )
        except Exception:
            pass

    return HTMLResponse("""
        <html>
            <head>
                <title>Enterprise Brain</title>
            </head>
            <body style="font-family: Arial; text-align:center; padding:50px;">
                <h1>🚀 Enterprise Brain Running Successfully</h1>
                <p>Hugging Face + Docker Ready</p>
                <p>Server is Live</p>
            </body>
        </html>
    """)

# ==========================================================
# LOGIN PAGE
# ==========================================================

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if templates:
        try:
            return templates.TemplateResponse(
                "login.html",
                {"request": request}
            )
        except Exception:
            pass

    return HTMLResponse("<h1>Login Page</h1>")

# ==========================================================
# REGISTER PAGE
# ==========================================================

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if templates:
        try:
            return templates.TemplateResponse(
                "register.html",
                {"request": request}
            )
        except Exception:
            pass

    return HTMLResponse("<h1>Register Page</h1>")

# ==========================================================
# SIMPLE CHAT TEST API
# ==========================================================

@app.post("/chat")
async def chat(
    request: Request,
    message: str = Form(...)
):
    try:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return JSONResponse({
                "reply": "OpenAI API Key not configured"
            })

        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        reply = response.choices[0].message.content

        return JSONResponse({
            "reply": reply
        })

    except Exception as e:
        return JSONResponse({
            "reply": f"Error: {str(e)}"
        })

# ==========================================================
# DEBUG ROUTE
# ==========================================================

@app.get("/debug")
def debug():
    return {
        "database_connected": bool(SessionLocal),
        "templates_found": bool(templates),
        "models_loaded": bool(models),
        "status": "Debug successful"
    }

# ==========================================================
# STARTUP LOG
# ==========================================================

print("====================================")
print("Enterprise Brain Started Successfully")
print("Hugging Face + Docker Ready 🚀")
print("====================================")
