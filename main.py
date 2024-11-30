import streamlit as st
import pymysql


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
        print("Database connection successful.")
        return connection
    except Exception as ex:
        print('PROBLEM WITH Database Connection:', ex)
        return None


# Expense Tracker class
class ExpenseTracker:
    def __init__(self, user_id):
        self.user_id = user_id
        self.connection = get_db_connection()
        if self.connection:
            self.cursor = self.connection.cursor()
            self.create_table()
        else:
            raise ConnectionError("Failed to connect to the database.")

    def create_table(self):
        # Ensure the table has a `user_id` column to associate expenses with users
        query = """
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            date DATE NOT NULL,
            amount FLOAT NOT NULL,
            category VARCHAR(100),  # Adjusted length as needed
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)  # Assuming `users` table exists
        )
        """
        self.cursor.execute(query)
        self.connection.commit()

    def add_expense(self, date, amount, category, description=None):
        try:
            query = """
            INSERT INTO expenses (user_id, date, amount, category, description)
            VALUES (%s, %s, %s, %s, %s)
            """
            self.cursor.execute(query, (self.user_id, date, amount, category, description))
            self.connection.commit()
            print("Expense added successfully.")
        except pymysql.MySQLError as e:
            print(f"Error adding expense: {e}")
            raise

    def get_expenses(self, start_date=None, end_date=None):
        query = """
        SELECT date, amount, category, description 
        FROM expenses 
        WHERE user_id = %s
        """
        if start_date and end_date:
            query += " AND date BETWEEN %s AND %s"
            self.cursor.execute(query, (self.user_id, start_date, end_date))
        else:
            self.cursor.execute(query, (self.user_id,))
        return self.cursor.fetchall()

    def calculate_total_expenditure(self, start_date=None, end_date=None):
        query = "SELECT SUM(amount) FROM expenses WHERE user_id = %s"
        if start_date and end_date:
            query += " AND date BETWEEN %s AND %s"
            self.cursor.execute(query, (self.user_id, start_date, end_date))
        else:
            self.cursor.execute(query, (self.user_id,))
        return self.cursor.fetchone()[0] or 0.0

    def delete_expense(self, date, amount, category, description=None):
        try:
            query = """
            DELETE FROM expenses
            WHERE user_id = %s AND date = %s AND amount = %s AND category = %s AND (description = %s OR description IS NULL)
            """
            self.cursor.execute(query, (self.user_id, date, amount, category, description))
            self.connection.commit()
            print("Expense deleted successfully.")
        except pymysql.MySQLError as e:
            print(f"Error deleting expense: {e}")
            raise

    def close_connection(self):
        if self.connection and self.connection.open:
            self.cursor.close()
            self.connection.close()
