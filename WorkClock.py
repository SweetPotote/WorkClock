import os
import sys
from datetime import datetime
from PyQt6.QtCore import QSize, Qt, QCalendar, QDate, QSettings
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QCalendarWidget, QVBoxLayout, QLabel, \
    QWidget, QGridLayout, QLineEdit, QCheckBox, QTabWidget
from PyQt6.QtGui import QIcon, QAction
import ctypes
import sqlite3
import datetime
import yaml

# https://stackoverflow.com/questions/31836104/pyinstaller-and-onefile-how-to-include-an-image-in-the-exe-file
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS2
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def fetch_date(QDate):
    # connect an sqlite database
    connection = sqlite3.connect(resource_path("data/WorkClockdb.db"))
    cursor = connection.cursor()

    # Convert QDate to SQLite DATE format ISO8601 string : "YYYY-MM-DD HH:MM:SS.SSS"
    # Here, only the date is required, so the string should be : "YYY-MM-DD 00:00:00.000"

    _date = QDate.toString("yyyy-MM-dd") + " 00:00:00.000"

    # fetch all the table names
    cursor.execute("""
    SELECT * FROM DB_Calendar WHERE Date = "{}"
    """.format(_date))
    day = cursor.fetchone()

    connection.close()

    return day

def toHour(minutes):
    hour = int(int(minutes)/60)
    concat_minutes = int(minutes) - hour*60
    return "{}:{}".format(str(hour).zfill(1), str(concat_minutes).zfill(2))

def toMinutes(hour):
    hourArray = hour.split(":")
    hourArray[0] = hourArray[0].zfill(2)
    hourArray[1] = hourArray[1].zfill(2)
    return int(hourArray[0])*60 +int(hourArray[1])

def get_config():
    with open(resource_path("config.yaml"), "r") as file_object:
        config=yaml.load(file_object, Loader=yaml.SafeLoader)
    return config

def export_config(conf):
    with open(resource_path("config.yaml"),"w") as file_object:
        yaml.dump(conf, file_object)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(resource_path('WorkClock.py'))

        # ====================== SAVE Tab Layout =====================

        self.calendar = QCalendarWidget()
        self.calendar.selectionChanged.connect(self.changeLabel)

        self.modifiable = QCheckBox()
        self.modifiable.setText("Non modifiable")
        self.modifiable.setChecked(False)
        self.modifiable.setStyleSheet("QToggle{"
                            "qproperty-bg_color:#EEE;"
                            "qproperty-circle_color:#000;"
                            "qproperty-active_color:#128;"
                            "qproperty-disabled_color:#707;"
                            "qproperty-text_color:#FFF;}")
        self.modifiable.stateChanged.connect(self.editable_or_not)

        self.label_entry = QLabel("Heure d'arrivée")
        self.entry = QLineEdit()
        self.entry.setInputMask("99:99")
        self.entry.setReadOnly(True)

        self.label_exit = QLabel("Heure de sortie")
        self.exit = QLineEdit()
        self.exit.setInputMask("99:99")
        self.exit.setReadOnly(True)

        self.label_midday = QLabel("Pause midi")
        self.midday = QLineEdit()
        self.midday.setInputMask("9:99")
        self.midday.setReadOnly(True)

        self.label_afk = QLabel("Temps d'absence autre")
        self.afk = QLineEdit()
        self.afk.setInputMask("9:99")
        self.afk.setReadOnly(True)

        self.saveButton = QPushButton()
        self.saveButton.setText("Save")
        self.saveButton.setEnabled(False)
        self.saveButton.released.connect(self.save_to_sql)

        self.label_hour_worked = QLabel("Travail ce jour : ")

        lay_save = QGridLayout()

        lay_save.addWidget(self.calendar, 0, 0,11,1)
        lay_save.addWidget(self.label_entry, 1, 1)
        lay_save.addWidget(self.entry, 2,1)
        lay_save.addWidget(self.label_exit, 3, 1)
        lay_save.addWidget(self.exit, 4, 1)
        lay_save.addWidget(self.label_midday, 5, 1)
        lay_save.addWidget(self.midday, 6, 1)
        lay_save.addWidget(self.label_hour_worked, 10,1)
        lay_save.addWidget(self.modifiable, 0,1)
        lay_save.addWidget(self.saveButton, 9,1)
        lay_save.addWidget(self.label_afk,7,1)
        lay_save.addWidget(self.afk,8,1)

        # ====================== Tab Menuing =====================

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setMovable(False)

        widget_save = QWidget()
        widget_save.setLayout(lay_save)

        tabs.addTab(widget_save,"SAUVEGARDE")
        tabs.addTab(QPushButton("Press me"), "DEPENSE")

        # ======================= Menu Bar =========================

        change_work_week = QAction("Semaine", self)
        change_work_week.setStatusTip("Modifier la semaine de travail")
        change_work_week.triggered.connect(self.change_work_week)
        

        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        settings_menu = menu.addMenu("&Settings")
        settings_menu.addAction(change_work_week)

        # ====================== Init window =====================

        self.setWindowTitle("WorkClock")
        self.setWindowIcon(QIcon(resource_path("assets/clock.png")))

        self.setCentralWidget(tabs)

        self.changeLabel()

    def changeLabel(self):
        _day = fetch_date(self.calendar.selectedDate())
        if _day is not None :
            self.entry.setText(str(_day[1])[10:16])
            self.exit.setText(str(_day[2])[10:16])
            self.midday.setText(toHour(str(_day[3])))
            self.afk.setText(toHour(str(_day[4])))
            self.label_hour_worked.setText("Travail ce jour : {}".format(toHour(str(_day[5]))))
        else :
            self.entry.setText("00:00")
            self.exit.setText("00:00")
            self.midday.setText("0:00")
            self.afk.setText("0:00")
            self.label_hour_worked.setText("Travail ce jour : ")

    def editable_or_not(self):
        if self.modifiable.isChecked() :
            self.modifiable.setText("Modifiable")
            self.entry.setReadOnly(False)
            self.exit.setReadOnly(False)
            self.midday.setReadOnly(False)
            self.afk.setReadOnly(False)
            self.saveButton.setEnabled(True)
        else :
            self.modifiable.setText("Non modifiable")
            self.entry.setReadOnly(True)
            self.exit.setReadOnly(True)
            self.midday.setReadOnly(True)
            self.afk.setReadOnly(True)
            self.saveButton.setEnabled(False)
            self.changeLabel()

    def save_to_sql(self):
        _entry = self.entry.text()
        _exit = self.exit.text()
        _midday = toMinutes(self.midday.text())
        _afk = toMinutes(self.afk.text())
        _day = self.calendar.selectedDate().toString("yyyy-MM-dd")
        tot_work = toHour(toMinutes(_exit) - toMinutes(_entry) - _midday - _afk)


        # connect an sqlite database
        connection = sqlite3.connect(resource_path("data/WorkClockdb.db"))
        cursor = connection.cursor()

        now = str(datetime.datetime.now())[:-3]

        cursor.execute("""
            DELETE FROM DB_Calendar WHERE Date = "{}"
            """.format(_day + " 00:00:00.000"))

        connection.commit()


        cursor.execute("""
            INSERT INTO DB_Calendar (Date, Entrance, Exit, Midday, ExitMinutes, MinutesWorked, LastModified)
            VALUES ("{}", "{}", "{}", {}, {}, {}, "{}")
            """.format(_day + " 00:00:00.000", _day + " " + _entry + ":00.000", _day + " " + _exit +":00.000",
                       _midday, _afk, toMinutes(tot_work), now))

        connection.commit()
        connection.close()

        self.changeLabel()

    def change_work_week(self):
        print("il faut faire quelque chose")
        # w = SettingsWindow()
        # w.show()

# class SettingsWindow(QWidget):
#     """
#         This "window" is a QWidget. If it has no parent, it
#         will appear as a free-floating window as we want.
#         """
#
#     def __init__(self):
#         super().__init__()
#         layout = QVBoxLayout()
#         self.label = QLabel("Another Window")
#         layout.addWidget(self.label)
#         widget = QWidget()
#         widget.setLayout(layout)
#         self.setCentralWidget(widget)

app = QApplication(sys.argv)
app.setStyle("fusion")

CONF = get_config()

window = MainWindow()
window.show()

app.exec()
