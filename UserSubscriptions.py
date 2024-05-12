import sqlite3
from datetime import datetime


class UserSubscriptions:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect_to_database()

    def connect_to_database(self):
        self.conn = sqlite3.connect('users.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS subscriptions
                              (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, topic TEXT, subscribed_at TEXT)''')
        self.conn.commit()

    def subscribe_to_topic(self, user_id, topic):
        self.cursor.execute("SELECT topic FROM subscriptions WHERE user_id = ? AND LOWER(topic) = LOWER(?)", (user_id, topic))
        existing_subscription = self.cursor.fetchone()

        if existing_subscription:
            return f"You are already subscribed to '{topic}'."
        else:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("INSERT INTO subscriptions (user_id, topic, subscribed_at) VALUES (?, ?, ?)",
                                (user_id, topic, current_time))
            self.conn.commit()
            return f"Successfully subscribed to '{topic}'."

    def get_user_subscriptions_with_id(self, user_id):
        self.cursor.execute("SELECT id, topic FROM subscriptions WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()

    def get_user_subscriptions(self, user_id):
        self.cursor.execute("SELECT topic FROM subscriptions WHERE user_id = ?", (user_id,))
        return self.cursor.fetchall()

    def unsubscribe_from_topic(self, subscription_id):
        self.cursor.execute("DELETE FROM subscriptions WHERE id = ?", (subscription_id,))
        self.conn.commit()

    def drop_table(self):
        self.cursor.execute('''DROP TABLE subscriptions''')
        self.conn.commit()
