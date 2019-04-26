import pygame as pg
import os
import sys
import random
import win32api


class KIRA:
    def __init__(self):
        self.player = False
        self.playlist = []
        self.volume = 0.5

    def play_music(self):
        if len(self.playlist) == 0:
            self.create_playlist(input('Музыка в плейлисте закончилась.'
                                       ' Напишите название плейлиста для запуска: '))
        music = random.choice(self.playlist)
        del self.playlist[self.playlist.index(music)]
        pg.mixer.music.load(music)
        pg.mixer.music.play()
        pg.mixer.music.set_volume(self.volume)

    def create_playlist(self, name):
        # Ловим название плейлиста и создаем путь
        path = 'data\\playlists\\'
        playlist_name = str(name) + '.txt'
        fullpath = path + playlist_name
        # Записываем данные с файла в список
        with open(fullpath, 'r') as PlayFile:
            self.playlist = [line.strip() for line in PlayFile]

    def search(self, disk, name, exp):
        disk = disk + ':\\'
        list_files = []
        for root, dirs, files in os.walk(disk):
            for file in files:
                if name:
                    if name in file:
                        if exp:
                            if file.endswith(exp):
                                list_files.append(os.path.join(root, file))
                        else:
                            list_files.append(os.path.join(root, file))
                else:
                    if exp:
                        if file.endswith(exp):
                            list_files.append(os.path.join(root, file))
                    else:
                        list_files.append(os.path.join(root, file))
        return list_files

    def start_file(self, disk, name):
        file = self.search(disk, name, '.exe')
        if len(file) == 1:
            win32api.WinExec(file[0])
            print('Готово!')
        elif len(file) > 1:
            print('Ошибка! Файлов по вашим параметрам оказалось несколько. Запуск невозможен')
        else:
            print('Ошибка! Файл не найден!')

    def check_commands(self, sentence):
        if 'выключи музыку' in sentence.lower():
            self.player = False
            pg.quit()
        if 'включи музыку' in sentence.lower() and not self.player:
            self.create_playlist(input('Напишите название плейлиста для запуска: '))
            pg.init()
            pg.display.set_mode((200, 100))
            pg.mixer.init(frequency=44100, channels=2, buffer=4096)
            self.player = True
        if 'следующая' in sentence.lower():
            self.play_music()
        if 'выход' in sentence.lower():
            print('До следующей встречи ;)')
            sys.exit()
        if 'убавь громкость на' in sentence.lower():
            value = [int(i) for i in sentence.split() if i.isdigit()][0] / 100
            self.volume -= value
            if self.volume < 0:
                self.volume = 0
                print('Громкость на минимальном значении')
            pg.mixer.music.set_volume(self.volume)
        if 'прибавь громкость на' in sentence.lower():
            value = [int(i) for i in sentence.split() if i.isdigit()][0] / 100
            self.volume += value
            if self.volume > 1:
                self.volume = 1
                print('Громкость на максимальном значении')
            pg.mixer.music.set_volume(self.volume)
        if 'установить громкость на' in sentence.lower():
            value = [int(i) for i in sentence.split() if i.isdigit()][0] / 100
            self.volume = value
            pg.mixer.music.set_volume(self.volume)
        if 'найди файл' in sentence.lower():
            disk = input('На каком диске вы хотите найти файл: ')
            name_true = input('Ищете ли вы файл по имени? ').lower()
            if name_true == 'да':
                name = input('Укажите имя файла: ')
            else:
                name = None
            exp_true = input('Ищете ли вы файл с определенным расширением? ')
            if exp_true == 'да':
                exp = input('Введите расширение файла формата ".расширение": ')
            else:
                exp = None
            list_files = self.search(disk, name, exp)
            if len(list_files) == 1:
                print('Файл находится в каталоге:', list_files[0])
            elif len(list_files) > 1:
                print('Найденных файлов несколько и находятся они в этих каталогах:\n', '\n'.join(list_files), sep='')
            else:
                print('Не найдено ни одного файла по вашим параметрам')
        if 'запусти файл' in sentence.lower():
            disk = input('Введите диск, на котором лежит файл: ')
            name = input('Введите имя файла: ')
            self.start_file(disk, name)

    def main(self):
        print('''Привет. Я Кира - бот-помощник.
Доступные команды на данный момент, если данные команды будут в вашем предложение, то тогда команда будет выполнена:
- Музыка:
    - Включи музыку - запустить музыку
    - Следующий трек - следующий трек
    - Выключи музыку - выключить музыку
    - Убавь громкость на *значение в процентах* - убавить музыку
    - Прибавь громкость на *значение в процентах* - прибавить музыку
    - Установить громкость на *значение в процентах* - установить громкость на какое-то значение 
- Файлы:
    - Найди файлы - поиск файлов по вашим параметрам, которые вы указываете в процессе
    - Запусти файл - открывает файл с расширением .exe
- Выход - завершить сеанс со мной''')

        # Основной цикл программы
        while True:
            # Ловим команды
            string = input()
            # Проверяем команды
            self.check_commands(string)
            # Повторяем, что написал юзер
            print('Вы написали:', string)
            # Если плеер существует, то музыка живет
            if self.player:
                if not pg.mixer.music.get_busy():
                    self.play_music()


if __name__ == '__main__':
    KIRA().main()
