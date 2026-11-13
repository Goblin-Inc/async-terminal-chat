import sqlite3
import secrets
import string

class AuthManager:
    def __init__(self, db_path="server_users.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Создает таблицу, если её еще нет"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    secret_code TEXT NOT NULL
                )
            ''')
            conn.commit()

    def generate_code(self) -> str:
        """Генерирует красивый секретный код формата XXXX-XXXX"""
        alphabet = string.ascii_uppercase + string.digits
        part1 = ''.join(secrets.choice(alphabet) for _ in range(4))
        part2 = ''.join(secrets.choice(alphabet) for _ in range(4))
        return f"{part1}-{part2}"

    def register_user(self, username: str) -> str:
        """Регистрирует нового пользователя и возвращает его код"""
        secret_code = self.generate_code()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, secret_code) VALUES (?, ?)",
                    (username, secret_code)
                )
                conn.commit()
            return secret_code
        except sqlite3.IntegrityError:
            # На случай, если пока мы регистрировали, ник уже заняли
            return ""

    def check_user_exists(self, username: str) -> bool:
        """Проверяет, занят ли никнейм"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None

    def verify_code(self, username: str, code: str) -> bool:
        """Проверяет, подходит ли код к никнейму"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT secret_code FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row:
                return row[0] == code.strip().upper()
        return False