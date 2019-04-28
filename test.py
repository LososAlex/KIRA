import os
import sys
import random
import win32api
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QLabel, QWidget
from PyQt5.QtMultimedia import QMediaPlaylist, QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
import requests


# Виджет для просмотра картинок
class ImageViewer(QWidget):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        # Инициализиреум картинку
        label = QLabel(self)
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        # Удаляем картинку, если она временная
        if 'temp.' in image_path:
            os.remove(image_path)
        # Настраиваем окно под картинку
        self.resize(pixmap.width(), pixmap.height())  # fit window to the image
        self.setWindowTitle('Ваша картинка')


class KIRA(QMainWindow):
    def __init__(self):
        super().__init__()
        # Создаем переменную строки, но задаем ей значение None
        self.string = None
        # Загружаем GUI
        uic.loadUi('example.ui', self)
        # Настраиваем GUI
        self.pushButton.setText('Ответить')
        self.pushButton.clicked.connect(self.catch)
        # Устанавливаем начальное значение громкости музыки
        self.volume = 50
        # Создаем объект список для плейлиста, это нужно для перемешки треков в функции mix.
        # Является копией оригинального плейлиста
        self.playlist_list = []
        # Создаем плейлист и плеер
        self.playlist = QMediaPlaylist(self)
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.player = QMediaPlayer()
        self.player_on = False
        # Задаем начальную громкость плееру
        self.player.setVolume(self.volume)

    # Функция вывода текста, так называемый print
    def append_text(self, text):
        self.textEdit.append(text)

    # Функция доставания текста из строки, так называемый input
    def get_text(self):
        self.string = self.lineEdit.text()
        self.lineEdit.clear()
        self.append_text(self.string)
        return self.string

    # Показавыает диалоговое окно с вопросом, ответ на который возвращается
    def showDialog(self, question):
        text, ok = QInputDialog.getText(self, 'У меня есть вопрос', question)
        if ok:
            return str(text)

    # Открывает окно с картинкой
    def image(self, directory):
        self.image_viewer = ImageViewer(directory)
        self.image_viewer.show()

    # Функция показа карты по координатам
    def get_map(self):
        address = self.showDialog('Введите адрес или координаты (через запятую):').split(', ')
        if address[1].isdigit() and address[0].isdigit() and len(address) == 2:
            ll = address[1] + ',' + address[0]
        else:
            geocoder_request = "http://geocode-maps.yandex.ru/1.x/?geocode={}&format=json".format(', '.join(address))
            coors = self.geocoder_request(geocoder_request).split()
            ll = coors[0] + ',' + coors[1]
        z = self.showDialog('Задайте масштаб от 1 до 18')
        accept = self.showDialog('Показать карту со спутника?:')
        if accept.lower() == 'да':
            l = 'sat'
        else:
            l = 'map'
        request = "https://static-maps.yandex.ru/1.x/?z={}&l={}&ll={}&pt={},pm2ntl".format(z, l, ll, ll)
        if l == 'sat':
            image = self.create_img(request, 'temp', True)
        else:
            image = self.create_img(request, 'temp')
        self.image(image)

    def geocoder_request(self, request):
        response = None
        try:
            response = requests.get(request)
            if response:
                json_response = response.json()

                toponym = json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
                toponym_address = toponym['metaDataProperty']['GeocoderMetaData']['text']
                toponym_coordinates = toponym['Point']['pos']
            else:
                print("Ошибка выполнения запроса:")
                print(request)
                print('Http статус: ', response.status_code, "(", response.reason, ')')
        except:
            print('Запрос не удалось выполнить. Проверьте подключение к сети интернет.')
        return toponym_coordinates

    # Функция создания временной картинки карты
    def create_img(self, request, name, sat=False):
        response = None
        try:
            response = requests.get(request)

            if not response:
                print("Ошибка выполнения запроса:")
                print(request)
                print("Http статус:", response.status_code, "(", response.reason, ")")
                sys.exit(1)
        except:
            print("Запрос не удалось выполнить. Проверьте наличие сети Интернет.")
            sys.exit(1)

        # Запишем полученное изображение в файл.
        if sat:
            map_file = "{}.jpg".format(name)
        else:
            map_file = "{}.png".format(name)
        try:
            with open(map_file, "wb") as file:
                file.write(response.content)
        except IOError as ex:
            print("Ошибка записи временного файла:", ex)
            sys.exit(2)
        return map_file

    # Запуск музыки
    def play_music(self):
        # Если плейлист пустой, то спрашивает название и создает новый
        if self.playlist.isEmpty():
            self.create_playlist(self.showDialog('Введите название плейлиста:'))
            self.player.setPlaylist(self.playlist)
        self.player.play()

    # Функция создания плейлиста
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
            # Добавляем треки в списочную копию плейлиста
            self.playlist_list.append(content)
            # Затем в сам плейлист
            self.playlist.addMedia(content)

    # Функция перемешивания треков
    def mix(self):
        # Останавливаем плеер и очищаем плейлист
        self.player.stop()
        self.playlist.clear()
        # С помощью копии перемешиваем треки в сам плейлист
        playlist_copy = self.playlist_list
        for i in range(len(self.playlist_list)):
            track = random.choice(playlist_copy)
            del playlist_copy[playlist_copy.index(track)]
            self.playlist.addMedia(track)
        # Добавляем плейлист в плеер и запускаем плеер
        self.player.setPlaylist(self.playlist)
        self.player.play()

    # Функция создания плейлиста из папки в txt
    def playlist_from_dir_to_txt(self):
        # Спрашиваем путь к папке
        directory = self.showDialog('Введите путь к папке, где лежит музыка:')
        music = '\n'.join(self.search(directory, None, '.mp3'))
        # Спрашиваем, как пользователь хочет назвать плейлист
        name_playlist = self.showDialog('Введите название для этого плейлиста:')
        path = 'data\\playlists\\' + name_playlist + '.txt'
        # Записываем данные в файл
        with open(path, 'w', errors='ignore') as f:
            f.write(music)

    # Функция поиска папок или файлов
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
                for directory in dirs:
                    if name:
                        if name in directory:
                            list_files.append(os.path.join(root, directory))
                    else:
                        list_files.append(os.path.join(root, directory))
        return list_files

    # Функция запуска файлов
    def start_file(self, directory, name):
        name = name.split('.')
        name, exp = name
        exp = '.' + exp
        file = self.search(directory, name, exp)
        if len(file) == 1:
            os.popen('start {}'.format(str(file[0])))
            self.append_text('Готово!')
        elif len(file) > 1:
            self.append_text('Ошибка! Файлов по вашим параметрам оказалось несколько. Запуск невозможен')
        else:
            self.append_text('Ошибка! Файл не найден!')
    
    # Функция проверки запросов пользователя
    def check_commands(self, sentence):
        if 'включи музыку' in sentence.lower() and not self.player_on:
            self.play_music()
            self.player_on = True
        if self.player_on:
            if 'выключи музыку' in sentence.lower():
                self.player.stop()
                self.player_on = False
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
                self.append_text('Найденных файлов несколько и находятся они в этих каталогах:\n'
                                 + '\n'.join(list_files))
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
                self.append_text('Найденных папок несколько и находятся они в этих каталогах:\n'
                                 + '\n'.join(list_files))
            else:
                self.append_text('Не найдено ни одной папки по вашим параметрам')
            self.append_text('Готово!')
        if 'выключи пк' in sentence.lower():
            sec = self.showDialog('Через сколько секунд выключить ПК?')
            os.popen('shutdown /s /t {}'.format(sec))
        if 'переведи пк в режим гибернации' in sentence.lower():
            os.popen('shutdown /h')
        if 'отмена выключения пк' in sentence.lower():
            os.popen('shutdown /a')
        if 'выход' in sentence.lower():
            self.append_text('До следующей встречи ;)')
            sys.exit()
        if 'покажи карту' in sentence.lower():
            self.get_map()

    # Функция приветствия с пользователем
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
- Экспериментальные функции:
    - Покажи карту - показывает карту по вашим параметрам
- Выключи пк - выключение пк через какое-то время
- Переведи пк в режим гибернации - переход пк в режим гибернации
- Отмена выключения пк - отмена отключения пк
- Выход - завершить сеанс со мной''')

    # Функция ловли команды из строки
    def catch(self):
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
