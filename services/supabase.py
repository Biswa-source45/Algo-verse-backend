import httpx
from app.config import settings

class SupabaseClient:
    def __init__(self, admin: bool = False):
        key = settings.SUPABASE_SERVICE_ROLE_KEY if admin else settings.SUPABASE_ANON_KEY

        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }
        self.base_url = f"{settings.SUPABASE_URL}/rest/v1"

    async def get(self, table: str, params: dict = None):
        async with httpx.AsyncClient() as client:
            res = await client.get(
                f"{self.base_url}/{table}",
                headers=self.headers,
                params=params,
            )
            res.raise_for_status()
            return res.json()

    async def post(self, table: str, data: dict):
        async with httpx.AsyncClient() as client:
            res = await client.post(
                f"{self.base_url}/{table}",
                headers=self.headers,
                json=data,
            )
            res.raise_for_status()
            return res.json()

    async def patch(self, table: str, params: dict, data: dict):
        async with httpx.AsyncClient() as client:
            res = await client.patch(
                f"{self.base_url}/{table}",
                headers=self.headers,
                params=params,
                json=data,
            )
            res.raise_for_status()
            return res.json()
