import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv()

# Configuración de la base de datos desde variables de entorno
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
    "dbname":   os.getenv("DB_NAME", "voz_db"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def get_connection():
    #Conexión a PostgreSQL.
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def init_db():
    #Crea las tablas si no existen y verifica la conexión.
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id          SERIAL PRIMARY KEY,
                nombre      TEXT NOT NULL UNIQUE,
                activo      BOOLEAN NOT NULL DEFAULT TRUE,
                creado_en   TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # Tabla de logs de acceso
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_acceso (
                id          SERIAL PRIMARY KEY,
                nombre      TEXT NOT NULL,
                resultado   TEXT NOT NULL,
                confianza   FLOAT,
                fecha       TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        conn.commit()
        conn.close()
        print("Conexión a PostgreSQL exitosa")

    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")