from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el archivo .env")


def get_client() -> Client:
    """Retorna el cliente de Supabase."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def init_db():
    """
    Esta función solo verifica que la conexión funcione.
    """
    try:
        client = get_client()
        client.table("usuarios").select("id").limit(1).execute()
        print("✅ Conexión a Supabase exitosa")
    except Exception as e:
        print(f"Error conectando a Supabase: {e}")