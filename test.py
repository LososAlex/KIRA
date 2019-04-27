import os
import sys
import random
import win32api
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog
from PyQt5.QtMultimedia import QMediaPlaylist, QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from PyQt5 import uic


class KIRA(QMainWindow):
    def __init__(self):
        super().__init__()
        self.player = False
        self.volume = 50
        self.string = None
        uic.loadUi('example.ui', self)
        self.pushButton.setText('Ответить')
        self.pushButton.clicked.connect(self.ok)
        self.playlist_list = []

        self.playlist = QMediaPlaylist(self)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.player = QMediaPlayer()
        self.player.setVolume(self.volume)

    def append_text(self, text):
        self.textEdit.append(text)

    def get_text(self):
        self.string = self.lineEdit.text()
        self.lineEdit.clear()
        self.append_text(self.string)
        return self.string

    def showDialog(self, question):
        text, ok = QInputDialog.getText(self, 'У меня есть вопрос', question)
        if ok:
            return str(text)

    def play_music(self):
        if self.playlist.isEmpty():
            self.create_playlist(self.showDialog('Введите название плейлиста:'))
            self.player.setPlaylist(self.playlist)
        else:
            print(1)
        self.player.play()

    def create_playlist(self, name):
        # Ловим название плейлиста и создаем путь
        path = 'data\\playlists\\'
        playlist_name = str(name) + '.txt'
        fullpath = path + playlist_name
        # Записываем данные с файла в список
        with open(fullpath, 'r') as PlayFile:
            playlist = [line.strip() for line in PlayFile]
        for track in playlist:
            url = QUrl.fromLocalFile(track)
            content = QMediaContent(url)
            self.playlist_list.append(content)
            self.playlist.addMedia(content)

    def mix(self):
        self.player.stop()
        self.playlist.clear()
        playlist_copy = self.playlist_list
        for i in range(len(self.playlist_list)):
            track = random.choice(playlist_copy)
            del playlist_copy[playlist_copy.index(track)]
            self.playlist.addMedia(track)
        self.player.setPlaylist(self.playlist)
        self.player.play()

    def playlist_from_dir_to_txt(self):
        directory = self.showDialog('Введите путь к папке, где лежит музыка:')
        music = '\n'.join(self.search(directory, None, '.mp3'))
        name_playlist = self.showDialog('Введите название для этого плейлиста:')
        path = 'data\\playlists\\' + name_playlist + '.txt'
        with open(path, 'w') as f:
            f.write(music)

    def search(self, path, name, exp, search_dir=False):
        list_files = []
        for root, dirs, files in os.walk(path):
            if not search_dir:
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
            else:
                for dir in dirs:
                    if name:
                        if name in dir:
                            list_files.append(os.path.join(root, dir))
                    else:
                        list_files.append(os.path.join(root, dir))
        return list_files

    def start_file(self, dir, name):
        name = name.split('.')
        name, exp = name
        exp = '.' + exp
        file = self.search(dir, name, exp)
        if len(file) == 1:
            os.popen('start {}'.format(str(file[0])))
            self.append_text('Готово!')
        elif len(file) > 1:
            self.append_text('Ошибка! Файлов по вашим параметрам оказалось несколько. Запуск невозможен')
        else:
            self.append_text('Ошибка! Файл не найден!')

    def check_commands(self, sentence):
        if 'включи музыку' in sentence.lower() and not self.player.isAudioAvailable():
            self.play_music()
        if self.player.isAudioAvailable():
            if 'выключи музыку' in sentence.lower():
                self.player.stop()
                self.append_text('Готово!')
            if 'следующий трек' in sentence.lower():
                self.playlist.next()
            if 'предыдущий трек' in sentence.lower():
                self.playlist.previous()
            if 'убавь громкость' in sentence.lower():
                self.volume -= int(self.showDialog('На какое значение вы хотите убавить громкость?'))
                if self.volume < 0:
                    self.volume = 0
                    self.append_text('Вы достигли минимальной громкости')
                self.player.setVolume(self.volume)
            if 'прибавь громкость' in sentence.lower():
                self.volume += int(self.showDialog('На какое значение вы хотите прибавить громкость?'))
                if self.volume > 100:
                    self.volume = 100
                    self.append_text('Вы достигли максимальной громкости')
                self.player.setVolume(self.volume)
            if 'установи громкость' in sentence.lower():
                self.volume = int(self.showDialog('На какое значение вы хотите установить громкость?'))
                self.player.setVolume(self.volume)
            if 'перемешать треки' in sentence.lower():
                self.mix()
        if 'создай плейлист' in sentence.lower():
            self.playlist_from_dir_to_txt()
            self.append_text('Готово!')
        if 'найди файл' in sentence.lower():
            path = self.showDialog('Введите путь откуда хотите начать поиск папки:')
            name_true = self.showDialog('Ищете ли вы файл по имени?').lower()
            if name_true == 'да':
                name = self.showDialog('Укажите имя файла:')
            else:
                name = None
            exp_true = self.showDialog('Ищете ли вы файл с определенным расширением?')
            if exp_true == 'да':
                exp = self.showDialog('Введите расширение файла формата ".расширение":')
            else:
                exp = None
            list_files = self.search(path, name, exp)
            if len(list_files) == 1:
                self.append_text('Файл находится в каталоге: ' + list_files[0])
            elif len(list_files) > 1:
                self.append_text('Найденных файлов несколько и находятся они в этих каталогах:\n' + '\n'.join(list_files))
            else:
                self.append_text('Не найдено ни одного файла по вашим параметрам')
            self.append_text('Готово!')
        if 'запусти файл' in sentence.lower():
            disk = self.showDialog('Введите путь, в котором лежит файл:')
            name = self.showDialog('Введите имя файла с расширением:')
            self.start_file(disk, name)
        if 'браузер' in sentence.lower():
            self.append_text('''У вас есть три варианта развития событий:
    - Введите поисковой запрос
    - Введите ссылку на сайт формата "https://site.com", на который вы хотите попасть
    - Ничего не писать и тогда просто запустится браузер''')
            url = self.showDialog('Введите ваш запрос описанный ранее или нажмите Enter для запуска браузера:')
            if url:
                if 'https://' not in url:
                    url = 'https://yandex.ru/search/?text=' + '%20'.join(url.split())
                os.popen('start {}'.format(url))
            else:
                os.popen('start https://yandex.ru')
            self.append_text('Готово!')
        if 'открой папку' in sentence.lower():
            url = self.showDialog('Введите путь до папки:')
            os.popen('explorer {}'.format(url))
            self.append_text('Готово!')
        if 'найди папку' in sentence.lower():
            path = self.showDialog('Введите путь откуда хотите начать поиск папки:')
            name_true = self.showDialog('Ищете ли вы папку по имени? ').lower()
            if name_true == 'да':
                name = self.showDialog('Укажите имя папки:')
            else:
                name = None
            list_files = self.search(path, name, None, search_dir=True)
            if len(list_files) == 1:
                self.append_text('Папка находится в каталоге:' + list_files[0])
            elif len(list_files) > 1:
                self.append_text('Найденных папок несколько и находятся они в этих каталогах:\n' + '\n'.join(list_files))
            else:
                self.append_text('Не найдено ни одной папки по вашим параметрам')
            self.append_text('Готово!')
        if 'выключи пк' in sentence.lower():
            sec = self.showDialog('Через сколько секунд выключить ПК?')
            os.popen('shutdown /s /t {}'.format(sec))
        if 'отмена выключения пк' in sentence.lower():
            os.popen('shutdown /a')
        if 'выход' in sentence.lower():
            self.append_text('До следующей встречи ;)')
            sys.exit()

    def hello(self):
        self.append_text('''Привет. Я Кира - бот-помощник.
Доступные команды на данный момент, если данные команды будут в вашем предложении, то тогда команда будет выполнена:
- Музыка:
    - Включи музыку - запустить музыку
    *Следующие команды не работают, пока вы не включите музыку*
    - Создай плейлист -  создание плейлиста из треков в указанной директории
    - Следующий трек - следующий трек
    - Предыдущий трек - предыдущий трек
    - Выключи музыку - выключить музыку
    - Убавь громкость - убавить музыку
    - Прибавь громкость - прибавить музыку
    - Установи громкость - установить громкость на какое-то значение
    - Перемешать треки - перемешать треки в плейлисте 
- Файлы:
    - Найди файлы - поиск файлов по вашим параметрам, которые вы указываете в процессе
    - Запусти файл - открывает файл *Оговорка, в названии файла не должно быть пробелов! Замените их на _*
    - Найди папку - поиск папок по вашим параметрам, которые вы указываете в процессе
    - Открой папку - открывает папку по вашему пути
- Выход в интернет:
    - Браузер - открывает браузер по вашим параметрам
- Выключи пк - выключение пк через какое-то время
- Отмена выключения пк - отмена отключения пк
- Выход - завершить сеанс со мной''')

    def ok(self):
        # Ловим команды
        self.string = self.get_text()
        # Проверяем команды
        kira.check_commands(self.string)
        # Повторяем, что написал юзер
        self.append_text('Вы написали: ' + self.string)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    kira = KIRA()
    kira.show()
    kira.hello()
    sys.exit(app.exec())
