from supabase import create_client

DB_URL = 'https://tbobimigdddygwhenclp.supabase.co'
SECRET = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRib2JpbWlnZGRkeWd3aGVuY2xwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTYwMDcyNjEsImV4cCI6MjA3MTU4MzI2MX0.HDkogP6nZepcYRKr-ZE0605RHODGARjPWVVUOy06XUU'

supabase = create_client(DB_URL, SECRET)

def get_supabase_instance():
    return supabase