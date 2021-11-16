from datetime import datetime


def write_log(user, command: str, data):
    log_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(f'{user}.log', 'a', encoding='utf-8') as file:
        file.write(f'{log_date} | {command}\t| {data}\n')


def read_log(user: str):
    with open(f'{user}.log', 'r', encoding='utf-8') as file:
        result = file.read()
    return result
