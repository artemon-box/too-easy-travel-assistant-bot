from datetime import datetime
import os


def write_log(user: int, command: str, data: str):
    log_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    path = os.path.join('logs', f'{user}.log')
    with open(path, 'a', encoding='utf-8') as file:
        file.write(f'{log_date} | {command}|{data}\n{"-" * 50}\n')


def read_log(user: int) -> str:
    path = os.path.join('logs', f'{user}.log')
    if not os.path.exists(path) or not os.stat(path).st_size:
        return 'История поиска пока пуста.'
    with open(path, 'r', encoding='utf-8') as file:
        result = file.read()
    return result[-4096:]


def clear_history(user: int) -> None:
    path = os.path.join('logs', f'{user}.log')
    file = open(path, 'w', encoding='utf-8')
    file.close()
