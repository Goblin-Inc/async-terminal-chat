import asyncio
import random
from auth_db import AuthManager

# ANSI цвета для разметки
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"

# Пуническая палитра ярких цветов для юзеров
USER_COLORS = [
    "\033[32m", # Зеленый
    "\033[33m", # Желтый
    "\033[34m", # Синий
    "\033[35m", # Пурпурный
    "\033[36m", # Голубой
    "\033[91m", # Ярко-красный
    "\033[92m", # Ярко-зеленый
    "\033[93m", # Ярко-желтый
    "\033[94m", # Ярко-синий
    "\033[95m", # Ярко-пурпурный
    "\033[96m", # Ярко-голубой
]

class ChatServer:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.db = AuthManager()
        self.clients = {}      # {writer: username}
        self.user_colors = {}  # {username: color_code}

    def get_user_color(self, username: str) -> str:
        """Закрепляет за юзером случайный цвет, если его еще нет"""
        if username not in self.user_colors:
            self.user_colors[username] = random.choice(USER_COLORS)
        return self.user_colors[username]

    async def broadcast(self, message: str, exclude_writer=None):
        """Рассылка сообщения всем авторизованным пользователям"""
        for writer in self.clients:
            if writer != exclude_writer:
                try:
                    writer.write(message.encode('utf-8'))
                    await writer.drain()
                except Exception:
                    pass

    async def handle_auth(self, reader, writer) -> str:
        """Логика авторизации пользователя при подключении"""
        try:
            writer.write(f"{CYAN}--- Добро пожаловать в Приватный Чат ---{RESET}\nВведите ваш никнейм:\n".encode('utf-8'))
            await writer.drain()
            
            data = await reader.readline()
            username = data.decode('utf-8').strip()
            
            if not username:
                writer.write(f"{RED}Пустой никнейм недопустим. Отключение.{RESET}\n".encode('utf-8'))
                await writer.drain()
                return ""

            if self.db.check_user_exists(username):
                writer.write(f"{YELLOW}Этот никнейм занят.{RESET}\nВведите ваш секретный код доступа:\n".encode('utf-8'))
                await writer.drain()
                
                data = await reader.readline()
                code = data.decode('utf-8').strip()
                
                if self.db.verify_code(username, code):
                    writer.write(f"{GREEN}Авторизация успешна! Вход в чат...{RESET}\n".encode('utf-8'))
                    await writer.drain()
                    return username
                else:
                    writer.write(f"{RED}Неверный код доступа. Отключение.{RESET}\n".encode('utf-8'))
                    await writer.drain()
                    return ""
            else:
                new_code = self.db.register_user(username)
                welcome_msg = (
                    f"\n{GREEN}Вы успешно зарегистрированы!{RESET}\n"
                    f"Ваш секретный код доступа: {YELLOW}{new_code}{RESET}\n\n"
                    f"{RED}[ ВНИМАНИЕ ]{RESET} Запомни или запиши этот код.\n"
                    f"Иначе ты больше не сможешь зайти под юзером {CYAN}{username}{RESET}.\n\n"
                    f"Нажмите [Enter], чтобы скрыть код и войти в чат..."
                )
                writer.write(welcome_msg.encode('utf-8'))
                await writer.drain()
                
                await reader.readline()
                return username
                
        except Exception as e:
            print(f"Ошибка при авторизации: {e}")
            return ""

    async def handle_client(self, reader, writer):
        """Основной цикл работы с клиентом после подключения"""
        username = await self.handle_auth(reader, writer)
        
        if not username:
            writer.close()
            await writer.wait_closed()
            return

        self.clients[writer] = username
        print(f"[+] {username} подключился к чату.")
        
        # Назначаем цвет
        color = self.get_user_color(username)
        
        # Системное сообщение о входе отправляем с цветом зашедшего
        await self.broadcast(f"\n{color}[+] {username} зашел в комнату.{RESET}\n")

        # Отправляем клиенту маркер с кодом его цвета, чтобы он знал, как красить себя локально
        writer.write(f"COLOR_ASSIGN:{color}\n".encode('utf-8'))
        await writer.drain()

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                
                message = data.decode('utf-8').strip()
                if message:
                    # Сервер пакует сообщение, используя уникальный цвет юзера
                    formatted_msg = f"{color}┌─[{username}]{RESET}\n{color}└──╼ ${RESET} {message}\n"
                    await self.broadcast(formatted_msg, exclude_writer=writer)
                    
        except asyncio.CancelledError:
            pass
        finally:
            if writer in self.clients:
                del self.clients[writer]
            print(f"[-] {username} покинул чат.")
            await self.broadcast(f"\n{RED}[-] {username} покинул комнату.{RESET}\n")
            writer.close()
            await writer.wait_closed()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        print(f"[*] Сервер запущен на {self.host}:{self.port} и готов принимать гостей...")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    server = ChatServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n[*] Сервер остановлен.")