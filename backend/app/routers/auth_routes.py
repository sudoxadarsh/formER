from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db
from ..models import User, Profile, utc_now
from ..schemas import UserRegister, UserLogin, UserResponse, Token
from ..auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserRegister, db = Depends(get_db)):
    # Check if user already exists
    existing = await db.users.find_one({"email": user_in.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    now = utc_now()
    user_doc = {
        "email": user_in.email.lower(),
        "name": user_in.name,
        "hashed_password": hash_password(user_in.password),
        "created_at": now,
        "updated_at": now
    }
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    user_doc["_id"] = result.inserted_id
    user = User(user_doc)

    # Initialize default empty profile with user's name and email
    default_personal = {
        "full_name": user.name,
        "first_name": user.name.split()[0] if user.name else "",
        "last_name": user.name.split()[-1] if len(user.name.split()) > 1 else "",
        "nationality": "Indian",
        "category": "General",
        "gender": "",
        "dob": ""
    }
    default_contact = {
        "email": user.email,
        "phone": "",
        "country": "India"
    }

    profile_doc = {
        "user_id": user_id,
        "personal_data": default_personal,
        "contact_data": default_contact,
        "education_data": {"tenth": {}, "twelfth": {}, "undergraduate": {}, "postgraduate": {}},
        "work_data": [],
        "documents_data": {},
        "preferences": {"auto_suggest": True, "strict_review": True, "encryption": "AES-256"},
        "updated_at": now
    }
    await db.profiles.insert_one(profile_doc)

    token = create_access_token({"sub": user_id, "email": user.email})
    return Token(access_token=token, user=UserResponse.model_validate(user))

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db = Depends(get_db)):
    user_doc = await db.users.find_one({"email": credentials.email.lower()})
    if not user_doc or not verify_password(credentials.password, user_doc.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    user = User(user_doc)
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return Token(access_token=token, user=UserResponse.model_validate(user))

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
