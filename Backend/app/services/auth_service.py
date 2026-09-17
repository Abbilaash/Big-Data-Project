import logging
import httpx
from typing import Dict, Any, Tuple
from urllib.parse import urlencode

from app.config import get_settings
from app.database.mongodb import get_database
from app.database.neo4j import execute_query
from app.utils.helpers import generate_user_id, utc_now
from app.utils.security import create_access_token

logger = logging.getLogger("campusconnect.auth_service")

class AuthService:
    @staticmethod
    def get_google_login_url(state: str = "default_state") -> str:
        settings = get_settings()
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "state": state,
            "prompt": "consent"
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    @staticmethod
    async def exchange_google_code(code: str) -> Dict[str, Any]:
        settings = get_settings()
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(token_url, data=data)
            if token_resp.status_code != 200:
                logger.error(f"Google token exchange failed: {token_resp.text}")
                raise ValueError("Failed to exchange Google OAuth code")
            
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            
            userinfo_resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if userinfo_resp.status_code != 200:
                logger.error(f"Google userinfo fetch failed: {userinfo_resp.text}")
                raise ValueError("Failed to fetch user info from Google")
                
            return userinfo_resp.json()

    @staticmethod
    async def process_google_user(user_info: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Returns (user_doc, access_token)
        """
        settings = get_settings()
        db = get_database()
        
        google_id = str(user_info.get("id") or user_info.get("sub"))
        email = user_info.get("email")
        name = user_info.get("name", "")
        picture = user_info.get("picture", "")
        
        if not email:
            raise ValueError("Google profile does not contain a valid email address")

        # Check existing user
        user = await db.users.find_one({"$or": [{"google_id": google_id}, {"email": email}]})
        now = utc_now()
        
        # Determine role based on ADMIN_EMAIL
        role = "ADMIN" if settings.ADMIN_EMAIL and email.lower() == settings.ADMIN_EMAIL.lower() else "USER"

        if user:
            # Update role or google_id if necessary
            update_fields = {"updated_at": now}
            if user.get("role") != role:
                update_fields["role"] = role
            if not user.get("google_id"):
                update_fields["google_id"] = google_id
            if picture and not user.get("profile_picture"):
                update_fields["profile_picture"] = picture
                
            await db.users.update_one({"_id": user["_id"]}, {"$set": update_fields})
            user.update(update_fields)
        else:
            # Create incomplete user
            user_id = generate_user_id()
            user = {
                "user_id": user_id,
                "google_id": google_id,
                "email": email,
                "name": name,
                "year": None,
                "department": None,
                "profile_picture": picture,
                "role": role,
                "profile_completed": False,
                "created_at": now,
                "updated_at": now
            }
            await db.users.insert_one(user)

        # Generate JWT
        token_data = {
            "sub": user["user_id"],
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user["role"],
            "profile_completed": user["profile_completed"]
        }
        token = create_access_token(token_data)
        return user, token

    @staticmethod
    async def complete_profile(
        user_id: str, 
        name: str, 
        year: int, 
        department: str, 
        profile_picture: str = None
    ) -> Tuple[Dict[str, Any], str]:
        db = get_database()
        user = await db.users.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found")

        now = utc_now()
        update_data = {
            "name": name,
            "year": year,
            "department": department,
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
        SET u.name = $name, u.email = $email
        """
        await execute_query(cypher_query, {
            "user_id": user_id,
            "name": name,
            "email": user["email"]
        })

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
