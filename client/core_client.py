import asyncio
import sys

# ANSI цвета
RESET = "\033[0m"
CLEAR_SCREEN = "\033[H\033[J"
DEFAULT_COLOR = "\033[36m" # Стандартный голубой, пока сервер не выдал другой

MY_USERNAME = "Вы"
MY_COLOR = DEFAULT_COLOR

async def listen_to_server(reader):
    """Слушает сервер построчно и выводит сообщения в терминал"""
    global MY_COLOR
    try:
        while True:
            data = await reader.readline()
            if not data:
                print(f"\nСоединение с сервером разорвано.")
                break
            
            message = data.decode('utf-8')
            
            # Если сервер прислал нам наш цвет — сохраняем его и не выводим в консоль
            if message.startswith("COLOR_ASSIGN:"):
                MY_COLOR = message.split(":")[1].strip()
                continue
            
            sys.stdout.write(message)
            sys.stdout.flush()
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"\nОшибка при приеме данных: {e}")

async def send_to_server(writer):
    """Считывает ввод пользователя, стирает сырой текст и рисует красивое цветное эхо"""
    global MY_USERNAME, MY_COLOR
    loop = asyncio.get_event_loop()
    try:
        input_count = 0
        
        while True:
            line = await loop.run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            input_count += 1
            cleaned_line = line.strip()
            
            if input_count == 1 and cleaned_line:
                MY_USERNAME = cleaned_line

            writer.write(line.encode('utf-8'))
            await writer.drain()
            
            if input_count == 2:
                sys.stdout.write(CLEAR_SCREEN)
                sys.stdout.flush()
                continue
            
            if input_count > 2 and cleaned_line:
                # Стираем локальную сырую строку ввода
                sys.stdout.write("\033[F\033[K")
                
                # Рисуем рамочку, используя цвет, который нам выдал сервер!
                my_msg = f"{MY_COLOR}┌─[{MY_USERNAME}]{RESET}\n{MY_COLOR}└──╼ ${RESET} {cleaned_line}\n"
                sys.stdout.write(my_msg)
                sys.stdout.flush()

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"\nОшибка при отправке данных: {e}")

async def main():
    host = "127.0.0.1"
    port = 8000
    
    try:
        reader, writer = await asyncio.open_connection(host, port)
    except ConnectionRefusedError:
        print("Не удалось подключиться к server. Убедись, что core_server.py запущен.")
        return

    listen_task = asyncio.create_task(listen_to_server(reader))
    send_task = asyncio.create_task(send_to_server(writer))

    done, pending = await asyncio.wait(
        [listen_task, send_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    for task in pending:
        task.cancel()
        
    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nВыход из чата.")