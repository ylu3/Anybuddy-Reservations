import os.path
import sys
from datetime import date, timedelta, datetime

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QTimer
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit, QAction, QSystemTrayIcon, QMenu
from wxauto import WeChat

from check_reservations import send_request, format_response

wx = WeChat()

weekday_map = {
    "Monday": "星期一",
    "Tuesday": "星期二",
    "Wednesday": "星期三",
    "Thursday": "星期四",
    "Friday": "星期五",
    "Saturday": "星期六",
    "Sunday": "星期日",
}

class LogWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("羽毛球场地更新")
        self.resize(600, 400)
        self.text_area = QTextEdit(self)
        self.text_area.setReadOnly(True)
        self.setCentralWidget(self.text_area)

    @pyqtSlot(str)
    def append_log(self, message: str):
        self.text_area.append(message)

    def closeEvent(self, event):
        event.ignore()
        self.hide()

class Worker(QObject):
    log = pyqtSignal(str)

    def __init__(self, interval_sec=60, parent=None):
        super().__init__(parent)
        self.interval_sec = interval_sec
        self.timer = None
        self.last_result = ""
        self._running = False

    @pyqtSlot()
    def start(self):
        if self._running:
            return
        self._running = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reservation_once)
        self.timer.start(self.interval_sec * 1000)
        self.check_reservation_once()

    @pyqtSlot()
    def stop(self):
        self._running = False
        if self.timer:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None

    @staticmethod
    def formatted_msg(msg: str) -> str:
        return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"

    @pyqtSlot()
    def check_reservation_once(self):
        self.log.emit(self.formatted_msg("正在检查场地..."))
        today = date.today()

        self.log.emit(self.formatted_msg(f"今天是 {today}, {weekday_map[today.strftime('%A')]}"))
        next_saturday = today + timedelta((5 - today.weekday()) % 7)
        next_sunday = today + timedelta((6 - today.weekday()) % 7)

        self.log.emit(self.formatted_msg(f"下周六是 {next_saturday}, 正在检查..."))
        response_sat = send_request(next_saturday)
        res_sat = format_response(response_sat, next_saturday)
        self.log.emit(res_sat)

        self.log.emit(self.formatted_msg(f"下周日是 {next_sunday}, 正在检查..."))
        response_sun = send_request(next_sunday)
        res_sun = format_response(response_sun, next_sunday)
        self.log.emit(res_sun)
        body = (
            f"📅 羽毛球场地更新\n"
            f"—— 周六 ({next_saturday}) ——\n"
            f"{res_sat}\n"
            f"—— 周日 ({next_sunday}) ——\n"
            f"{res_sun}"
        )

        if response_sat.status_code != 200 or response_sun.status_code != 200:
            self.log.emit(self.formatted_msg("请求失败，跳过"))
        elif body != self.last_result:
            try:
                # 精确匹配群名，避免同名干扰
                wx.SendMsg(body, who="文件传输助手")
                self.log.emit(self.formatted_msg("有更新，已发送邮件"))
                self.last_result = body
            except Exception as e:
                self.log.emit(self.formatted_msg(f"发送邮件失败：{e}"))
        else:
            self.log.emit(self.formatted_msg("暂无更新"))

        self.log.emit("")

class TrayApp:
    def __init__(self, app):
        self.app = app
        self.window = LogWindow()
        icon_path = os.path.join(getattr(sys, "_MEIPASS", ""), "Anybuddy.ico") if hasattr(sys, '_MEIPASS') else "Anybuddy.ico"
        self.tray = QSystemTrayIcon(QIcon(icon_path), self.app)
        self.menu = QMenu(self.window)
        self.action_open = QAction("Open", self.window)
        self.action_exit = QAction("Exit", self.window)
        self.action_open.triggered.connect(self.show_window)
        self.action_exit.triggered.connect(self.exit_app)
        self.menu.addAction(self.action_open)
        self.menu.addAction(self.action_exit)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()
        self.window.show()
        self.thread = QThread(self.window)
        self.worker = Worker(interval_sec=60)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start)
        self.worker.log.connect(self.window.append_log)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def show_window(self):
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def exit_app(self):
        self.worker.stop()
        self.tray.hide()
        self.thread.quit()
        self.thread.wait(3000)
        self.app.quit()

if __name__ == "__main__":
    qApp = QApplication(sys.argv)
    tray_app = TrayApp(qApp)
    sys.exit(qApp.exec_())
