import os
import sys
import random
import win32api
from PyQt5.QtWidgets import QApplication, QMainWindow, QInputDialog, QLabel, QWidget, QSystemTrayIcon, QAction, QMenu,\
    QStyle, QSlider
from PyQt5.QtMultimedia import QMediaPlaylist, QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
import requests


# Виджет для просмотра картинок
class MapViewer(QWidget):
    def __init__(self, address, parent=None):
        super().__init__(parent)

        self.image = self.get_map(address)

        # Инициализиреум картинку
        self.label = QLabel(self)
        pixmap = QPixmap(self.image)
        self.label.setPixmap(pixmap)
        # Настраиваем окно под картинку
        self.resize(pixmap.width(), pixmap.height())  # fit window to the image
        self.setWindowTitle('Ваша картинка')
        self.slider = QSlider(self)
        self.slider.setGeometry(0, 0, 22, pixmap.height())
        self.slider.setValue(100)
        self.slider.valueChanged[int].connect(self.changeValue)

    def changeValue(self, value):
        delta = value / 10000
        lower, upper = self.bbox.split('~')
        lower = str(float(lower.split(',')[0]) - delta) + ',' + str(float(lower.split(',')[1]) - delta)
        upper = str(float(upper.split(',')[0]) + delta) + ',' + str(float(upper.split(',')[1]) + delta)
        self.bbox = lower + '~' + upper
        request = "https://static-maps.yandex.ru/1.x/?bbox={}&l={}&ll={}&pt={},pm2ntl".format(self.bbox, self.l,
                                                                                              self.ll, self.ll)
        image = self.create_img(request, 'temp')
        pixmap = QPixmap(image)
        self.label.setPixmap(pixmap)

    # Функция показа карты по координатам
    def get_map(self, address):
        geocoder_request = "http://geocode-maps.yandex.ru/1.x/?geocode={}&format=json".format(address)
        answer = self.geocoder_request(geocoder_request)
        coors = answer[0].split()
        self.ll = coors[0] + ',' + coors[1]
        self.bbox = answer[1]
        self.l = 'map'
        request = "https://static-maps.yandex.ru/1.x/?bbox={}&l={}&ll={}&pt={},pm2ntl".format(self.bbox, self.l, self.ll, self.ll)
        if self.l == 'sat':
            image = self.create_img(request, 'temp', True)
        else:
            image = self.create_img(request, 'temp')
        return image

    def geocoder_request(self, request):
        response = None
        try:
            response = requests.get(request)
            if response:
                json_response = response.json()

                toponym = json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
                toponym_lower = toponym['boundedBy']['Envelope']['lowerCorner'].split()
                toponym_upper = toponym['boundedBy']['Envelope']['upperCorner'].split()
                boundedBy = toponym_lower[0] + ',' + toponym_lower[1] + '~' + toponym_upper[0] + ',' + \
                            toponym_upper[1]
                toponym_coordinates = toponym['Point']['pos']
            else:
                print("Ошибка выполнения запроса:")
                print(request)
                print('Http статус: ', response.status_code, "(", response.reason, ')')
        except:
            print('Запрос не удалось выполнить. Проверьте подключение к сети интернет.')
        return [toponym_coordinates, boundedBy]

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

    def closeEvent(self, event):
        os.remove(self.image)


class Player(QWidget):
    def __init__(self, playlist, playlist_copy, parent=None):
        super().__init__(parent)
        uic.loadUi('player.ui', self)

        # Устанавливаем начальное значение громкости музыки
        self.volume = 50
        # Создаем объект список для плейлиста, это нужно для перемешки треков в функции mix.
        # Является копией оригинального плейлиста
        self.playlist_list = playlist_copy
        # Создаем плейлист и плеер
        self.playlist = playlist
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)
        self.player = QMediaPlayer()
        # Задаем начальную громкость плееру
        self.player.setVolume(self.volume)
        self.player.setPlaylist(self.playlist)

        # self.slider.setFocusPolicy(Qt.NoFocus)
        self.slider.valueChanged[int].connect(self.changeValue)

        self.pushButton.clicked.connect(self.play_music)
        self.pushButton_2.clicked.connect(self.next)
        self.pushButton_3.clicked.connect(self.prev)
        self.pushButton_4.clicked.connect(self.mix)
        self.pushButton_5.clicked.connect(self.pause)

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

    def next(self):
        self.playlist.next()
        print(self.playlist.currentMedia().canonicalUrl())

    def prev(self):
        self.playlist.previous()
        print(self.playlist.currentMedia().canonicalUrl())

    def play_music(self):
        self.player.play()

    def changeValue(self, value):
        self.volume = value
        self.player.setVolume(self.volume)

    def closeEvent(self, event):
        self.playlist.clear()
        self.player.stop()

    def pause(self):
        self.player.pause()


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

        self.player_widget = QWidget()

        # Инициализируем QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))

        '''
            Объявим и добавим действия для работы с иконкой системного трея
            show - показать окно
            hide - скрыть окно
            exit - выход из программы
        '''
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        hide_action = QAction("Hide", self)
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

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
    def show_map(self):
        self.map_viewer = MapViewer(self.showDialog('Введите адрес или координаты (через запятую):'))
        self.map_viewer.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Кира бот-помощник",
            "Если что я в трее)",
            QSystemTrayIcon.Information,
            100
        )

    # Запуск музыки
    def play_music(self):
        playlist, playlist_list = self.create_playlist(self.showDialog('Введите название плейлиста:'))
        self.player_widget = Player(playlist, playlist_list)
        self.player_widget.show()

    # Функция создания плейлиста
    def create_playlist(self, name):
        playlist = QMediaPlaylist()
        playlist_list = []
        # Ловим название плейлиста и создаем путь
        path = 'data\\playlists\\'
        playlist_name = str(name) + '.txt'
        fullpath = path + playlist_name
        # Записываем данные с файла в список
        with open(fullpath, 'r') as PlayFile:
            playlist_txt = [line.strip() for line in PlayFile]
        for track in playlist_txt:
            url = QUrl.fromLocalFile(track)
            content = QMediaContent(url)
            # Добавляем треки в списочную копию плейлиста
            playlist_list.append(content)
            # Затем в сам плейлист
            playlist.addMedia(content)
        return playlist, playlist_list

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
        if '!команды' in sentence.lower():
            self.append_text('''Доступные команды на данный момент, если данные команды будут в вашем предложении, то тогда команда будет выполнена:
- Включи плеер - открывает плеер с музыкой
- Создай плейлист -  создание плейлиста из треков в указанной директории
- Браузер - открывает браузер по вашим параметрам
- Покажи карту - показывает карту по вашим параметрам
- Файлы:
    - Найди файлы - поиск файлов по вашим параметрам, которые вы указываете в процессе
    - Запусти файл - открывает файл *Оговорка, в названии файла не должно быть пробелов! Замените их на _*
    - Найди папку - поиск папок по вашим параметрам, которые вы указываете в процессе
    - Открой папку - открывает папку по вашему пути
- Выключи пк - выключение пк через какое-то время
- Переведи пк в режим гибернации - переход пк в режим гибернации
- Отмена выключения пк - отмена отключения пк
- Выход - завершить сеанс со мной''')
        if 'включи плеер' in sentence.lower() and not self.player_widget.isVisible():
            self.play_music()
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
            self.show_map()

    # Функция приветствия с пользователем
    def hello(self):
        self.append_text('Привет. Я Кира - бот-помощник. Чтобы посмотреть список команд напишите !команды')

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
