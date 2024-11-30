import pymysql
import hashlib
import streamlit as st

# Database connection setup
def get_db_connection():
    try:
        # Connect to MySQL database
        connection = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='MySQLpassword1234',
            db='walletnote'  # Ensure this matches your database name
        )
        return connection
    except Exception as ex:
        st.error(f"Database Connection Error: {ex}")
        return None

# Hashing function for passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User Authentication Class
class UserAuth:
    def __init__(self):
        self.connection = get_db_connection()
        if not self.connection:
            raise ConnectionError("Failed to connect to the database.")
        self.cursor = self.connection.cursor()

    def create_users_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL
        );
        """
        self.cursor.execute(query)
        self.connection.commit()

    def register_user(self, username, password):
        try:
            password_hash = hash_password(password)
            query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
            self.cursor.execute(query, (username, password_hash))
            self.connection.commit()
            return True
        except pymysql.MySQLError as e:
            st.error(f"Error during registration: {e}")
            return False

    def authenticate_user(self, username, password):
        try:
            password_hash = hash_password(password)
            query = "SELECT id FROM users WHERE username = %s AND password_hash = %s"
            self.cursor.execute(query, (username, password_hash))
            result = self.cursor.fetchone()
            if result:
                return result[0]  # Return user ID if authenticated
            return None
        except pymysql.MySQLError as e:
            st.error(f"Error during authentication: {e}")
            return None
