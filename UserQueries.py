import sqlite3

class UserQueries:
    def __init__(self):
        self.connect_to_database()

    def connect_to_database(self):
        self.conn = sqlite3.connect('users.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_queries (
                                    ID INTEGER PRIMARY KEY, 
                                    user_id INTEGER, 
                                    theme TEXT, 
                                    number_of_search INTEGER DEFAULT 0, 
                                    reaction_heart INTEGER DEFAULT 0, 
                                    reaction_like INTEGER DEFAULT 0, 
                                    reaction_dislike INTEGER DEFAULT 0
                                );''')
        self.conn.commit()

    def add_query(self, user_id, theme):
        theme = theme.lower()
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM user_queries WHERE user_id = ? AND theme = ?", (user_id, theme))
        existing_query = cursor.fetchone()
        if existing_query:
            cursor.execute("UPDATE user_queries SET number_of_search = number_of_search + 1 WHERE user_id = ? AND theme = ?", (user_id, theme))
        else:
            cursor.execute("INSERT INTO user_queries (user_id, theme, number_of_search) VALUES (?, ?, 1)", (user_id, theme))
        self.conn.commit()

    def increase_reaction(self, user_id, theme, reaction_type):
        theme = theme.lower()
        cursor = self.conn.cursor()

        print(user_id, theme, reaction_type)

        if reaction_type == "reaction_heart":
            cursor.execute("UPDATE user_queries SET reaction_heart = reaction_heart + 1 WHERE user_id = ? AND theme = ?", (user_id, theme))
            message = "You reacted with ❤️"
        elif reaction_type == "reaction_like":
            cursor.execute("UPDATE user_queries SET reaction_like = reaction_like + 1 WHERE user_id = ? AND theme = ?", (user_id, theme))
            message = "You reacted with 👍"
        elif reaction_type == "reaction_dislike":
            cursor.execute("UPDATE user_queries SET reaction_dislike = reaction_dislike + 1 WHERE user_id = ? AND theme = ?", (user_id, theme))
            message = "You reacted with 👎"
        else:
            message = ""

        self.conn.commit()
        return message


    def get_popular_queries(self, user_id, limit=3):
        self.cursor.execute("SELECT theme, SUM(number_of_search) AS total_searches FROM user_queries WHERE user_id = ? GROUP BY theme ORDER BY total_searches DESC LIMIT ?", (user_id, limit))
        rows = self.cursor.fetchall()
        popular_queries = [{"theme": row[0], "total_searches": row[1]} for row in rows]
        return popular_queries

    def get_total_queries(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT SUM(number_of_search) FROM user_queries WHERE user_id = ?", (user_id,))
        total_queries = cursor.fetchone()[0]
        return total_queries
