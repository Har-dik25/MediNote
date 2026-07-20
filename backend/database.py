import sqlite3
import os
from passlib.context import CryptContext

# Set up the password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use an absolute path for the SQLite DB to ensure it is created in the backend folder
DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def init_db():
    """Initializes the database and creates the users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            clinicName TEXT,
            specialty TEXT,
            phone TEXT,
            region TEXT,
            role TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user_by_email(email: str):
    """Fetches a user from the database by their email."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None

def create_user(user_data: dict):
    """Inserts a new user into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Hash the password
    password_hash = pwd_context.hash(user_data['password'])
    
    # Generate a simple ID
    import uuid
    user_id = "u_" + str(uuid.uuid4())[:8]
    
    try:
        cursor.execute('''
            INSERT INTO users (id, name, email, password_hash, clinicName, specialty, phone, region, role)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            user_data.get('name', ''),
            user_data['email'],
            password_hash,
            user_data.get('clinicName', ''),
            user_data.get('specialty', ''),
            user_data.get('phone', ''),
            user_data.get('region', 'UK (NICE)'),
            'clinician'
        ))
        conn.commit()
        
        # Return the created user without the password hash
        user_response = {
            "id": user_id,
            "name": user_data.get('name', ''),
            "email": user_data['email'],
            "clinicName": user_data.get('clinicName', ''),
            "specialty": user_data.get('specialty', ''),
            "phone": user_data.get('phone', ''),
            "region": user_data.get('region', 'UK (NICE)'),
            "role": 'clinician'
        }
        return user_response
    except sqlite3.IntegrityError:
        # Email already exists
        return None
    finally:
        conn.close()

def verify_password(plain_password: str, hashed_password: str):
    """Verifies a plain password against the hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

# Initialize the DB table on import
init_db()
