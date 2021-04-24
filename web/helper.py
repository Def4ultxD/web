def time_finder(time):
    time_main = ''
    if time in [i for i in range(5, 12)]:
        time_main = 'Доброе утро, '
    if time in [i for i in range(12, 18)]:
        time_main = 'Добрый день, '
    if time in [i for i in range(18, 22)]:
        time_main = 'Добрый вечер, '
    if time < 5 or time > 21:
        time_main = 'Доброй ночи, '
    return time_main


def user_finder():
    with open('user', 'r', encoding='utf8') as file:
        name = file.readline()
    return name


def user_writer(login):
    with open('user', 'w', encoding='utf8') as file:
        file.write(str(login))


def text_writer(f):
    with open('text.txt', 'wb') as text:
        text.write(f)
