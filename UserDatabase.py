import sqlite3

class UserDatabase:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect_to_database()

    def connect_to_database(self):
        self.conn = sqlite3.connect('users.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                              (id INTEGER PRIMARY KEY
                              , user_id INTEGER UNIQUE
                              , first_name TEXT
                              , last_name TEXT
                              , user_name TEXT
                              , language_code TEXT
                              , recommendation INTEGER
                              , recommendation_time TEXT DEFAULT '12:00'
                              , notification_frequency TEXT DEFAULT 'weekly'
                              , notification_time TEXT DEFAULT '12:00')''')

        self.conn.commit()

    def add_user(self, user_id, first_name, last_name, user_name):
        with self.conn:
            self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            existing_user = self.cursor.fetchone()
            if not existing_user:
                self.cursor.execute("INSERT INTO users (user_id, first_name, last_name, user_name) VALUES (?, ?, ?, ?)", (user_id, first_name, last_name, user_name))


    def set_language_code(self, user_id, language_code):
        self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        existing_user = self.cursor.fetchone()
        if existing_user:
            self.cursor.execute("UPDATE users SET language_code = ? WHERE user_id = ?", (language_code, user_id))
        else:
            self.cursor.execute("INSERT INTO users (user_id, chat_id, language_code) VALUES (?, ?)", (user_id, language_code))
        self.conn.commit()


    def get_language_code(self, user_id):
        self.cursor.execute("SELECT language_code FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else ''

    def set_recommendation(self, user_id, recommendation):
        self.cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        existing_user = self.cursor.fetchone()
        if existing_user:
            self.cursor.execute("UPDATE users SET recommendation = ? WHERE user_id = ?", (recommendation, user_id))
        else:
            self.cursor.execute("INSERT INTO users (user_id, recommendation) VALUES (?, ?)", (user_id, recommendation))
        self.conn.commit()

    def get_recommendation(self, user_id):
        self.cursor.execute("SELECT recommendation FROM users WHERE user_id=?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else ''

    def get_users_for_recommendation(self):
        self.cursor.execute("SELECT user_id FROM users WHERE recommendation = 1")
        users_with_recommendation = [row[0] for row in self.cursor.fetchall()]
        return users_with_recommendation

    def set_recommendation_time(self, user_id, recommendation_time):
        self.cursor.execute("UPDATE users SET recommendation_time = ? WHERE user_id = ?", (recommendation_time, user_id))
        self.conn.commit()

    def set_notification_time(self, user_id, notification_time):
        self.cursor.execute("UPDATE users SET notification_time = ? WHERE user_id = ?", (notification_time, user_id))
        self.conn.commit()

    def get_recommendation_time(self, user_id):
        self.cursor.execute("SELECT recommendation_time FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else ''

    def get_notification_time(self, user_id):
        self.cursor.execute("SELECT notification_time FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else ''

    def set_notification_frequency(self, user_id, frequency):
        with self.conn:
            self.cursor.execute("UPDATE users SET notification_frequency = ? WHERE user_id = ?", (frequency, user_id))
            self.conn.commit()

    def get_notification_frequency(self, user_id):
        self.cursor.execute("SELECT notification_frequency FROM users WHERE user_id = ?", (user_id,))
        result = self.cursor.fetchone()
        return result[0] if result else ''

    def drop_table(self, user_id):
        self.cursor.execute('''DROP TABLE users''')
        self.conn.commit()
