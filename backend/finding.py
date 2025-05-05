from dotenv import load_dotenv
import os

load_dotenv()  # Load the .env file

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

print(f"VITE_SUPABASE_URL: {url}")
print(f"VITE_SUPABASE_ANON_KEY: {key}")

if not url or not key:
    raise ValueError("Supabase URL and/or key is missing!")
