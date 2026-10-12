import logging
from pymongo.errors import DuplicateKeyError
from typing import Dict, Any, Tuple, Optional

from app.config import get_settings
from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.utils.helpers import generate_user_id, utc_now
from app.utils.security import create_access_token, hash_password, verify_password

logger = logging.getLogger("campusconnect.auth_service")

class AuthService:
    @staticmethod
    async def register_user(
        name: str,
        email: str,
        password: str,
        year: int,
        department: str,
        profile_picture: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        """Register a new user with email and password and sync to Neo4j."""
        settings = get_settings()
        db = get_database()
        email_clean = email.strip().lower()

        # Check existing user
        existing = await db.users.find_one({"email": email_clean})
        if existing:
            raise ValueError("An account with this email already exists.")

        now = utc_now()
        role = "ADMIN" if settings.ADMIN_EMAIL and email_clean == settings.ADMIN_EMAIL.lower() else "USER"
        user_id = generate_user_id()
        pw_hash = hash_password(password)

        user_doc = {
            "user_id": user_id,
            "email": email_clean,
            "password_hash": pw_hash,
            "name": name.strip(),
            "year": year,
            "department": department.strip(),
            "profile_picture": profile_picture,
            "role": role,
            "profile_completed": True,
            "created_at": now,
            "updated_at": now
        }

        try:
            await db.users.insert_one(user_doc)
        except DuplicateKeyError:
            raise ValueError("An account with this email already exists.")

        # Sync to Neo4j graph
        cypher_query = """
        MERGE (u:User {user_id: $user_id})
        SET u.name = $name, u.email = $email, u.department = $department, u.year = $year
        """
        await execute_query(cypher_query, {
            "user_id": user_id,
            "name": user_doc["name"],
            "email": email_clean,
            "department": department.strip(),
            "year": year,
        }, required=False)

        # Generate JWT
        token_data = {
            "sub": user_id,
            "user_id": user_id,
            "email": email_clean,
            "role": role,
            "profile_completed": True
        }
        token = create_access_token(token_data)
        return user_doc, token

    @staticmethod
    async def login_user(email: str, password: str) -> Tuple[Dict[str, Any], str]:
        """Authenticate user by email and password, issuing a JWT token."""
        settings = get_settings()
        db = get_database()
        email_clean = email.strip().lower()

        user = await db.users.find_one({"email": email_clean})
        if not user or not user.get("password_hash"):
            raise ValueError("Invalid email or password.")

        if not verify_password(password, user["password_hash"]):
            raise ValueError("Invalid email or password.")

        # If email matches ADMIN_EMAIL, ensure role is ADMIN
        if settings.ADMIN_EMAIL and email_clean == settings.ADMIN_EMAIL.lower() and user.get("role") != "ADMIN":
            await db.users.update_one({"_id": user["_id"]}, {"$set": {"role": "ADMIN"}})
            user["role"] = "ADMIN"

        token_data = {
            "sub": user["user_id"],
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user.get("role", "USER"),
            "profile_completed": bool(user.get("profile_completed", True))
        }
        token = create_access_token(token_data)
        return user, token

    @staticmethod
    async def complete_profile(
        user_id: str, 
        name: str, 
        year: int, 
        department: str, 
        profile_picture: Optional[str] = None
    ) -> Tuple[Dict[str, Any], str]:
        db = get_database()
        user = await db.users.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")

        now = utc_now()
        update_data = {
            "name": name.strip(),
            "year": year,
            "department": department.strip(),
            "profile_completed": True,
            "updated_at": now
        }
        if profile_picture:
            update_data["profile_picture"] = profile_picture

        await db.users.update_one({"user_id": user_id}, {"$set": update_data})
        user.update(update_data)

        # Sync to Neo4j graph
        cypher_query = """
        MERGE (u:User {user_id: $user_id})
        SET u.name = $name, u.email = $email, u.department = $department, u.year = $year
        """
        await execute_query(cypher_query, {
            "user_id": user_id,
            "name": update_data["name"],
            "email": user["email"],
            "department": update_data["department"],
            "year": update_data["year"],
        }, required=False)

        # Issue updated full JWT
        token_data = {
            "sub": user["user_id"],
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user["role"],
            "profile_completed": True
        }
        token = create_access_token(token_data)
        return user, token

