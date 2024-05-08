import sqlite3

class UserLocations:
    def __init__(self):
        self.connect_to_database()

    def connect_to_database(self):
        self.conn = sqlite3.connect('users.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_locations
                              (ID INTEGER PRIMARY KEY, user_id INTEGER, latitude TEXT, longitude TEXT, names TEXT)''')
        self.conn.commit()

    def add_location(self, user_id, latitude, longitude, names):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM user_locations WHERE user_id = ? AND latitude = ? AND longitude = ?", (user_id, latitude, longitude))
        existing_query = cursor.fetchone()
        if not existing_query:
            cursor.execute("INSERT INTO user_locations (user_id, latitude, longitude, names) VALUES (?, ?, ?, ?)", (user_id, latitude, longitude, names))
        self.conn.commit()
