import httpx
from app.config import settings
from typing import Optional
import json

class SupabaseClient:
    def __init__(self, admin: bool = False):
        key = settings.SUPABASE_SERVICE_ROLE_KEY if admin else settings.SUPABASE_ANON_KEY

        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self.base_url = f"{settings.SUPABASE_URL}/rest/v1"

    async def get(self, table: str, params: Optional[dict] = None):
        """Fetch records from a table"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(
                f"{self.base_url}/{table}",
                headers=self.headers,
                params=params or {},
            )
            res.raise_for_status()
            return res.json()

    async def post(self, table: str, data: dict | list):
        """
        Insert record(s) into a table
        Returns the inserted data
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(
                    f"{self.base_url}/{table}",
                    headers=self.headers,
                    json=data,
                )
                
                if res.status_code == 409:
                    # Get detailed error
                    error_detail = res.text
                    print(f"409 Conflict on {table}")
                    print(f"Data attempted: {json.dumps(data, indent=2, default=str)}")
                    print(f"Error detail: {error_detail}")
                    raise httpx.HTTPError(f"Conflict inserting into {table}: {error_detail}")
                
                res.raise_for_status()
                return res.json()
                
            except httpx.HTTPStatusError as e:
                print(f"HTTP Error on {table}: {e}")
                print(f"Response: {e.response.text}")
                raise

    async def patch(self, table: str, params: dict, data: dict):
        """Update record(s) in a table"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.patch(
                f"{self.base_url}/{table}",
                headers=self.headers,
                params=params,
                json=data,
            )
            res.raise_for_status()
            return res.json()

    async def upsert(self, table: str, data: dict | list):
        """
        Upsert (insert or update) record(s)
        Uses on_conflict to handle duplicates
        """
        headers = {
            **self.headers,
            "Prefer": "resolution=merge-duplicates,return=representation"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.post(
                f"{self.base_url}/{table}",
                headers=headers,
                json=data,
            )
            res.raise_for_status()
            return res.json()

    async def delete(self, table: str, params: dict):
        """Delete record(s) from a table"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.delete(
                f"{self.base_url}/{table}",
                headers=self.headers,
                params=params,
            )
            res.raise_for_status()
            return res.json()
