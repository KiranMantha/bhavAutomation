from supabase import create_client

DB_URL = 'https://vbxaqvyvmjpxogaenvdy.supabase.co'
SECRET = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZieGFxdnl2bWpweG9nYWVudmR5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzYzMzI1OTEsImV4cCI6MjA1MTkwODU5MX0.1SqsgxgrKTsZMuGr6oDPhULjjjPzjPpaQRy1L1ZFZWU'

supabase = create_client(DB_URL, SECRET)

def get_supabase_instance():
    return supabase