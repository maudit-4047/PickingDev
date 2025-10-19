import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv 

# Load environment variables from .env file in backend directory
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)


# Supabase API config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Debug: Print environment variables (remove in production)
print(f"Loading .env from: {env_path}")
print(f"SUPABASE_URL found: {'Yes' if SUPABASE_URL else 'No'}")
print(f"SUPABASE_KEY found: {'Yes' if SUPABASE_KEY else 'No'}")

# Validate environment variables
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL not found in environment variables")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY not found in environment variables")

# Initialize Supabase client
from supabase import create_client, Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


