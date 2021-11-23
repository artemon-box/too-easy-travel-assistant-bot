from datetime import datetime
import os


def write_log(user, command: str, data):
    log_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    path = os.path.join('logs', f'{user}.log')
    with open(path, 'a', encoding='utf-8') as file:
        file.write(f'{log_date} | {command}|{data}\n{"-" * 50}\n')


def read_log(user: str) -> str:
    path = os.path.join('logs', f'{user}.log')
    if os.stat(path).st_size:
        with open(path, 'r', encoding='utf-8') as file:
            result = file.read()
        return result
    return 'История поиска пока пуста.'


def clear_history(user: str) -> None:
    path = os.path.join('logs', f'{user}.log')
    file = open(path, 'w', encoding='utf-8')
    file.close()
