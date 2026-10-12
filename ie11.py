"""
Internet Explorer 11 — Nostalgia Edition (full version)
A fan-made browser with the classic IE11 desktop UI, using the Evergreen
Microsoft Edge WebView2 runtime via QtWebView2.

Install:
    py -m pip install -r requirements.txt

Run:
    py ie11.py

The Microsoft Edge WebView2 Evergreen Runtime must be installed.  It updates
independently through Microsoft so this app automatically uses its current
Chromium engine; it does not ship or emulate the retired IE11 engine.

Optional: place ie11.ico (or ie11.png) next to this file to use it as the app icon.
"""
import sys
import os
import json
import threading
import wave
import math
import base64
import ctypes
from urllib.parse import quote_plus, urlsplit
from urllib.request import urlopen
import http.client
import queue

from PyQt5.QtCore import (Qt, QUrl, QPoint, QPointF, QRect, QRectF, QSize, QTimer, QEvent,
                          QObject, pyqtSignal, QStandardPaths)
from PyQt5.QtGui import (QKeySequence, QFont, QColor, QBrush, QIcon, QPainter,
                         QPen, QPixmap, QPolygonF, QDesktopServices, QDrag, QCursor, QFontMetrics)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QToolButton, QMenu, QAction, QLabel,
    QTabBar, QTabWidget, QStackedWidget, QStatusBar, QProgressBar, QMessageBox,
    QInputDialog, QDialog, QShortcut, QListWidget, QListWidgetItem, QFrame,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QMenuBar, QHeaderView, QDialogButtonBox, QSplashScreen, QComboBox)
from qtwebview2 import QtWebViewWidget, PageLoadEvent, NewWindowResponse
try:
    from PyQt5.QtMultimedia import QSoundEffect
except Exception:
    QSoundEffect = None

HOME_URL = "https://msn.com"
BING_SEARCH_URL = "https://www.bing.com/search?q="
SUGGEST_URL = "https://api.bing.com/osjson.aspx?query="
_s = urlsplit(SUGGEST_URL)
_BING_SUGGEST_HOST = _s.netloc
_BING_SUGGEST_PATH = _s.path + ("?" + _s.query if _s.query else "")
NEW_TAB_URL = "ie11://newtab"


def _dpapi_protect(value):
    """Encrypt text for the current Windows account without a new dependency."""
    if not sys.platform.startswith("win"):
        raise OSError("The password vault requires Windows.")
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_byte))]
    raw = value.encode("utf-8"); source = (ctypes.c_byte * len(raw)).from_buffer_copy(raw); out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(ctypes.byref(DATA_BLOB(len(raw), source)), "IE11 Nostalgia password vault", None, None, None, 0, ctypes.byref(out)):
        raise ctypes.WinError()
    try: return base64.b64encode(ctypes.string_at(out.pbData, out.cbData)).decode("ascii")
    finally: ctypes.windll.kernel32.LocalFree(out.pbData)


def _dpapi_unprotect(value):
    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_byte))]
    raw = base64.b64decode(value); source = (ctypes.c_byte * len(raw)).from_buffer_copy(raw); out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(DATA_BLOB(len(raw), source)), None, None, None, None, 0, ctypes.byref(out)):
        raise ctypes.WinError()
    try: return ctypes.string_at(out.pbData, out.cbData).decode("utf-8")
    finally: ctypes.windll.kernel32.LocalFree(out.pbData)


def build_new_tab_html(dark_mode=True):
    """MSN-inspired new tab page. Optional: place ie11_logo.png next to this file."""
    if dark_mode:
        bg, panel, text, muted, border = "#101923", "#1c2937", "#f4f8fc", "#a8bacb", "#34475a"
        card, hover = "#223345", "#304a61"
    else:
        bg, panel, text, muted, border = "#eef4f9", "#ffffff", "#172536", "#5b6c7c", "#d1dde7"
        card, hover = "#ffffff", "#e3eff9"
    html = r'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Internet Explorer 11</title><style>
*{box-sizing:border-box}body{margin:0;background:@BG@;color:@TEXT@;font:16px "Segoe UI",Arial,sans-serif;min-height:100vh}
.top{height:56px;display:flex;align-items:center;justify-content:space-between;padding:0 28px;border-bottom:1px solid @BORDER@;background:@PANEL@}
.brand{display:flex;align-items:center;gap:12px;font-size:15px;font-weight:650}
.logo{width:34px;height:34px;border-radius:10px;overflow:hidden;display:grid;place-items:center;background:linear-gradient(135deg,#00a4ef,#0078d4 55%,#5c2d91);color:#fff;font-size:20px;font-weight:800}
.logo img{width:100%;height:100%;object-fit:contain}.topnote{font-size:12px;color:@MUTED@}
main{max-width:1020px;margin:0 auto;padding:clamp(48px,9vh,105px) 24px 48px;text-align:center}
.eyebrow{color:#32a9f4;text-transform:uppercase;letter-spacing:2.6px;font-size:11px;font-weight:750}
h1{font-size:clamp(28px,4vw,44px);line-height:1.15;letter-spacing:-1px;margin:14px 0 12px}
.sub{color:@MUTED@;margin:0 0 30px;font-size:15px}
.search{display:flex;gap:10px;max-width:680px;margin:0 auto 52px;padding:7px;border:1px solid @BORDER@;background:@PANEL@;border-radius:14px;box-shadow:0 12px 38px #00000018}
.search input{flex:1;min-width:0;background:transparent;color:@TEXT@;border:0;outline:0;padding:0 15px;font-size:16px}
.search input::placeholder{color:@MUTED@}
.search button{border:0;border-radius:9px;padding:13px 22px;background:#087bd1;color:#fff;font-size:14px;font-weight:700;cursor:pointer}
.search button:hover{background:#1597ee}
.section-head{display:flex;justify-content:space-between;align-items:center;margin:0 0 16px}
.section-head h2{font-size:15px;margin:0}.section-head span{font-size:12px;color:@MUTED@}
.tiles{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:14px}
.tile{display:flex;min-height:118px;flex-direction:column;align-items:center;justify-content:center;gap:12px;text-decoration:none;color:@TEXT@;background:@CARD@;border:1px solid @BORDER@;border-radius:13px;transition:transform .16s,background .16s}
.tile:hover{background:@HOVER@;border-color:#168fe0;transform:translateY(-3px)}
.tile-icon{width:42px;height:42px;border-radius:13px;display:grid;place-items:center;background:#087bd122;color:#39aaff;font-size:21px;font-weight:750}
.tile-label{font-size:12px;font-weight:600}
.footer{text-align:center;color:@MUTED@;font-size:11px;margin-top:45px}.footer strong{color:@TEXT@}
@media(max-width:700px){.tiles{grid-template-columns:repeat(3,minmax(0,1fr))}.topnote{display:none}}
</style></head><body>
<header class="top"><div class="brand"><div class="logo"><img src="ie11_logo.png" alt="" onerror="this.parentElement.textContent='IE'"></div><span>Internet Explorer 11</span></div><div class="topnote">Your browser, your starting point</div></header>
<main><div class="eyebrow">Nostalgia Edition</div><h1>Where would you like to go?</h1>
<p class="sub">A familiar starting page, powered by Chromium.</p>
<form class="search" id="searchForm"><input id="q" autocomplete="off" autofocus placeholder="Search the web with Bing or enter an address…"><button type="submit">Search&nbsp;↗</button></form>
<div class="section-head"><h2>Quick links</h2><span>Your favorite places on the web</span></div>
<div class="tiles">
<a class="tile" href="https://www.msn.com/"><span class="tile-icon">M</span><span class="tile-label">MSN</span></a>
<a class="tile" href="https://www.bing.com/"><span class="tile-icon">⌕</span><span class="tile-label">Bing</span></a>
<a class="tile" href="https://www.youtube.com/"><span class="tile-icon">▶</span><span class="tile-label">YouTube</span></a>
<a class="tile" href="https://www.roblox.com/"><span class="tile-icon">◇</span><span class="tile-label">Roblox</span></a>
<a class="tile" href="https://www.minecraft.net/"><span class="tile-icon">▦</span><span class="tile-label">Minecraft</span></a>
<a class="tile" href="https://www.google.com/"><span class="tile-icon">G</span><span class="tile-label">Google</span></a>
</div>
<div class="footer"><strong>Internet Explorer 11</strong> &nbsp;·&nbsp; A fan-made browser start page</div></main>
<script>document.getElementById('searchForm').addEventListener('submit',function(e){e.preventDefault();var q=document.getElementById('q').value.trim();if(q)location.href='https://www.bing.com/search?q='+encodeURIComponent(q)});</script>
</body></html>'''
    for token, value in (("@BG@", bg), ("@PANEL@", panel), ("@TEXT@", text),
                         ("@MUTED@", muted), ("@BORDER@", border),
                         ("@CARD@", card), ("@HOVER@", hover)):
        html = html.replace(token, value)
    return html


def build_ie_icon():
    """Fallback: draw a nostalgic blue 'e' with a yellow swoosh."""
    pm = QPixmap(32, 32)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor("#F8B62D"), 3))
    p.setBrush(Qt.NoBrush)
    p.drawArc(0, 7, 32, 20, 30 * 16, 300 * 16)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#0A72B8"))
    p.drawEllipse(3, 3, 26, 26)
    p.setPen(QColor("white"))
    p.setFont(QFont("Georgia", 15, QFont.Bold))
    p.drawText(pm.rect().adjusted(0, -1, 0, -1), Qt.AlignCenter, "e")
    p.end()
    return QIcon(pm)


def find_resource(name):
    """Find a data file both when running as a script and when bundled
    with PyInstaller (--add-data puts files into sys._MEIPASS)."""
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, name))
        candidates.append(os.path.join(meipass, "images", name))
    base = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(base, name))
    candidates.append(os.path.join(base, "images", name))
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


# Display sizes of the nav buttons. Change these two numbers to resize;
# the PNGs are scaled (smoothly) to fit these squares.
BACK_BUTTON_SIZE = 50
FORWARD_BUTTON_SIZE = 30

NAV_IMAGE_FILES = {
    "back": ("back.png", "back_blue.png", "arrow_left_blue.png"),
    "back_gray": ("back_gray.png", "back_disabled.png", "arrow_left_gray.png"),
    "forward": ("forward.png", "forward_blue.png", "arrow_right_blue.png"),
    "forward_gray": ("forward_gray.png", "forward_disabled.png", "arrow_right_gray.png"),
}


def load_nav_pixmaps():
    """Load the four nav PNGs; returns a dict of pixmaps, or None if any
    is missing (the buttons then fall back to drawn glossy orbs)."""
    pixmaps = {}
    for key, aliases in NAV_IMAGE_FILES.items():
        pm = None
        for name in aliases:
            path = find_resource(name)
            if path:
                loaded = QPixmap(path)
                if not loaded.isNull():
                    pm = loaded
                    break
        if pm is None:
            return None
        pixmaps[key] = pm
    return pixmaps


def scale_nav_pixmap(pixmap, size):
    return pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def make_fallback_nav_pixmap(size, direction, enabled):
    """Draw a glossy circular arrow so the nav buttons still work if the
    PNG files are missing."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#1E86D6") if enabled else QColor("#D8D8D8"))
    p.setPen(QPen(QColor("#13639F") if enabled else QColor("#C2C2C2"), max(1, size // 22)))
    p.drawEllipse(1, 1, size - 2, size - 2)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("white"))
    p.save()
    p.translate(size / 2.0, size / 2.0)
    if direction == "left":
        p.scale(-1.0, 1.0)
    s = size / 2.0
    shaft_h = size * 0.20
    p.drawRect(QRectF(-s * 0.85, -shaft_h / 2.0, s * 0.85, shaft_h))
    head = QPolygonF([QPointF(-s * 0.05, -s * 0.55),
                      QPointF(s * 0.75, 0.0),
                      QPointF(-s * 0.05, s * 0.55)])
    p.drawPolygon(head)
    p.restore()
    p.end()
    return pm


def load_ie_icon():
    """Use ie11.ico (or ie11.png/svg) bundled with the app or next to the
    script; draw a fallback icon if absent."""
    for name in ("ie11.ico", "ie11.png", "ie11.svg"):
        path = find_resource(name)
        if path:
            icon = QIcon(path)
            if not icon.isNull() and not icon.pixmap(16, 16).isNull():
                return icon
    return build_ie_icon()


def load_newtab_icon():
    """Load newtab.png if present; returns QIcon or None."""
    for name in ("newtab.png", "new_tab.png"):
        path = find_resource(name)
        if path:
            icon = QIcon(path)
            if not icon.isNull() and not icon.pixmap(16, 16).isNull():
                return icon
    return None


def build_error_html(url, detail=""):
    """The deliberately plain, old IE connection failure document."""
    safe_url = (url or "").replace("&", "&amp;").replace("<", "&lt;")
    return '''<!doctype html><html><head><meta charset="utf-8"><title>Internet Explorer cannot display the webpage</title>
<style>body{margin:58px auto;max-width:760px;color:#222;background:#fff;font:14px "Segoe UI",Arial,sans-serif}.crest{color:#1479bd;font:34px Georgia,serif;font-weight:bold;letter-spacing:-1px;margin-bottom:28px}.crest:first-letter{font-style:italic}h1{font-size:24px;font-weight:normal;margin:0 0 24px}p{line-height:1.55}.url{color:#666;margin:20px 0}.link{display:block;color:#0645ad;text-decoration:none;font-size:15px;margin:16px 0;padding-left:22px}.link:before{content:'›';font-size:24px;vertical-align:-2px;margin-right:8px;color:#1685c5}button{font:13px "Segoe UI";padding:4px 20px}</style></head><body>
<div class="crest">e</div><h1>Internet Explorer cannot display the webpage</h1>
<p>• Make sure your web browser settings are correct and that you are connected to the Internet.</p>
<p class="url">''' + safe_url + '''</p><button onclick="location.href='ie11-error:refresh'">Refresh</button>
<a class="link" href="ie11-error:diagnose">Diagnose Connection Problems</a>
<a class="link" href="ie11-error:more">More information</a></body></html>'''


class InfoBar(QFrame):
    """One compact, reusable IE-style notification bar."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("InfoBar")
        self.setVisible(False)
        self.setFixedHeight(34)
        self._menu = QMenu(self)
        row = QHBoxLayout(self); row.setContentsMargins(9, 2, 5, 2); row.setSpacing(7)
        self.icon = QLabel("ⓘ"); self.icon.setStyleSheet("font-size:16px;color:#316fa3")
        self.message = QLabel(); self.message.setTextFormat(Qt.PlainText)
        self.actions = QHBoxLayout(); self.actions.setSpacing(4)
        self.options = QToolButton(); self.options.setText("Options ▾"); self.options.setPopupMode(QToolButton.InstantPopup); self.options.setMenu(self._menu)
        self.close = QToolButton(); self.close.setText("✕"); self.close.setToolTip("Close notification"); self.close.clicked.connect(self.hide)
        row.addWidget(self.icon); row.addWidget(self.message, 1); row.addLayout(self.actions); row.addWidget(self.options); row.addWidget(self.close)
        self.apply_theme(False)
    def apply_theme(self, dark):
        colors = ("#3b3423", "#5d5133", "#fff1bd", "#e5c365") if dark else ("#222", "#fff4ce", "#fff4ce", "#e5c365")
        self.setStyleSheet("QFrame#InfoBar{background:%s;border-top:1px solid %s;border-bottom:1px solid %s;color:%s}QToolButton{border:1px solid #b7a870;background:transparent;padding:2px 7px}QToolButton:hover{background:#ffe9a4}" % (colors[1], colors[3], colors[3], colors[0]))
    def show_message(self, text, buttons=(), options=()):
        self.message.setText(text)
        while self.actions.count():
            item = self.actions.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._menu.clear()
        for label, callback in buttons:
            btn = QPushButton(label); btn.clicked.connect(callback); self.actions.addWidget(btn)
        for label, callback in options:
            act = self._menu.addAction(label); act.triggered.connect(callback)
        self.options.setVisible(bool(options))
        self.show()


class DraggableFavicon(QLabel):
    def __init__(self, browser):
        super().__init__("🌐", browser); self.browser = browser; self._start = None
    def mousePressEvent(self, event):
        self._start = event.pos(); super().mousePressEvent(event)
    def mouseMoveEvent(self, event):
        if not self._start or (event.pos() - self._start).manhattanLength() < 6: return
        tab = self.browser.current_tab()
        if not tab: return
        drag = QDrag(self); mime = __import__('PyQt5.QtCore', fromlist=['QMimeData']).QMimeData()
        mime.setText((tab.view.title() or tab.view.url().toString()) + "\n" + tab.view.url().toString())
        drag.setMimeData(mime); drag.exec_(Qt.MoveAction)


class FavoritesBar(QWidget):
    def __init__(self, browser):
        super().__init__(); self.browser = browser; self.setAcceptDrops(True)
    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.acceptProposedAction()
    def dropEvent(self, event):
        parts = event.mimeData().text().split("\n", 1)
        if len(parts) == 2 and parts[1].startswith(("http://", "https://")):
            self.browser.add_favorite_direct(parts[0], parts[1]); event.acceptProposedAction()


class QuickTabsDialog(QDialog):
    def __init__(self, browser):
        super().__init__(browser); self.browser=browser; self.setWindowTitle("Quick Tabs"); self.setWindowIcon(browser.windowIcon()); self.resize(680, 380)
        v=QVBoxLayout(self); v.addWidget(QLabel("Open tabs")); self.list=QListWidget(self); v.addWidget(self.list)
        buttons=QDialogButtonBox(QDialogButtonBox.Close); switch=buttons.addButton("Switch to", QDialogButtonBox.AcceptRole); v.addWidget(buttons)
        for i in range(browser.stack.count()):
            tab=browser.stack.widget(i); item=QListWidgetItem("%s\n%s" % (tab.view.title() or "New tab", tab.view.url().toString())); item.setData(Qt.UserRole,i); self.list.addItem(item)
        self.list.setCurrentRow(browser.tabbar.currentIndex()); self.list.itemDoubleClicked.connect(self.switch); switch.clicked.connect(self.switch); buttons.rejected.connect(self.reject)
    def switch(self, *_):
        item=self.list.currentItem()
        if item: self.browser.tabbar.setCurrentIndex(item.data(Qt.UserRole)); self.accept()


class NavImageButton(QToolButton):
    """Navigation button that shows a custom PNG normally and a gray PNG
    when disabled. Sizes itself exactly to the scaled pixmap."""
    def __init__(self, enabled_pixmap, disabled_pixmap, tooltip, parent=None):
        super().__init__(parent)
        self.setObjectName("NavImageButton")
        icon = QIcon()
        icon.addPixmap(enabled_pixmap, QIcon.Normal)
        icon.addPixmap(enabled_pixmap, QIcon.Active)
        icon.addPixmap(enabled_pixmap, QIcon.Selected)
        icon.addPixmap(disabled_pixmap, QIcon.Disabled)
        self.setIcon(icon)
        self.setIconSize(enabled_pixmap.size())
        self.setFixedSize(enabled_pixmap.size())
        self.setToolTip(tooltip)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "QToolButton{border:none;background:transparent;padding:0;margin:0;}")


LIGHT_QSS = """
QMainWindow, QWidget { background:#F0F0F0; color:#1A1A1A;
    font-family:"Segoe UI",sans-serif; font-size:12px; }
QWidget#ToolbarContainer { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
    stop:0 #F7F7F7, stop:1 #EAEAEA); border-bottom:1px solid #D6D6D6; }
QWidget#TabStrip { background:transparent; }
QWidget#AddressRow { background:transparent; }
QWidget#FavoritesBar { background:#F4F4F4; border-bottom:1px solid #D9D9D9; }
QWidget#FavoritesCenter { background:#F6F6F6; border-right:1px solid #D0D0D0; }

QToolButton#BackButton { border:1px solid #13639F; border-radius:22px;
    color:#FFFFFF; font-size:24px; font-weight:bold;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #5FB2EE, stop:0.5 #1E86D6, stop:1 #156CB0); }
QToolButton#BackButton:enabled:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #74C1F6, stop:0.5 #2C96E4, stop:1 #1B7CC6); }
QToolButton#BackButton:enabled:pressed {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #1568AC, stop:1 #1E86D6); }
QToolButton#BackButton:disabled { border:1px solid #C6C6C6; color:#A6A6A6;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #EFEFEF, stop:1 #DEDEDE); }
QToolButton#ForwardButton { border:1px solid #13639F; border-radius:13px;
    color:#FFFFFF; font-size:12px; font-weight:bold;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #5FB2EE, stop:0.5 #1E86D6, stop:1 #156CB0); }
QToolButton#ForwardButton:enabled:hover {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #74C1F6, stop:0.5 #2C96E4, stop:1 #1B7CC6); }
QToolButton#ForwardButton:disabled { border:1px solid #C6C6C6; color:#A6A6A6;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #EFEFEF, stop:1 #DEDEDE); }
QToolButton#NavDrop { background:transparent; border:none; color:#666;
    font-size:9px; }
QToolButton#NavDrop:hover:enabled { background:#E3F0FB; color:#000; }
QToolButton#NavDrop:disabled { color:#BBBBBB; }

QToolButton#CommandButton { background:transparent; border:1px solid transparent;
    border-radius:2px; color:#3B3B3B; padding:1px 6px; font-size:15px; }
QToolButton#CommandButton:hover:enabled { background:#E3F0FB; border-color:#A9CFEE; color:#000; }
QToolButton#CommandButton:pressed:enabled { background:#D0E5F7; border-color:#8FBCE3; }
QToolButton#CommandButton:disabled { color:#9A9A9A; }
QToolButton#CommandButton::menu-indicator { image:none; }
QToolButton#FavBarLink { background:transparent; border:1px solid transparent;
    padding:2px 8px; color:#1A1A1A; font-size:12px; }
QToolButton#FavBarLink:hover:enabled { background:#E6F2FA; border-color:#AED0EA; }
QToolButton#FavBarLink::menu-indicator { image:none; }

QFrame#AddressFrame { background:#FFFFFF; border:1px solid #9A9A9A; border-radius:2px; }
QFrame#AddressFrame[focus="true"] { border:1px solid #3C7FB1; }
QLineEdit#AddressBar { background:transparent; border:none; color:#111;
    font-size:13px; padding:0 2px; selection-background-color:#3399FF; }
QToolButton#AddressDrop { background:transparent; border:none; color:#555;
    font-size:10px; width:16px; }
QToolButton#AddressDrop:hover:enabled { background:#DCEBF9; }
QLineEdit#SearchBar { background:#FFFFFF; border:1px solid #ABADB3;
    border-radius:2px; padding:3px 8px; font-size:12px; }
QLineEdit#SearchBar:focus { border:1px solid #3C7FB1; }

QTabBar { background:transparent; font-size:12px; }
QTabBar::tab { background:#E6E6E6; color:#3A3A3A; border:1px solid #C9C9C9;
    border-radius:3px; padding:5px 12px 4px 12px; margin-right:3px;
    min-width:100px; }
QTabBar::tab:selected { background:#FFFFFF; color:#000; border-color:#B8B8B8; }
QTabBar::tab:hover:!selected { background:#F1F1F1; }
QStackedWidget { background:#FFFFFF; }

QStatusBar { background:#F0F0F0; border-top:1px solid #D8D8D8; color:#333; }
QStatusBar::item { border:none; }
QStatusBar QLabel { padding:0 6px; color:#333; }
QPushButton#ZoomButton { background:transparent; border:1px solid transparent;
    border-radius:2px; padding:1px 8px; color:#333; }
QPushButton#ZoomButton:hover:enabled { background:#E3F0FB; border-color:#A9CFEE; }

QMenu { background:#FAFAFA; color:#1A1A1A; border:1px solid #9A9A9A; padding:2px; }
QMenu::item { padding:5px 28px 5px 20px; }
QMenu::item:selected:enabled { background:#CDE6F7; color:#000; }
QMenu::item:disabled { color:#9A9A9A; }
QMenu::separator { height:1px; background:#DCDCDC; margin:3px 6px; }
QMenuBar { background:#F0F0F0; }
QMenuBar::item { padding:4px 10px; background:transparent; }
QMenuBar::item:selected { background:#CDE6F7; }

QLineEdit { background:#FFFFFF; border:1px solid #ABADB3; padding:3px 5px;
    color:#111; selection-background-color:#3399FF; }
QListWidget { background:#FFFFFF; color:#1A1A1A; border:1px solid #B4B4B4; outline:0; }
QListWidget::item { padding:5px 6px; }
QListWidget::item:selected { background:#CDE6F7; color:#000; }
QTreeWidget { background:#FFFFFF; color:#1A1A1A; border:1px solid #B4B4B4; outline:0; }
QTreeWidget::item:selected { background:#CDE6F7; color:#000; }
QHeaderView::section { background:#F4F4F4; color:#333; border:1px solid #D0D0D0;
    border-top:none; padding:3px 8px; }
QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
    stop:0 #FCFCFC, stop:1 #EDEDED); border:1px solid #ADADAD;
    border-radius:2px; padding:4px 14px; color:#1A1A1A; }
QPushButton:hover:enabled { border-color:#3C7FB1; }
QPushButton:pressed { background:#DCEBF9; }
QProgressBar { background:#FFFFFF; border:1px solid #B4B4B4; height:9px; max-height:9px; }
QProgressBar::chunk { background:#1D82D2; }
QToolTip { background:#FFFFE1; color:#000; border:1px solid #767676; padding:2px; }
"""

DARK_QSS = """
QMainWindow, QWidget { background:#1F1F1F; color:#E8E8E8;
    font-family:"Segoe UI",sans-serif; font-size:12px; }
QWidget#ToolbarContainer { background:#242424; border-bottom:1px solid #181818; }
QWidget#TabStrip { background:transparent; }
QWidget#AddressRow { background:transparent; }
QWidget#FavoritesBar { background:#242424; border-bottom:1px solid #181818; }
QWidget#FavoritesCenter { background:#232323; border-right:1px solid #181818; }
QToolButton#BackButton { border:1px solid #0A5C8F; border-radius:22px;
    color:white; font-size:24px; font-weight:bold;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1D82D2, stop:1 #1568AC); }
QToolButton#BackButton:disabled { border:1px solid #3A3A3A; color:#777; background:#2A2A2A; }
QToolButton#ForwardButton { border:1px solid #0A5C8F; border-radius:13px;
    color:white; font-size:12px; font-weight:bold;
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #1D82D2, stop:1 #1568AC); }
QToolButton#ForwardButton:disabled { border:1px solid #3A3A3A; color:#777; background:#2A2A2A; }
QToolButton#NavDrop { background:transparent; border:none; color:#AAA; font-size:9px; }
QToolButton#NavDrop:hover:enabled { background:#3D3D3D; color:#FFF; }
QToolButton#NavDrop:disabled { color:#666; }
QToolButton#CommandButton { background:transparent; color:#CCCCCC;
    border:1px solid transparent; border-radius:3px; padding:1px 6px; font-size:15px; }
QToolButton#CommandButton:hover:enabled { background:#3D3D3D; color:#FFF; border-color:#505050; }
QToolButton#CommandButton:disabled { color:#6A6A6A; }
QToolButton#CommandButton::menu-indicator { image:none; }
QToolButton#FavBarLink { background:transparent; border:1px solid transparent;
    padding:2px 8px; color:#CCC; font-size:12px; }
QToolButton#FavBarLink:hover:enabled { background:#3D3D3D; color:#FFF; }
QFrame#AddressFrame { background:#000; border:1px solid #3F3F3F; border-radius:2px; }
QFrame#AddressFrame[focus="true"] { border:1px solid #0078D7; }
QLineEdit#AddressBar { background:transparent; border:none; color:#FFF; font-size:13px; }
QToolButton#AddressDrop { background:transparent; border:none; color:#AAA;
    font-size:10px; width:16px; }
QLineEdit#SearchBar { background:#000; border:1px solid #3F3F3F; color:#FFF;
    border-radius:2px; padding:3px 8px; font-size:12px; }
QLineEdit#SearchBar:focus { border:1px solid #0078D7; }
QTabBar { background:transparent; font-size:12px; }
QTabBar::tab { background:#292929; color:#D5D5D5; border:1px solid #383838;
    border-radius:3px; padding:5px 12px 4px 12px; margin-right:3px;
    min-width:100px; }
QTabBar::tab:selected { background:#1F1F1F; color:#FFF; }
QTabBar::tab:hover:!selected { background:#353535; }
QStackedWidget { background:#1F1F1F; }
QStatusBar { background:#242424; color:#BDBDBD; border-top:1px solid #181818; }
QStatusBar::item { border:none; }
QPushButton#ZoomButton { background:transparent; border:1px solid transparent;
    color:#BDBDBD; padding:1px 8px; }
QPushButton#ZoomButton:hover:enabled { background:#3D3D3D; }
QMenu { background:#16191E; color:#F0F0F0; border:1px solid #2A2E34; padding:2px; }
QMenu::item { padding:5px 28px 5px 20px; }
QMenu::item:selected:enabled { background:#232A33; color:#FFF; }
QMenu::item:disabled { color:#6A6A6A; }
QMenu::separator { height:1px; background:#2D333C; margin:3px 6px; }
QMenuBar { background:#242424; }
QMenuBar::item { padding:4px 10px; }
QMenuBar::item:selected { background:#3D3D3D; }
QLineEdit { background:#000; color:#FFF; border:1px solid #3F3F3F; padding:3px 5px; }
QListWidget, QTreeWidget { background:#171A1F; color:#E8E8E8; border:1px solid #2A2E34; }
QListWidget::item:selected, QTreeWidget::item:selected { background:#1689D5; color:#FFF; }
QHeaderView::section { background:#242424; color:#CCC; border:1px solid #343434;
    border-top:none; padding:3px 8px; }
QPushButton { background:#333; color:#E8E8E8; border:1px solid #4A4A4A;
    border-radius:2px; padding:4px 14px; }
QPushButton:hover:enabled { background:#3D3D3D; border-color:#5A5A5A; }
QProgressBar { background:#171717; border:1px solid #343434; height:9px; max-height:9px; }
QProgressBar::chunk { background:#0078D7; }
QToolTip { background:#2B2B2B; color:#EEE; border:1px solid #555; padding:2px; }
"""

# The title row deliberately shares this same paint with the toolbar stack: no
# per-row borders means the chrome reads as one continuous Aero-inspired object.
CHROME_LIGHT_QSS = """
QWidget#ToolbarContainer { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #F7F9FB,stop:.52 #F1F5F8,stop:1 #E9EEF3); border:none; border-bottom:1px solid #C9D1D8; border-top-left-radius:8px; border-top-right-radius:8px; }
QWidget#TitleBar, QWidget#AddressRow, QWidget#TabStrip, QWidget#FavoritesBar { background:transparent; border:none; }
QWidget#ToolbarContainer[maximized="true"] { border-top-left-radius:0; border-top-right-radius:0; } QWidget#TitleBar { border-top:1px solid rgba(255,255,255,90); }
QLabel#ChromeTitle { color:#1A1A1A; font-size:12px; }
QToolButton#CaptionButton { border:0; border-radius:0; background:transparent; color:#222; font-size:16px; padding:0; }
QToolButton#CaptionButton:hover { background:#E5F1FB; } QToolButton#CaptionButton:pressed { background:#C9E5F7; }
QToolButton#CloseCaption:hover { background:#E81123; color:white; } QToolButton#CloseCaption:pressed { background:#B50D1B; color:white; }
"""
CHROME_DARK_QSS = """
QWidget#ToolbarContainer { background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #2A2D33,stop:.52 #272A2F,stop:1 #232529); border:none; border-bottom:1px solid #151619; border-top-left-radius:8px; border-top-right-radius:8px; }
QWidget#TitleBar, QWidget#AddressRow, QWidget#TabStrip, QWidget#FavoritesBar { background:transparent; border:none; }
QWidget#ToolbarContainer[maximized="true"] { border-top-left-radius:0; border-top-right-radius:0; } QWidget#TitleBar { border-top:1px solid rgba(255,255,255,45); }
QLabel#ChromeTitle { color:#E8E8E8; font-size:12px; }
QToolButton#CaptionButton { border:0; border-radius:0; background:transparent; color:#E8E8E8; font-size:16px; padding:0; }
QToolButton#CaptionButton:hover { background:#3D3D3D; } QToolButton#CaptionButton:pressed { background:#4A4A4A; }
QToolButton#CloseCaption:hover { background:#E81123; color:white; } QToolButton#CloseCaption:pressed { background:#B50D1B; color:white; }
"""

DEVTOOLS_QSS = """
QMainWindow#F12Window { background:#2B2B2B; color:#E6E6E6;
    font-family:"Segoe UI",sans-serif; font-size:12px; }
QLabel#F12Badge { color:#FFF; font-weight:bold; padding:5px 12px;
    border-right:1px solid #4A4A4A; }
QToolButton#F12Tab { background:transparent; color:#D7D7D7;
    border:1px solid transparent; padding:5px 12px; font-size:12px; }
QToolButton#F12Tab:hover { background:#3A3A3A; color:#FFF; }
QToolButton#F12Tab:checked { background:#4B4B4B; color:#FFF; }
QToolButton#F12Icon { background:transparent; color:#D7D7D7; border:none;
    padding:4px 9px; font-size:13px; }
QToolButton#F12Icon:hover:enabled { background:#3A3A3A; color:#FFF; }
QToolButton#F12Icon:disabled { color:#6A6A6A; }
QWidget#F12SubBar { background:#1F1F1F; border-top:1px solid #3A3A3A;
    border-bottom:1px solid #3A3A3A; }
QLineEdit#F12Find { background:#141414; color:#E6E6E6; border:1px solid #4A4A4A;
    padding:2px 6px; }
"""

DOWNLOADS_QSS = """
QDialog { background:#FFFFFF; color:#1A1A1A; font-family:"Segoe UI",sans-serif; font-size:12px; }
QLabel#DlHeading { color:#1A6BB8; font-size:16px; }
QTreeWidget { background:#FFFFFF; border:1px solid #D9D9D9; }
QHeaderView::section { background:#F7F7F7; color:#3B3B3B; border:1px solid #E3E3E3;
    border-top:none; padding:4px 8px; }
QFrame#DlSearchFrame { background:#FFFFFF; border:1px solid #ABADB3; }
QLineEdit#DlSearch { border:none; background:transparent; }
QToolButton#DlSearchBtn { border:none; background:transparent; color:#555; font-size:13px; }
QToolButton#DlAction { border:none; background:transparent; color:#0645AD;
    padding:1px 7px; font-size:12px; }
QToolButton#DlAction:hover { color:#0B3D91; background:#EAF3FB; }
QPushButton { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
    stop:0 #FCFCFC, stop:1 #EDEDED); border:1px solid #ADADAD;
    border-radius:2px; padding:4px 16px; }
QPushButton:hover { border-color:#3C7FB1; }
QLabel#StatusLink { color:#0645AD; }
"""


class _SuggestSignals(QObject):
    done = pyqtSignal(int, str, object)   # token, query, results (None = error)
_suggest_conn = None
_suggest_conn_lock = threading.Lock()


def _bing_suggest_request(query):
    """Fetch Bing suggestions reusing one warm HTTPS connection."""
    global _suggest_conn
    path = _BING_SUGGEST_PATH + quote_plus(query)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
               "Accept": "application/json", "Connection": "keep-alive"}
    last_error = None
    for _attempt in range(2):  # second attempt after a stale keep-alive
        try:
            with _suggest_conn_lock:
                if _suggest_conn is None:
                    _suggest_conn = http.client.HTTPSConnection(
                        _BING_SUGGEST_HOST, timeout=3)
                _suggest_conn.request("GET", path, headers=headers)
                response = _suggest_conn.getresponse()
                body = response.read()
                if response.status != 200:
                    raise OSError(f"HTTP {response.status}")
            parsed = json.loads(body.decode("utf-8", "replace"))
            if isinstance(parsed, list) and len(parsed) >= 2 and isinstance(parsed[1], list):
                return [str(s) for s in parsed[1][:8]]
            return []
        except Exception as exc:
            last_error = exc
            with _suggest_conn_lock:
                try:
                    if _suggest_conn is not None:
                        _suggest_conn.close()
                except Exception:
                    pass
                _suggest_conn = None
    raise last_error if last_error else OSError("suggest request failed")


class SuggestWorker(threading.Thread):
    """One long-lived worker thread; always fetches only the newest query."""
    def __init__(self, browser):
        super().__init__(daemon=True)
        self.browser = browser
        self._jobs = queue.Queue()

    def submit(self, token, query):
        self._jobs.put((token, query))

    def run(self):
        while True:
            try:
                token, query = self._jobs.get()
                while True:  # drain stale jobs — latest wins
                    try:
                        token, query = self._jobs.get_nowait()
                    except queue.Empty:
                        break
                try:
                    results = _bing_suggest_request(query)
                except Exception:
                    results = None
                self.browser._suggest_sig.done.emit(token, query, results)
            except Exception:
                pass  # never let the worker die

class _HistoryItem:
    def __init__(self, title, url, index):
        self._title, self._url, self.index = title, QUrl(url), index
    def title(self): return self._title
    def url(self): return self._url

class _History:
    def __init__(self, view): self.view = view
    def canGoBack(self): return self.view._history_index > 0
    def canGoForward(self): return self.view._history_index < len(self.view._history) - 1
    def backItems(self, count):
        return [_HistoryItem(t,u,i) for i,(t,u) in reversed(list(enumerate(self.view._history[:self.view._history_index])))][:count]
    def forwardItems(self, count):
        return [_HistoryItem(t,u,i) for i,(t,u) in list(enumerate(self.view._history[self.view._history_index+1:], self.view._history_index+1))][:count]
    def goToItem(self, item): self.view._go_history_index(item.index)

class _CookieStore:
    def __init__(self, profile): self.profile = profile
    def deleteAllCookies(self):
        for view in self.profile.views:
            try: view.widget.clear_all_browsing_data()
            except Exception: pass

class _Settings:
    def setAttribute(self, *args): pass

class _Profile:
    """Compatibility shim for the old QtWebEngine profile API.
    WebView2 persists cookies/cache in its user_data_folder instead."""
    ForcePersistentCookies = 1
    def __init__(self): self.views=[]; self._settings=_Settings(); self.downloadRequested=_NoSignal()
    def setPersistentStoragePath(self, path): self.storage=path
    def setCachePath(self, path): self.cache=path
    def setPersistentCookiesPolicy(self, *_): pass
    def persistentStoragePath(self): return getattr(self,'storage',os.getcwd())
    def cachePath(self): return getattr(self,'cache',os.getcwd())
    def settings(self): return self._settings
    def cookieStore(self): return _CookieStore(self)
    def clearHttpCache(self):
        for view in self.views:
            try: view.widget.clear_all_browsing_data()
            except Exception: pass

class _NoSignal:
    def connect(self, *_): pass

class BrowserViewAdapter(QWidget):
    """Qt-widget compatibility adapter over the Microsoft Edge WebView2 backend."""
    urlChanged = pyqtSignal(object)
    titleChanged = pyqtSignal(str)
    loadProgress = pyqtSignal(int)
    loadFinished = pyqtSignal(bool)
    iconChanged = pyqtSignal(object)
    linkHovered = pyqtSignal(str)
    newWindowRequested = pyqtSignal(str)
    def __init__(self, browser, parent=None, is_private=False):
        super().__init__(parent)
        self.browser=browser; self._url=QUrl('about:blank'); self._title=''; self._icon=QIcon()
        self._history=[]; self._history_index=-1; self._zoom=1.0; self._last_progress=0
        self.widget=QtWebViewWidget(parent=self,
            user_data_folder=None if is_private else os.path.join(browser.data_dir,'webview2'),
            # Passing no user-agent override lets WebView2 expose its current,
            # Evergreen Edge/Chromium identity to modern sites.
            incognito=is_private, user_agent=browser.web_user_agent, debug=False, lazyload=False,
            new_window_handler=self._new_window_handler,
            download_started_handler=self._download_started,
            download_completed_handler=self._download_completed)
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0); layout.addWidget(self.widget)
        browser.profile.views.append(self)
        self.widget.signals.navigation_requested.connect(self._on_navigation)
        self.widget.signals.title_changed.connect(self._on_title)
        self.widget.signals.page_loaded.connect(self._on_loaded)
        self.newWindowRequested.connect(browser.open_new_window_url)
    def _download_started(self, url, path):
        # WebView2 selects its default download path; accept and record it.
        try:
            directory = os.path.dirname(path) or os.path.join(os.path.expanduser('~'), 'Downloads')
            os.makedirs(directory, exist_ok=True)
            rec = {"name": os.path.basename(path), "dir": directory, "path": path,
                   "item": None, "done": False, "ok": None, "received": 0,
                   "total": 0, "row": None}
            self.browser.download_records.append(rec)
            self.browser.downloads.append(path)
            self.browser.downloads = self.browser.downloads[-200:]
            self.browser.save_state()
            dlg = getattr(self.browser, '_downloads_dialog', None)
            if dlg is not None and dlg.isVisible(): dlg.refresh()
            self.browser.status_label.setText('Downloading: ' + os.path.basename(path))
        except Exception: pass
        return True
    def _download_completed(self, url, path, ok):
        try:
            for rec in reversed(self.browser.download_records):
                if rec.get('path') == path:
                    rec['done'] = True; rec['ok'] = bool(ok); break
            dlg = getattr(self.browser, '_downloads_dialog', None)
            if dlg is not None and dlg.isVisible(): dlg.refresh()
            self.browser.status_label.setText(('Download finished: ' if ok else 'Download failed: ')+os.path.basename(path))
            if ok:
                self.browser.infobar.show_message("Download of %s completed." % os.path.basename(path), [("Open", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(path))), ("Open folder", lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path))) )])
        except Exception: pass
    def _on_navigation(self, url):
        try: self._url=QUrl(str(url)); self.urlChanged.emit(self._url); self.loadProgress.emit(15)
        except Exception: pass
    def _on_title(self, title):
        self._title=str(title or ''); self.titleChanged.emit(self._title)
    def _on_loaded(self, event, url):
        try:
            self._url=QUrl(str(url)); self.urlChanged.emit(self._url)
            self.loadProgress.emit(100); self.loadFinished.emit(event == PageLoadEvent.Finished or str(event).lower().endswith("finished"))
            u=self._url.toString()
            if u and (not self._history or self._history[self._history_index][1] != u):
                self._history=self._history[:self._history_index+1]; self._history.append((self._title or u,u)); self._history_index=len(self._history)-1
        except Exception: self.loadFinished.emit(True)
    def _new_window_handler(self, url):
        """qtwebview2's supported popup hook; never invoke webbrowser.open."""
        self.newWindowRequested.emit(str(url))
        return NewWindowResponse.Deny
    def setUrl(self, url):
        self._url=url if isinstance(url,QUrl) else QUrl(str(url)); self.widget.load_url(self._url.toString())
    def setHtml(self, html, base_url=None):
        # Resolve the optional logo locally before loading HTML in WebView2.
        if base_url:
            try:
                logo=find_resource('ie11_logo.png')
                if logo: html=html.replace('src="ie11_logo.png"', 'src="'+QUrl.fromLocalFile(logo).toString()+'"')
            except Exception: pass
        self.widget.load_html(html)
    def url(self): return self._url
    def title(self): return self._title
    def icon(self): return self._icon
    def history(self): return _History(self)
    def back(self):
        if self.history().canGoBack(): self._go_history_index(self._history_index-1)
    def forward(self):
        if self.history().canGoForward(): self._go_history_index(self._history_index+1)
    def _go_history_index(self, i):
        if 0 <= i < len(self._history): self._history_index=i; self.setUrl(QUrl(self._history[i][1]))
    def reload(self): self.widget.reload()
    def stop(self):
        try: self.widget.eval_js('window.stop()')
        except Exception: pass
    def setZoomFactor(self, value): self._zoom=max(.25,min(5.0,float(value))); self.widget.zoom(self._zoom)
    def zoomFactor(self): return self._zoom
    def findText(self, text):
        safe=json.dumps(text); self.widget.eval_js("(function(){let t="+safe+";let s=window.find(t);return s;})()")
    def setFocus(self): self.widget.focus()
    def page(self): return self
    def toHtml(self, callback):
        try: self.widget.evaluate_js('document.documentElement.outerHTML', callback)
        except Exception: callback('')
    def printToPdf(self, filename=None):
        # WebView2 exposes native print; users can select Microsoft Print to PDF.
        try: self.widget.print()
        except Exception: pass
    def open_devtools(self): self.widget.open_devtools()
    def mapToGlobal(self, pos): return super().mapToGlobal(pos)


class BrowserTab(QWidget):
    def __init__(self, browser, url=NEW_TAB_URL, is_private=False):
        super().__init__()
        self.browser=browser; self.is_private=is_private; self.loading=False; self.loading_frame=0; self.failed_url=""; self.error_detail=""
        self.view=BrowserViewAdapter(browser,self,is_private=is_private)
        self.page=self.view
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        self.private_strip=QLabel("  InPrivate")
        self.private_strip.setFixedHeight(20); self.private_strip.setStyleSheet("background:#4B2E6B;color:white;font-weight:bold;padding:2px 8px")
        self.private_strip.setVisible(is_private); layout.addWidget(self.private_strip); layout.addWidget(self.view)
        self.view.urlChanged.connect(lambda u: browser.on_url_changed(self,u))
        self.view.titleChanged.connect(lambda t: browser.on_title_changed(self,t))
        self.view.loadProgress.connect(lambda v: browser.on_load_progress(self,v))
        self.view.loadFinished.connect(lambda ok: browser.on_load_finished(self,ok))
        self.view.iconChanged.connect(lambda icon: browser.on_icon_changed(self,icon))
        self.view.linkHovered.connect(lambda link: browser.on_link_hovered(self,link))
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(lambda pos: browser.page_context_menu(self,pos))
        self.is_custom_new_tab=url in (NEW_TAB_URL,'about:blank')
        if self.is_custom_new_tab: self.view.setHtml(build_new_tab_html(browser.dark_mode))
        else: self.view.setUrl(QUrl(url))


class SuggestionPopup(QWidget):
    """The IE11 address-bar dropdown: history, Bing Suggestions, the
    'Turn off suggestions' row, and the Bing icon + Add footer."""

    def __init__(self, browser):
        super().__init__(browser, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setObjectName("SuggestPopup")
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.NoFocus)
        self.browser = browser
        self._last_text = ""
        self._current_target = browser.address_frame
        self.setStyleSheet("""
            QWidget#SuggestPopup { background:#FFFFFF; border:1px solid #9A9A9A; }
            QWidget { background:#FFFFFF; color:#222; font-family:"Segoe UI",sans-serif; font-size:12px; }
            QListWidget#SuggestList { background:#FFFFFF; border:none; outline:0; }
            QListWidget#SuggestList::item { padding:4px 12px; }
            QListWidget#SuggestList::item:selected { background:#CDE6F7; color:#000; }
            QWidget#SuggestFooter { background:#F4F4F4; border-top:1px solid #E0E0E0; }
            QPushButton#SuggestAdd {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FCFCFC, stop:1 #EDEDED);
                border:1px solid #ADADAD; border-radius:2px; padding:3px 16px; }
            QPushButton#SuggestAdd:hover { border-color:#3C7FB1; }
            QLabel#BingDot { background:#0B84D8; color:#FFF; border-radius:3px;
                font-weight:bold; font-size:12px; }
        """)
        v = QVBoxLayout(self)
        v.setContentsMargins(1, 1, 1, 1)
        v.setSpacing(0)
        self.list = QListWidget()
        self.list.setObjectName("SuggestList")
        self.list.setFocusPolicy(Qt.NoFocus)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list.itemClicked.connect(self._clicked)
        v.addWidget(self.list, 1)
        self.footer = QWidget()
        self.footer.setObjectName("SuggestFooter")
        self.footer.setFocusPolicy(Qt.NoFocus)
        f = QHBoxLayout(self.footer)
        f.setContentsMargins(6, 3, 6, 3)
        f.setSpacing(6)
        bing = QLabel("b")
        bing.setObjectName("BingDot")
        bing.setFixedSize(18, 18)
        bing.setAlignment(Qt.AlignCenter)
        f.addWidget(bing)
        f.addStretch(1)
        add_btn = QPushButton("Add")
        add_btn.setObjectName("SuggestAdd")
        add_btn.setFocusPolicy(Qt.NoFocus)
        add_btn.clicked.connect(self._add_provider)
        f.addWidget(add_btn)
        v.addWidget(self.footer)

    def _target_input(self):
        target = getattr(self, "_current_target", None)
        if target is getattr(self.browser, "search_bar", None):
            return self.browser.search_bar
        return self.browser.address_bar

    def _restore_focus(self):
        target = self._target_input()
        if target:
            target.setFocus()

    def populate(self, text, want_bing=True, pending=False, results=None, error=False):
        text = (text or "").strip()
        self._last_text = text
        self.list.clear()
        if text:
            low = text.lower()
            seen = set()
            matches = []
            for title, url in reversed(self.browser.history):
                if url in seen:
                    continue
                tl = (title or "").lower()
                if low in url.lower() or (tl and low in tl):
                    matches.append((title or url, url))
                    seen.add(url)
                if len(matches) >= 3:
                    break
            for title, url in matches:
                it = QListWidgetItem("🌐  " + title)
                it.setData(Qt.UserRole, ("history", url))
                it.setToolTip(url)
                self.list.addItem(it)
        show_bing = want_bing and self.browser.suggestions_enabled and bool(text)
        if show_bing:
            header = QListWidgetItem("Bing Suggestions")
            header.setFlags(Qt.NoItemFlags)
            header.setForeground(QBrush(QColor("#7A7A7A")))
            self.list.addItem(header)
            note = None
            if pending:
                note = "Searching Bing suggestions…"
            elif error:
                note = "An error occurred."
            if note:
                ph = QListWidgetItem(note)
                ph.setFlags(Qt.NoItemFlags)
                fo = ph.font()
                fo.setItalic(True)
                ph.setFont(fo)
                ph.setForeground(QBrush(QColor("#9A9A9A")))
                self.list.addItem(ph)
            else:
                for s in (results or [])[:8]:
                    it = QListWidgetItem("⌕  " + s)
                    it.setData(Qt.UserRole, ("suggest", s))
                    self.list.addItem(it)
            turn = QListWidgetItem("Turn off suggestions (stop sending keystrokes to Bing)")
            turn.setFlags(Qt.ItemIsEnabled)
            turn.setForeground(QBrush(QColor("#0645AD")))
            turn.setData(Qt.UserRole, ("turnoff", None))
            self.list.addItem(turn)
        elif not text:
            for title, url in list(reversed(self.browser.history))[:10]:
                it = QListWidgetItem("🌐  " + (title or url))
                it.setData(Qt.UserRole, ("history", url))
                it.setToolTip(url)
                self.list.addItem(it)
        self._resize_to_content()

    def apply_results(self, query, results):
        if self._last_text != query:
            return
        self.populate(query, want_bing=True, pending=False,
                      results=results, error=(results is None))

    def _resize_to_content(self):
        fm = self.list.fontMetrics()
        row_h = fm.height() + 9
        h = min(340, self.list.count() * row_h + 10)
        target = getattr(self, "_current_target", None) or self.browser.address_frame
        w = max(440, target.width()) if target is self.browser.address_frame else max(300, target.width())
        if w != self.width():
            self.setFixedWidth(w)
        total = h + self.footer.sizeHint().height() + 4
        if total != self.height():
            self.setFixedHeight(total)

    def show_at(self, target_widget=None):
        if self.list.count() == 0:
            return
        target = target_widget or getattr(self, "_current_target", None) or self.browser.address_frame
        self._current_target = target
        pos = target.mapToGlobal(QPoint(0, target.height()))
        self.move(pos)
        self._resize_to_content()
        if not self.isVisible():
            self.show()

    def _clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        kind, payload = data
        if kind == "turnoff":
            self.browser.set_suggestions_enabled(False)
            self.hide()
            self._restore_focus()
        elif kind == "history":
            self.hide()
            self.browser.navigate(payload)
            self._restore_focus()
        elif kind == "suggest":
            self.hide()
            self.browser.navigate(BING_SEARCH_URL + quote_plus(payload))
            self._restore_focus()

    def trigger_current(self):
        item = self.list.currentItem()
        if not item:
            return False
        data = item.data(Qt.UserRole)
        if not data:
            return False
        kind, payload = data
        if kind == "turnoff":
            self.browser.set_suggestions_enabled(False)
            self.hide()
            self._restore_focus()
            return True
        if kind == "history":
            self.hide()
            self.browser.navigate(payload)
            self._restore_focus()
            return True
        if kind == "suggest":
            self.hide()
            self.browser.navigate(BING_SEARCH_URL + quote_plus(payload))
            self._restore_focus()
            return True
        return False

    def move_selection(self, delta):
        count = self.list.count()
        if count == 0:
            return
        row = self.list.currentRow()
        if row < 0:
            row = 0 if delta > 0 else count - 1
        else:
            row = (row + delta) % count
        for _ in range(count):
            it = self.list.item(row)
            if it and (it.flags() & Qt.ItemIsSelectable):
                self.list.setCurrentRow(row)
                self.list.scrollToItem(it)
                return
            row = (row + delta) % count

    def _add_provider(self):
        QMessageBox.information(
            self, "Add a search provider",
            "Bing is already your default search provider.\n\n"
            "Additional search providers are not available in this\n"
            "nostalgia edition of Internet Explorer.")


def download_row_text(rec):
    if rec.get("done"):
        if rec.get("ok") is False:
            return rec["name"] + " (canceled)"
        return rec["name"]
    total = rec.get("total") or 0
    received = rec.get("received") or 0
    if total > 0:
        return f'{rec["name"]} — {int(received * 100 / total)}%'
    if received > 0:
        return f'{rec["name"]} — {received / 1048576:.1f} MB'
    return rec["name"]


class DownloadsDialog(QDialog):
    """Recreation of 'View Downloads - Internet Explorer'."""

    def __init__(self, browser):
        super().__init__(browser)
        self.browser = browser
        self.setWindowTitle("View Downloads - Internet Explorer")
        self.setWindowIcon(browser.windowIcon())
        self.resize(680, 430)
        self.setStyleSheet(DOWNLOADS_QSS)
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 10)
        v.setSpacing(8)
        top = QHBoxLayout()
        head = QLabel("View and track your downloads")
        head.setObjectName("DlHeading")
        top.addWidget(head)
        top.addStretch(1)
        search_frame = QFrame()
        search_frame.setObjectName("DlSearchFrame")
        search_frame.setFixedWidth(250)
        sh = QHBoxLayout(search_frame)
        sh.setContentsMargins(6, 1, 2, 1)
        sh.setSpacing(2)
        self.search = QLineEdit()
        self.search.setObjectName("DlSearch")
        self.search.setPlaceholderText("Search downloads")
        mag = QToolButton()
        mag.setObjectName("DlSearchBtn")
        mag.setText("⌕")
        mag.setCursor(Qt.PointingHandCursor)
        sh.addWidget(self.search, 1)
        sh.addWidget(mag)
        top.addWidget(search_frame)
        v.addLayout(top)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name", "Location", "Actions"])
        self.tree.setRootIsDecorated(False)
        self.tree.setUniformRowHeights(True)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Interactive)
        self.tree.setColumnWidth(0, 230)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.Fixed)
        self.tree.setColumnWidth(2, 180)
        v.addWidget(self.tree, 1)
        bottom = QHBoxLayout()
        opts = QLabel('<a href="#options">Options</a>')
        opts.setObjectName("StatusLink")
        opts.linkActivated.connect(lambda _: QMessageBox.information(
            self, "Download options",
            "Files are saved to the folder you choose when each download starts."))
        bottom.addWidget(opts)
        bottom.addStretch(1)
        clear = QPushButton("Clear list")
        close = QPushButton("Close")
        close.setDefault(True)
        clear.clicked.connect(self.clear_list)
        close.clicked.connect(self.close)
        bottom.addWidget(clear)
        bottom.addWidget(close)
        v.addLayout(bottom)
        self.search.textChanged.connect(self.filter_rows)
        self.refresh()

    def refresh(self):
        self.tree.clear()
        for rec in reversed(self.browser.download_records):
            item = QTreeWidgetItem([download_row_text(rec), rec.get("dir") or "", ""])
            rec["row"] = item
            self.tree.addTopLevelItem(item)
            self.tree.setItemWidget(item, 2, self._actions_widget(rec))

    def update_row(self, rec):
        row = rec.get("row")
        if row is not None:
            row.setText(0, download_row_text(rec))

    def _actions_widget(self, rec):
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(2, 0, 2, 0)
        h.setSpacing(10)
        if rec.get("done"):
            open_btn = QToolButton()
            open_btn.setObjectName("DlAction")
            open_btn.setText("Open")
            open_btn.setCursor(Qt.PointingHandCursor)
            open_btn.clicked.connect(lambda checked=False, r=rec:
                                     QDesktopServices.openUrl(QUrl.fromLocalFile(r["path"])))
            h.addWidget(open_btn)
            folder_btn = QToolButton()
            folder_btn.setObjectName("DlAction")
            folder_btn.setText("Open folder")
            folder_btn.setCursor(Qt.PointingHandCursor)
            folder_btn.clicked.connect(lambda checked=False, r=rec:
                                       QDesktopServices.openUrl(QUrl.fromLocalFile(r.get("dir") or os.getcwd())))
            h.addWidget(folder_btn)
        else:
            cancel_btn = QToolButton()
            cancel_btn.setObjectName("DlAction")
            cancel_btn.setText("Cancel")
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.clicked.connect(lambda checked=False, r=rec: r["item"].cancel())
            h.addWidget(cancel_btn)
        h.addStretch(1)
        return w

    def filter_rows(self, text):
        t = text.strip().lower()
        for i in range(self.tree.topLevelItemCount()):
            it = self.tree.topLevelItem(i)
            match = (t in it.text(0).lower()) or (t in it.text(1).lower())
            it.setHidden(bool(t) and not match)

    def clear_list(self):
        self.browser.download_records = [r for r in self.browser.download_records if not r.get("done")]
        self.refresh()


class DevToolsWindow(QMainWindow):
    """IE11-style F12 window (DOM Explorer / Console / Debugger / ...) with
    the real Chromium developer tools embedded underneath."""

    PANELS = (("DOM Explorer", "elements"), ("Console", "console"),
              ("Debugger", "sources"), ("Network", "network"),
              ("Performance", "timeline"), ("Memory", "memory"),
              ("Emulation", "emulation"))

    def __init__(self, browser):
        super().__init__(None)
        self.setObjectName("F12Window")
        self.browser = browser
        self.setWindowTitle("F12 Developer Tools")
        self.setWindowIcon(browser.windowIcon())
        self.resize(1180, 760)
        self._inspected = None
        self._mode = None
        self._remote_base = None
        root = QWidget()
        v = QVBoxLayout(root)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)
        row1 = QWidget()
        h = QHBoxLayout(row1)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        badge = QLabel("F12")
        badge.setObjectName("F12Badge")
        h.addWidget(badge)
        self.panel_btns = []
        for label, key in self.PANELS:
            b = QToolButton()
            b.setText(label)
            b.setObjectName("F12Tab")
            b.setCheckable(True)
            b.setToolTip(f"{label}  (Chromium panel: {key})")
            b.clicked.connect(lambda checked=False, name=label: self.select_panel(name))
            h.addWidget(b)
            self.panel_btns.append(b)
        self.panel_btns[0].setChecked(True)
        h.addStretch(1)
        dock = QToolButton()
        dock.setObjectName("F12Icon")
        dock.setText("🗗")
        dock.setToolTip("Dock the tools (nostalgia only)")
        dock.setEnabled(False)
        h.addWidget(dock)
        help_btn = QToolButton()
        help_btn.setObjectName("F12Icon")
        help_btn.setText("?")
        help_btn.clicked.connect(self._about)
        h.addWidget(help_btn)
        close_btn = QToolButton()
        close_btn.setObjectName("F12Icon")
        close_btn.setText("✕")
        close_btn.clicked.connect(self.close)
        h.addWidget(close_btn)
        v.addWidget(row1)
        row2 = QWidget()
        row2.setObjectName("F12SubBar")
        h2 = QHBoxLayout(row2)
        h2.setContentsMargins(6, 3, 6, 3)
        h2.setSpacing(6)
        insp = QToolButton()
        insp.setObjectName("F12Icon")
        insp.setText("⌖")
        insp.setToolTip("Select element (right-click the page → Inspect element)")
        insp.setEnabled(False)
        h2.addWidget(insp)
        rel = QToolButton()
        rel.setObjectName("F12Icon")
        rel.setText("⟳")
        rel.setToolTip("Refresh the tools")
        rel.clicked.connect(self.view_reload)
        h2.addWidget(rel)
        h2.addStretch(1)
        self.find = QLineEdit()
        self.find.setObjectName("F12Find")
        self.find.setPlaceholderText("Find (Ctrl+F)")
        self.find.setFixedWidth(200)
        h2.addWidget(self.find)
        v.addWidget(row2)
        self.view = QLabel("Use the browser's native Edge DevTools window (F12).")
        self.view.setAlignment(Qt.AlignCenter)
        v.addWidget(self.view, 1)
        self.setCentralWidget(root)
        self.setStyleSheet(DEVTOOLS_QSS)

    def view_reload(self):
        pass

    def select_panel(self, name):
        for i, (label, _key) in enumerate(self.PANELS):
            self.panel_btns[i].setChecked(label == name)
        # WebView2 owns its native DevTools window; these legacy panel buttons are decorative.

    def attach(self, tab):
        """Bind the tools to a page using QtWebEngine's built-in inspector."""
        page = tab.page
        if False:
            if self._inspected is not None and self._inspected is not page:
                try:
                    self._inspected.setDevToolsPage(None)
                except RuntimeError:
                    pass
            try:
                page.setDevToolsPage(self.view.page())
                self._inspected = page
                self._mode = "embedded"
                return True
            except Exception:
                return False
        return False

    def load_remote(self, url):
        self._mode = "remote"
        self.view.setUrl(QUrl(url))

    def _about(self):
        QMessageBox.information(
            self, "About the developer tools",
            "These F12 tools embed the Chromium DevTools frontend "
            "(Elements, Console, Sources/Debugger, Network, Performance, Memory).\n"
            "Switch panels with the tabs inside the tools area.")

    def detach(self):
        if self._inspected is not None:
            try:
                self._inspected.setDevToolsPage(None)
            except RuntimeError:
                pass
        self._inspected = None

    def closeEvent(self, event):
        self.detach()
        event.accept()


class ChromeTitleBar(QWidget):
    """Small event-owning title row; caption buttons are never drag targets."""
    def __init__(self, window):
        super().__init__(window); self.window = window; self.setObjectName("TitleBar"); self.setFixedHeight(34)
        row=QHBoxLayout(self); row.setContentsMargins(8,0,0,0); row.setSpacing(7)
        self.icon=QToolButton(); self.icon.setIcon(load_ie_icon()); self.icon.setIconSize(QSize(16,16)); self.icon.setFixedSize(22,30); self.icon.setStyleSheet("border:0;background:transparent;")
        self.title=QLabel("Internet Explorer"); self.title.setObjectName("ChromeTitle"); self.title.setSizePolicy(__import__('PyQt5.QtWidgets',fromlist=['QSizePolicy']).QSizePolicy.Expanding, __import__('PyQt5.QtWidgets',fromlist=['QSizePolicy']).QSizePolicy.Preferred)
        self.icon.installEventFilter(self); self.title.installEventFilter(self); self._icon_press=None
        row.addWidget(self.icon); row.addWidget(self.title,1)
        self.min_btn=self._button("—", "Minimize"); self.max_btn=self._button("□", "Maximize"); self.close_btn=self._button("✕", "Close", True)
        self.min_btn.clicked.connect(window.showMinimized); self.max_btn.clicked.connect(window.toggle_maximize); self.close_btn.clicked.connect(window.close)
        row.addWidget(self.min_btn); row.addWidget(self.max_btn); row.addWidget(self.close_btn)
    def _button(self, glyph, tip, close=False):
        b=QToolButton(); b.setObjectName("CloseCaption" if close else "CaptionButton"); b.setText(glyph); b.setToolTip(tip); b.setFixedSize(46,32); b.setFocusPolicy(Qt.NoFocus); return b
    def set_title(self, text):
        self.title.setText(QFontMetrics(self.title.font()).elidedText(text, Qt.ElideRight, max(40,self.width()-170)))
        self.title.setVisible(self.window.width() >= 480)
        self.max_btn.setText("❐" if self.window.isMaximized() else "□")
    def mousePressEvent(self,event):
        if event.button()==Qt.RightButton: self.window.show_system_menu(event.globalPos()); event.accept(); return
        if event.button()==Qt.LeftButton and self.childAt(event.pos()) not in (self.min_btn,self.max_btn,self.close_btn): self.window.chrome_drag_start(event.globalPos()); event.accept(); return
        super().mousePressEvent(event)
    def eventFilter(self,obj,event):
        if obj in (self.icon,self.title):
            if event.type()==QEvent.MouseButtonDblClick and event.button()==Qt.LeftButton:
                self.window.toggle_maximize(); return True
            if event.type()==QEvent.MouseButtonPress and event.button()==Qt.LeftButton:
                self._icon_press=event.globalPos(); self.window.chrome_drag_start(event.globalPos()); return True
            if event.type()==QEvent.MouseMove and self._icon_press is not None:
                self.window.chrome_drag_move(event.globalPos()); return True
            if event.type()==QEvent.MouseButtonRelease and event.button()==Qt.LeftButton:
                moved=(event.globalPos()-self._icon_press).manhattanLength() if self._icon_press else 99; self.window.chrome_drag_end()
                if obj is self.icon and moved < 4: self.window.show_system_menu(self.icon.mapToGlobal(QPoint(0,self.icon.height())))
                self._icon_press=None; return True
            if event.type()==QEvent.MouseButtonPress and event.button()==Qt.RightButton:
                self.window.show_system_menu(event.globalPos()); return True
        return super().eventFilter(obj,event)
    def mouseMoveEvent(self,event): self.window.chrome_drag_move(event.globalPos()); super().mouseMoveEvent(event)
    def mouseReleaseEvent(self,event): self.window.chrome_drag_end(); super().mouseReleaseEvent(event)
    def mouseDoubleClickEvent(self,event):
        if event.button()==Qt.LeftButton and self.childAt(event.pos()) not in (self.min_btn,self.max_btn,self.close_btn): self.window.toggle_maximize(); event.accept(); return
        super().mouseDoubleClickEvent(event)


class TitleBarMixin:
    """Frameless-window plumbing.  DWM and WM_NCHITTEST remain optional."""
    _resize_margin = 6
    def setup_custom_chrome(self):
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self._chrome_drag_origin=None; self._chrome_normal_geometry=None; self._manual_resize_edge=None
    def setWindowTitle(self, title):
        super().setWindowTitle(title)
        if hasattr(self,"titlebar"): self._update_chrome_title()
    def build_titlebar(self, toolbar_layout):
        self.titlebar=ChromeTitleBar(self)
        toolbar_layout.insertWidget(0,self.titlebar)
        self._update_chrome_title()
    def _update_chrome_title(self):
        if hasattr(self,"titlebar"): self.titlebar.set_title(self.windowTitle())
    def toggle_maximize(self):
        if self.isMaximized(): self.showNormal()
        else: self.showMaximized()
        QTimer.singleShot(0,self._update_chrome_title)
    def chrome_drag_start(self, global_pos):
        self._chrome_drag_origin=global_pos; self._chrome_normal_geometry=self.geometry()
    def chrome_drag_move(self, global_pos):
        if self._chrome_drag_origin is None: return
        if self.isMaximized():
            ratio=(self._chrome_drag_origin.x()-self.geometry().x())/max(1,self.width())
            self.showNormal(); geo=self.geometry(); self.move(global_pos.x()-int(geo.width()*ratio), global_pos.y()-17)
            self._chrome_drag_origin=global_pos; return
        self.move(self.pos() + global_pos-self._chrome_drag_origin); self._chrome_drag_origin=global_pos
    def chrome_drag_end(self): self._chrome_drag_origin=None
    def show_system_menu(self, global_pos=None):
        menu=QMenu(self); restore=self.action(menu,"Restore",self.showNormal); restore.setEnabled(self.isMaximized() or self.isMinimized())
        move=self.action(menu,"Move",lambda:None); move.setEnabled(False); size=self.action(menu,"Size",lambda:None); size.setEnabled(False)
        menu.addSeparator(); self.action(menu,"Minimize",self.showMinimized); maximize=self.action(menu,"Maximize",self.showMaximized); maximize.setEnabled(not self.isMaximized()); menu.addSeparator(); self.action(menu,"Close",self.close)
        menu.exec_(global_pos or QCursor.pos())
    def _apply_dwm_chrome(self):
        if sys.platform != "win32": return
        try:
            import ctypes
            class MARGINS(ctypes.Structure): _fields_=[("cxLeftWidth",ctypes.c_int),("cxRightWidth",ctypes.c_int),("cyTopHeight",ctypes.c_int),("cyBottomHeight",ctypes.c_int)]
            hwnd=int(self.winId()); dwm=ctypes.windll.dwmapi
            dwm.DwmExtendFrameIntoClientArea(hwnd,ctypes.byref(MARGINS(0,0,1,0)))
            for attr,value in ((33,2),(38,2)):
                val=ctypes.c_int(value)
                try: dwm.DwmSetWindowAttribute(hwnd,attr,ctypes.byref(val),ctypes.sizeof(val))
                except Exception: pass
        except Exception: pass
    def changeEvent(self,event):
        super().changeEvent(event)
        if event.type()==QEvent.WindowStateChange:
            self._update_chrome_title()
            if hasattr(self,"toolbar_container"):
                self.toolbar_container.setProperty("maximized", self.isMaximized()); self.toolbar_container.style().unpolish(self.toolbar_container); self.toolbar_container.style().polish(self.toolbar_container)
    def showEvent(self,event):
        super().showEvent(event)
        QTimer.singleShot(0,self._apply_dwm_chrome)
    def nativeEvent(self, event_type, message):
        # Native hit-testing preserves Windows snap, resizing and DWM shadows.
        if sys.platform == "win32" and not self.isFullScreen():
            try:
                import ctypes
                class POINT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
                class MSG(ctypes.Structure): _fields_=[("hwnd",ctypes.c_void_p),("message",ctypes.c_uint),("wParam",ctypes.c_void_p),("lParam",ctypes.c_void_p),("time",ctypes.c_uint),("pt",POINT)]
                msg=MSG.from_address(int(message))
                if msg.message == 0x0084: # WM_NCHITTEST
                    p=self.mapFromGlobal(QPoint(msg.pt.x,msg.pt.y)); m=self._resize_margin; w,h=self.width(),self.height()
                    if not self.isMaximized():
                        if p.x()<m and p.y()<m:return True,13
                        if p.x()>=w-m and p.y()<m:return True,14
                        if p.x()<m and p.y()>=h-m:return True,16
                        if p.x()>=w-m and p.y()>=h-m:return True,17
                        if p.x()<m:return True,10
                        if p.x()>=w-m:return True,11
                        if p.y()<m:return True,12
                        if p.y()>=h-m:return True,15
                    if hasattr(self,"titlebar") and self.titlebar.geometry().contains(p):
                        child=self.titlebar.childAt(self.titlebar.mapFrom(self,p))
                        if child not in (self.titlebar.min_btn,self.titlebar.max_btn,self.titlebar.close_btn): return True,2
            except Exception: pass
        return super().nativeEvent(event_type,message)


class IE11Nostalgia(TitleBarMixin, QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_custom_chrome()
        self.setWindowTitle("Internet Explorer")
        self.setWindowIcon(load_ie_icon())
        self.resize(1250, 790)
        self.setMinimumSize(780, 500)
        self.data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not self.data_dir:
            self.data_dir = os.path.join(os.path.expanduser("~"), ".ie11_nostalgia")
        os.makedirs(self.data_dir, exist_ok=True)
        self.state_file = os.path.join(self.data_dir, "browser_state.json")
        self.password_vault_file = os.path.join(self.data_dir, "password_vault.dat")
        self.dark_mode = False
        self.suggestions_enabled = True
        self.sounds_enabled = True; self.offline = False; self.caret_browsing = False
        # The interface is IE11-inspired, but rendering is always modern Edge
        # WebView2.  "ie11" remains an opt-in compatibility user-agent only.
        self.browser_mode = "modern"; self.zoom_sites = {}; self.popup_whitelist = []
        self.site_permissions = {}
        self.saved_session = {"tabs": [], "active": 0}; self._was_unclean = False; self._first_load = True
        self.favorites = [("🌐  Bing", "https://www.bing.com/"), ("🌐  MSN", HOME_URL)]
        self.history = []
        self.closed_tabs = []
        self.downloads = []
        self.download_records = []
        self.passwords = []
        self._suggest_token = 0
        self._suggest_suppressed_text = None
        self._load_state()
        self._load_password_vault()
        self._mark_running()
        self.web_user_agent = self._user_agent_for_mode(self.browser_mode)
        self.profile = _Profile()
        self.private_profile = _Profile()  # off-the-record profile when the backend supports one
        self.profile.setPersistentStoragePath(os.path.join(self.data_dir, "webdata"))
        self.profile.setCachePath(os.path.join(self.data_dir, "cache"))
        os.makedirs(self.profile.persistentStoragePath(), exist_ok=True)
        os.makedirs(self.profile.cachePath(), exist_ok=True)
        self._init_sounds()
        self._build_ui()
        self._loading_timer = QTimer(self)
        self._loading_timer.timeout.connect(self._tick_loading_icons)
        self._loading_timer.start(80)
        self._apply_theme()
        self._connect_downloads()
        self.add_tab(HOME_URL)
        if self._was_unclean and self.saved_session.get("tabs"):
            QTimer.singleShot(350, self._show_restore_infobar)
        elif self.saved_session.get("tabs"):
            QTimer.singleShot(100, self.restore_session)
        self._try_aero_glass()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self):
        self._suggest_sig = _SuggestSignals()
        self._suggest_sig.done.connect(self._on_suggestions)
        central = QWidget()
        main = QVBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        toolbar = QWidget()
        toolbar.setObjectName("ToolbarContainer")
        self.toolbar_container = toolbar
        col = QVBoxLayout(toolbar)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        self.build_titlebar(col)

        # ---- Address row (TOP): [▾][Back(large)][Forward][▾] address ⟳ | search ⌕ ----
        addr_row = QWidget()
        addr_row.setObjectName("AddressRow")
        ar = QHBoxLayout(addr_row)
        ar.setContentsMargins(8, 5, 8, 3)
        ar.setSpacing(3)

        # Recent-pages dropdown sits on the LEFT of the (image-based) Back button.
        nav = load_nav_pixmaps()
        if nav:
            back_on = scale_nav_pixmap(nav["back"], BACK_BUTTON_SIZE)
            back_off = scale_nav_pixmap(nav["back_gray"], BACK_BUTTON_SIZE)
            fwd_on = scale_nav_pixmap(nav["forward"], FORWARD_BUTTON_SIZE)
            fwd_off = scale_nav_pixmap(nav["forward_gray"], FORWARD_BUTTON_SIZE)
        else:
            back_on = make_fallback_nav_pixmap(BACK_BUTTON_SIZE, "left", True)
            back_off = make_fallback_nav_pixmap(BACK_BUTTON_SIZE, "left", False)
            fwd_on = make_fallback_nav_pixmap(FORWARD_BUTTON_SIZE, "right", True)
            fwd_off = make_fallback_nav_pixmap(FORWARD_BUTTON_SIZE, "right", False)

        self.back_drop = QToolButton()
        self.back_drop.setObjectName("NavDrop")
        self.back_drop.setText("▾")
        self.back_drop.setFixedSize(12, back_on.height())
        self.back_drop.setToolTip("See recent pages")
        self.back_drop.clicked.connect(self.show_back_history)
        self.back_btn = NavImageButton(back_on, back_off, "Back (Alt+Left)")
        self.back_btn.clicked.connect(self.go_back)
        self.forward_btn = NavImageButton(fwd_on, fwd_off, "Forward (Alt+Right)")
        self.forward_btn.clicked.connect(self.go_forward)
        self.forward_drop = QToolButton()
        self.forward_drop.setObjectName("NavDrop")
        self.forward_drop.setText("▾")
        self.forward_drop.setFixedSize(12, fwd_on.height())
        self.forward_drop.setToolTip("See pages you can go forward to")
        self.forward_drop.clicked.connect(self.show_forward_history)

        ar.addWidget(self.back_drop)
        ar.addWidget(self.back_btn)
        ar.addSpacing(3)
        ar.addWidget(self.forward_btn)
        ar.addWidget(self.forward_drop)
        ar.addSpacing(6)

        self.address_frame = QFrame()
        self.address_frame.setObjectName("AddressFrame")
        self.address_frame.setFixedHeight(30)
        self.address_frame.setProperty("focus", False)
        ah = QHBoxLayout(self.address_frame)
        ah.setContentsMargins(6, 2, 4, 2)
        ah.setSpacing(4)
        self.favicon_label = DraggableFavicon(self)
        self.favicon_label.setFixedSize(18, 18)
        self.favicon_label.setAlignment(Qt.AlignCenter)
        self.address_bar = QLineEdit()
        self.address_bar.setObjectName("AddressBar")
        self.address_bar.setPlaceholderText("Search or enter web address")
        self.address_bar.setFrame(False)
        self.address_bar.installEventFilter(self)
        self.address_bar.returnPressed.connect(self.navigate_to_url)
        self.address_bar.textEdited.connect(self._on_address_typed)
        self.lock_label = QLabel("🔒")
        self.lock_label.setFixedSize(16, 18)
        self.lock_label.setAlignment(Qt.AlignCenter)
        self.lock_label.setVisible(False)
        self.lock_label.setCursor(Qt.PointingHandCursor)
        self.lock_label.setToolTip("Website identification and permissions")
        self.lock_label.installEventFilter(self)
        self.addr_drop = QToolButton()
        self.addr_drop.setObjectName("AddressDrop")
        self.addr_drop.setText("▾")
        self.addr_drop.setToolTip("View recent sites")
        self.addr_drop.setCursor(Qt.PointingHandCursor)
        self.addr_drop.clicked.connect(self.show_address_dropdown)
        ah.addWidget(self.favicon_label)
        ah.addWidget(self.address_bar, 1)
        ah.addWidget(self.lock_label)
        self.feed_btn = QToolButton(); self.feed_btn.setText("◔"); self.feed_btn.setToolTip("View this feed"); self.feed_btn.setVisible(False)
        self.feed_btn.clicked.connect(self.open_discovered_feed)
        ah.addWidget(self.feed_btn)
        ah.addWidget(self.addr_drop)
        ar.addWidget(self.address_frame, 1)

        self.refresh_btn = QToolButton()
        self.refresh_btn.setObjectName("CommandButton")
        self.refresh_btn.setText("⟳")
        self.refresh_btn.setFixedSize(32, 28)
        self.refresh_btn.setToolTip("Refresh (F5)")
        self.refresh_btn.clicked.connect(self.reload_page)
        ar.addWidget(self.refresh_btn)

        # ---- Bing search bar, beside the URL bar ----
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("SearchBar")
        self.search_bar.setPlaceholderText("Search with Bing...")
        self.search_bar.setFixedWidth(230)
        self.search_bar.setFixedHeight(30)
        self.search_bar.installEventFilter(self)
        self.search_bar.returnPressed.connect(self.search_bing)
        self.search_bar.textEdited.connect(self._on_search_typed)
        self.search_btn = QToolButton()
        self.search_btn.setObjectName("CommandButton")
        self.search_btn.setText("⌕")
        self.search_btn.setFixedSize(30, 30)
        self.search_btn.setToolTip("Search with Bing")
        self.search_btn.clicked.connect(self.search_bing)
        ar.addWidget(self.search_bar)
        ar.addWidget(self.search_btn)
        col.addWidget(addr_row)

        # ---- Tab strip (UNDER the URL bar, IE11 style) ----
        # Home / Favorites / Tools / Feedback sit at the right end of this row,
        # exactly like real IE11.
        tabstrip = QWidget()
        tabstrip.setObjectName("TabStrip")
        ts = QHBoxLayout(tabstrip)
        ts.setContentsMargins(8, 3, 8, 4)
        ts.setSpacing(3)
        self.tabbar = QTabBar()
        self.tabbar.setTabsClosable(True)
        self.tabbar.setMovable(True)
        self.tabbar.setExpanding(False)
        self.tabbar.setDrawBase(False)
        self.tabbar.setElideMode(Qt.ElideRight)
        self.tabbar.currentChanged.connect(self.on_tab_changed)
        self.tabbar.tabCloseRequested.connect(self.close_tab)
        self.tabbar.tabMoved.connect(self.on_tab_moved)
        self.tabbar.tabBarDoubleClicked.connect(
            lambda idx: self.new_tab() if idx < 0 else None)
        ts.addWidget(self.tabbar, 0)
        self.new_tab_btn = QToolButton()
        self.new_tab_btn.setObjectName("CommandButton")
        self.new_tab_btn.setToolTip("New tab (Ctrl+T)")
        self.new_tab_btn.setFixedSize(26, 24)
        self.new_tab_btn.setFocusPolicy(Qt.NoFocus)
        self.new_tab_btn.clicked.connect(self.new_tab)
        self.update_new_tab_icon()
        ts.addWidget(self.new_tab_btn, 0)
        ts.addStretch(1)

        self.home_btn = QToolButton()
        self.home_btn.setObjectName("CommandButton")
        self.home_btn.setText("⌂")
        self.home_btn.setFixedSize(34, 28)
        self.home_btn.setToolTip("Go to your home page (Alt+Home)")
        self.home_btn.clicked.connect(lambda: self.navigate(HOME_URL))
        ar.addWidget(self.home_btn)

        self.star_btn = QToolButton()
        self.star_btn.setObjectName("CommandButton")
        self.star_btn.setText("★")
        self.star_btn.setFixedSize(34, 28)
        self.star_btn.setToolTip("View your favorites")
        self.star_btn.setStyleSheet(
            "QToolButton { color:#D89B00; } QToolButton:hover { color:#B37700; }")
        self.star_btn.clicked.connect(self.toggle_favorites_center)
        ar.addWidget(self.star_btn)

        self.tools_btn = QToolButton()
        self.tools_btn.setObjectName("CommandButton")
        self.tools_btn.setText("⚙")
        self.tools_btn.setFixedSize(34, 28)
        self.tools_btn.setToolTip("Tools")
        self.tools_btn.setPopupMode(QToolButton.InstantPopup)
        ar.addWidget(self.tools_btn)

        self.smile_btn = QToolButton()
        self.smile_btn.setObjectName("CommandButton")
        self.smile_btn.setText("🙂")
        self.smile_btn.setFixedSize(34, 28)
        self.smile_btn.setToolTip("Give feedback")
        self.smile_btn.setPopupMode(QToolButton.InstantPopup)
        smile_menu = QMenu(self)
        self.action(smile_menu, "Send a smile",
                    lambda: QMessageBox.information(self, "Feedback", "Thanks for the smile!"))
        self.action(smile_menu, "Send a frown",
                    lambda: QMessageBox.information(self, "Feedback", "Thanks for the feedback."))
        self.smile_btn.setMenu(smile_menu)
        ar.addWidget(self.smile_btn)
        col.addWidget(tabstrip)

        # ---- Favorites bar (the bookmark bar) ----
        self.fav_bar = FavoritesBar(self)
        self.fav_bar.setObjectName("FavoritesBar")
        self.fav_bar.setFixedHeight(30)
        fb = QHBoxLayout(self.fav_bar)
        fb.setContentsMargins(8, 1, 8, 1)
        fb.setSpacing(2)
        add_btn = QToolButton()
        add_btn.setObjectName("FavBarLink")
        add_btn.setText("☆ Add to favorites")
        add_btn.setToolTip("Add the current page to your favorites")
        add_btn.setPopupMode(QToolButton.InstantPopup)
        add_menu = QMenu(add_btn)
        self.action(add_menu, "Add to Favorites…", self.add_favorite)
        self.action(add_menu, "Organize favorites…", self.toggle_favorites_center)
        add_menu.addSeparator()
        self.action(add_menu, "Import and export…", self.import_export_info)
        add_btn.setMenu(add_menu)
        fb.addWidget(add_btn)
        self.fav_links = QHBoxLayout()
        self.fav_links.setSpacing(2)
        fb.addLayout(self.fav_links, 1)
        self.rebuild_favorites_bar()
        col.addWidget(self.fav_bar)
        self.infobar = InfoBar(toolbar)
        col.addWidget(self.infobar)
        main.addWidget(toolbar)

        # ---- Suggestions dropdown (instant: no debounce, no window churn) ----
        self.suggest_popup = SuggestionPopup(self)
        self._suggest_cache = {}
        self._suggest_cache_order = []
        self._suggest_worker = SuggestWorker(self)
        self._suggest_worker.start()

        # ---- Content: Favorites Center pane + pages ----
        self.fav_center = self._build_favorites_center()
        self.stack = QStackedWidget()
        content = QWidget()
        cl = QHBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.addWidget(self.fav_center)
        cl.addWidget(self.stack, 1)
        main.addWidget(content, 1)
        self.setCentralWidget(central)

        # ---- Status bar: link preview | progress | zone | zoom ----
        self.status = QStatusBar()
        self.status_label = QLabel("Done")
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(140)
        self.progress.setMaximumHeight(10)
        self.progress.setRange(0, 100)
        self.progress.hide()
        self.zone_label = QLabel("Internet | Protected Mode: On")
        self.zoom_btn = QPushButton("100%")
        self.zoom_btn.setObjectName("ZoomButton")
        self.zoom_btn.setToolTip("Change zoom level")
        self.zoom_btn.setMenu(self._build_zoom_menu())
        self.status.addWidget(self.status_label, 1)
        self.status.addPermanentWidget(self.progress)
        self.status.addPermanentWidget(self.zone_label)
        self.status.addPermanentWidget(self.zoom_btn)
        self.setStatusBar(self.status)
        self.status.setContextMenuPolicy(Qt.CustomContextMenu)
        self.status.customContextMenuRequested.connect(self.status_context_menu)

        # ---- Hidden classic menu bar (File / View / Favorites / Tools / Help) ----
        self._build_menu_bar()

        # ---- Keyboard shortcuts ----
        self._shortcuts = []
        self.add_shortcut("Ctrl+L", self.focus_address)
        self.add_shortcut("Ctrl+O", self.open_local_file)
        self.add_shortcut("Alt+D", self.focus_address)
        self.add_shortcut("Ctrl+E", self.focus_search)
        self.add_shortcut("Ctrl+T", self.new_tab)
        self.add_shortcut("Ctrl+W", lambda: self.close_tab(self.tabbar.currentIndex()))
        self.add_shortcut("Ctrl+Shift+T", self.reopen_closed_tab)
        self.add_shortcut("Ctrl+N", lambda: self.add_tab(NEW_TAB_URL))
        self.add_shortcut("Ctrl+R", self.reload_page)
        self.add_shortcut("Ctrl+D", self.add_favorite)
        self.add_shortcut("Ctrl+S", self.save_page)
        self.add_shortcut("Ctrl+P", self.print_to_pdf)
        self.add_shortcut("F5", self.reload_page)
        self.add_shortcut("Esc", self._escape_pressed)
        self.add_shortcut("F11", self.toggle_fullscreen)
        self.add_shortcut("Ctrl+J", self.show_downloads)
        self.add_shortcut("Ctrl+H", self.show_history)
        self.add_shortcut("Ctrl+F", self.find_on_page)
        self.add_shortcut("F12", self.open_devtools)
        self.add_shortcut("Ctrl+Shift+I", self.open_devtools)
        self.add_shortcut("Ctrl+Plus", lambda: self.zoom(1.1))
        self.add_shortcut("Ctrl+Equal", lambda: self.zoom(1.1))
        self.add_shortcut("Ctrl+Minus", lambda: self.zoom(0.9))
        self.add_shortcut("Ctrl+0", lambda: self.set_zoom(1.0))
        self.add_shortcut("Ctrl+Tab", self.next_tab)
        self.add_shortcut("Ctrl+Shift+Tab", self.previous_tab)
        self.add_shortcut("Ctrl+PageDown", self.next_tab)
        self.add_shortcut("Ctrl+PageUp", self.previous_tab)
        self.add_shortcut("Alt+Left", self.go_back)
        self.add_shortcut("Alt+Right", self.go_forward)
        self.add_shortcut("Alt+Home", lambda: self.navigate(HOME_URL))
        self.add_shortcut("Alt+Down", self.show_address_dropdown)
        self.add_shortcut("Alt+M", self.toggle_menu_bar)
        self.add_shortcut("Alt+Space", lambda: self.show_system_menu())
        self.add_shortcut("Ctrl+Q", self.show_quick_tabs)
        self.add_shortcut("F7", self.toggle_caret_browsing)
        self.add_shortcut("Ctrl+Shift+N", self.new_private_tab)

        # Tools menu last: it inspects fav_bar/_menubar, which now exist.
        self.tools_btn.setMenu(self.create_tools_menu())

    def _build_favorites_center(self):
        pane = QWidget()
        pane.setObjectName("FavoritesCenter")
        pane.setFixedWidth(250)
        v = QVBoxLayout(pane)
        v.setContentsMargins(6, 6, 6, 6)
        v.setSpacing(6)
        top = QHBoxLayout()
        refresh_small = QToolButton()
        refresh_small.setObjectName("FavBarLink")
        refresh_small.setText("⟳")
        refresh_small.setToolTip("Refresh")
        refresh_small.clicked.connect(self.refresh_favorites_center)
        top.addWidget(refresh_small)
        top.addStretch(1)
        add_center = QToolButton()
        add_center.setObjectName("FavBarLink")
        add_center.setText("Add to favorites")
        add_center.setPopupMode(QToolButton.InstantPopup)
        am = QMenu(add_center)
        self.action(am, "Add to Favorites…", self.add_favorite)
        self.action(am, "Organize favorites…", self.toggle_favorites_center)
        add_center.setMenu(am)
        top.addWidget(add_center)
        v.addLayout(top)
        self.center_tabs = QTabWidget()
        self.fav_tree = QTreeWidget()
        self.fav_tree.setHeaderHidden(True)
        self.fav_tree.itemDoubleClicked.connect(self._fav_tree_open)
        self.fav_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.fav_tree.customContextMenuRequested.connect(self._fav_tree_menu)
        self.feed_list = QListWidget()
        self.feed_list.addItem("This page has no feeds.\n\nFeeds let you follow updates from your favorite websites.")
        self.feed_list.itemDoubleClicked.connect(lambda item: self.navigate(item.data(Qt.UserRole)) if item.data(Qt.UserRole) else None)
        self.hist_tree = QTreeWidget()
        self.hist_tree.setHeaderHidden(True)
        self.hist_tree.itemDoubleClicked.connect(
            lambda item, col=0: self.navigate(item.data(0, Qt.UserRole)))
        self.center_tabs.addTab(self.fav_tree, "Favorites")
        self.center_tabs.addTab(self.feed_list, "Feeds")
        self.center_tabs.addTab(self.hist_tree, "History")
        v.addWidget(self.center_tabs, 1)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        sugg = QPushButton("Turn on Suggested Sites...")
        sugg.clicked.connect(self.suggested_sites_info)
        bottom.addWidget(sugg)
        v.addLayout(bottom)
        pane.setVisible(False)
        return pane

    def _build_menu_bar(self):
        mb = self.menuBar()
        mb.setVisible(False)
        m_file = mb.addMenu("File")
        self.action(m_file, "New tab\tCtrl+T", lambda: self.add_tab(NEW_TAB_URL))
        self.action(m_file, "Open location...\tCtrl+L", self.focus_address)
        self.action(m_file, "Open...\tCtrl+O", self.open_local_file)
        offline = self.action(m_file, "Work Offline", self.toggle_offline)
        offline.setCheckable(True); offline.setChecked(self.offline)
        self.action(m_file, "Save page as...\tCtrl+S", self.save_page)
        m_file.addSeparator()
        self.action(m_file, "Close tab\tCtrl+W", lambda: self.close_tab(self.tabbar.currentIndex()))
        self.action(m_file, "Exit", self.close)
        m_view = mb.addMenu("View")
        self.action(m_view, "Refresh\tF5", self.reload_page)
        self.action(m_view, "Full screen\tF11", self.toggle_fullscreen)
        m_view.addSeparator()
        self._mb_favbar = self.action(m_view, "Favorites bar", self.toggle_favorites_bar)
        self._mb_favbar.setCheckable(True)
        self._mb_favbar.setChecked(True)
        self._mb_menubar = self.action(m_view, "Menu bar", self.toggle_menu_bar)
        self._mb_menubar.setCheckable(True)
        m_view.addAction(self._mb_favbar)
        m_view.addAction(self._mb_menubar)
        m_fav = mb.addMenu("Favorites")
        m_fav.aboutToShow.connect(lambda: self.refresh_favorites_menu(m_fav))
        m_tools = mb.addMenu("Tools")
        self.action(m_tools, "Developer Tools\tF12", self.open_devtools)
        self.action(m_tools, "View downloads\tCtrl+J", self.show_downloads)
        self.action(m_tools, "History\tCtrl+H", self.show_history)
        m_tools.addSeparator()
        self.action(m_tools, "Delete browsing history...", self.clear_browsing_data)
        self.action(m_tools, "Internet options", self.internet_options)
        self.action(m_tools, "Compatibility View settings", self.compatibility_info)
        self.action(m_tools, "Toggle dark mode", self.toggle_dark_mode)
        m_help = mb.addMenu("Help")
        self.action(m_help, "About Internet Explorer", self.about)
        self._menubar = mb

    def _build_zoom_menu(self):
        menu = QMenu(self)
        for pct in (25, 50, 75, 90, 100, 110, 125, 150, 175, 200, 250, 300, 350, 400):
            act = QAction(f"{pct}%", menu)
            act.triggered.connect(lambda checked=False, v=pct: self.set_zoom(v / 100.0))
            menu.addAction(act)
        return menu

    # ------------------------------------------------------------------
    # Tabs (QTabBar + QStackedWidget so the address row sits above)
    # ------------------------------------------------------------------
    def on_tab_changed(self, idx):
        if idx >= 0:
            self.stack.setCurrentIndex(idx)
        self.sync_current_tab(idx)

    def on_tab_moved(self, frm, to):
        w = self.stack.widget(frm)
        self.stack.removeWidget(w)
        self.stack.insertWidget(to, w)
        self.stack.setCurrentIndex(self.tabbar.currentIndex())
    def update_new_tab_icon(self):
        icon = load_newtab_icon()
        if icon and hasattr(self, "new_tab_btn"):
            self.new_tab_btn.setIcon(icon)
            self.new_tab_btn.setIconSize(QSize(18, 18))
            self.new_tab_btn.setText("")
        elif hasattr(self, "new_tab_btn"):
            self.new_tab_btn.setIcon(QIcon())
            self.new_tab_btn.setText("+")

    def new_tab(self):
        """User-initiated new tab (Ctrl+T, + button): IE11 focused the
        address bar so you can start typing immediately."""
        self.add_tab(NEW_TAB_URL, focus_address=True)

    def add_tab(self, url=NEW_TAB_URL, focus_address=False, is_private=False, background=False):
        tab = BrowserTab(self, url, is_private=is_private)
        idx = self.stack.addWidget(tab)
        self.tabbar.addTab("[InPrivate] New tab" if is_private else "New tab")
        if is_private:
            self.tabbar.setTabTextColor(idx, QColor("#6b3a91"))
        if not background: self.tabbar.setCurrentIndex(idx)
        self.update_new_tab_icon()
        if focus_address:
            self.focus_address()

    def create_popup_page(self, background=True):
        """Backend popup hook; background preserves the originating tab focus."""
        current = self.tabbar.currentIndex()
        self.add_tab(NEW_TAB_URL, background=background)
        page = self.stack.widget(self.stack.count()-1).page
        if background and current >= 0: self.tabbar.setCurrentIndex(current)
        return page

    def popup_blocked(self, site):
        """Called by a backend popup callback when it rejects a script popup."""
        host = QUrl(site).host() or site
        self._play_sound("popup")
        self.infobar.show_message("Internet Explorer blocked a pop-up from %s." % host, [], [("Always allow pop-ups from this site", lambda h=host: self._allow_popup(h)), ("Settings", self.popup_settings)])

    # ------------------------------------------------------------------
    # Link and permission interpretation
    # ------------------------------------------------------------------
    @staticmethod
    def _url_from_callback(args):
        """Extract a URL from the several callback shapes used by WebView2."""
        for value in args:
            if isinstance(value, QUrl) and value.isValid(): return value
            for attr in ("url", "requestedUrl", "targetUrl", "uri"):
                candidate = getattr(value, attr, None)
                try:
                    candidate = candidate() if callable(candidate) else candidate
                    result = candidate if isinstance(candidate, QUrl) else QUrl(str(candidate))
                    if result.isValid() and result.scheme(): return result
                except Exception: pass
            try:
                result=QUrl(str(value))
                if result.isValid() and result.scheme() in ("http","https"): return result
            except Exception: pass
        return QUrl()

    def interpret_link(self, *args):
        """Route target=_blank/window.open callbacks into our own tab stack.

        This prevents Bing redirect cards from falling through to the OS default
        browser (Zen or any other registered handler).
        """
        url=self._url_from_callback(args)
        if url.scheme() not in ("http", "https"): return
        # Mark the WebView2 event handled before opening our tab, otherwise its
        # default behavior may still invoke the Windows HTTP association.
        for event in args:
            for name in ("cancel", "setHandled", "set_handled"):
                method=getattr(event,name,None)
                if callable(method):
                    try: method(True) if name != "cancel" else method(); break
                    except Exception: pass
            try: event.handled=True
            except Exception: pass
        source=self.current_tab()
        # Script-created popups stay protected unless the host was allowed.
        host=url.host().lower()
        if any("popup" in type(v).__name__.lower() for v in args) and host not in self.popup_whitelist:
            self.popup_blocked(url.toString()); return
        self.add_tab(url.toString(), background=True, is_private=bool(source and source.is_private))

    def open_new_window_url(self, url):
        """GUI-thread endpoint for qtwebview2's new_window_handler."""
        parsed = QUrl(str(url))
        if parsed.scheme() not in ("http", "https"):
            self.status_label.setText("Blocked unsupported external link")
            return
        source = self.current_tab()
        self.add_tab(parsed.toString(), background=True,
                     is_private=bool(source and source.is_private))

    def _install_link_interpreter(self, tab):
        """Fallback for runtimes without a new-window callback.

        Captured target=_blank links are opened in a browser tab and ordinary
        popup attempts are retained in this browser rather than delegated to
        Windows.  It is intentionally best-effort and harmless on CSP pages.
        """
        script = """(function(){if(window.__ieLinkInterpreter)return;window.__ieLinkInterpreter=1;
        document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[href]');
        if(a&&a.target&&a.target!=='_self'){a.target='_self';}},true);
        var oldOpen=window.open; window.open=function(u){if(u){location.href=String(u);return window;}return oldOpen.apply(window,arguments);};})();"""
        try: tab.view.widget.eval_js(script)
        except Exception: pass

    def interpret_permission(self, *args):
        url=self._url_from_callback(args); host=url.host() or (self.current_view().url().host() if self.current_view() else "this site")
        feature="location"
        for value in args:
            text=str(value).lower()
            if "camera" in text: feature="camera"
            elif "microphone" in text: feature="microphone"
            elif "notification" in text: feature="notifications"
        key=(host.lower()+":"+feature)
        request=next((value for value in args if any(hasattr(value,n) for n in ("accept","grant","deny","reject"))),None)
        if self.site_permissions.get(key) == "allow": self._answer_permission(request, True); return
        if self.site_permissions.get(key) == "block": self._answer_permission(request, False); return
        self.show_permission_infobar(host, feature, request, key)

    def show_permission_infobar(self, host, feature, request=None, key=None):
        key=key or (host.lower()+":"+feature)
        self.infobar.show_message("%s wants to use your %s." % (host, feature),
            [("Allow", lambda: self._store_permission(key, request, True)), ("Block", lambda: self._store_permission(key, request, False))],
            [("Always allow", lambda: self._store_permission(key, request, True)), ("Always block", lambda: self._store_permission(key, request, False))])

    def _answer_permission(self, request, allow):
        if request is None: return
        for name in (("accept","grant","allow") if allow else ("deny","reject","block")):
            method=getattr(request,name,None)
            if callable(method):
                try: method(); return
                except Exception: pass
    def _store_permission(self, key, request, allow):
        self.site_permissions[key]="allow" if allow else "block"; self._answer_permission(request,allow); self.save_state(); self.infobar.hide()
    def _allow_popup(self, host):
        if host not in self.popup_whitelist: self.popup_whitelist.append(host); self.save_state()
        self.infobar.hide()
    def popup_settings(self):
        dialog=QDialog(self); dialog.setWindowTitle("Pop-up Blocker Settings"); dialog.setWindowIcon(self.windowIcon()); v=QVBoxLayout(dialog); listing=QListWidget(); v.addWidget(QLabel("Allowed sites:")); v.addWidget(listing)
        def fill():
            listing.clear(); listing.addItems(self.popup_whitelist)
        remove=QPushButton("Remove selected"); remove.clicked.connect(lambda: (self.popup_whitelist.remove(listing.currentItem().text()) if listing.currentItem() and listing.currentItem().text() in self.popup_whitelist else None, fill(), self.save_state()))
        close=QPushButton("Close"); close.clicked.connect(dialog.accept); row=QHBoxLayout(); row.addWidget(remove); row.addStretch(); row.addWidget(close); v.addLayout(row); fill(); dialog.exec_()

    def close_tab(self, index):
        if index < 0 or index >= self.tabbar.count():
            return
        w = self.stack.widget(index)
        if isinstance(w, BrowserTab):
            url = w.view.url().toString()
            if url and not url.startswith("about:"):
                self.closed_tabs.append(url)
                self.closed_tabs = self.closed_tabs[-20:]
        self.tabbar.blockSignals(True)
        self.tabbar.removeTab(index)
        self.stack.removeWidget(w)
        self.tabbar.blockSignals(False)
        w.deleteLater()
        if self.tabbar.count() == 0:
            self.add_tab(NEW_TAB_URL)
        else:
            self.stack.setCurrentIndex(self.tabbar.currentIndex())
            self.sync_current_tab(self.tabbar.currentIndex())
        self.update_new_tab_icon()

    def reopen_closed_tab(self):
        if self.closed_tabs:
            self.add_tab(self.closed_tabs.pop())
        else:
            self.status_label.setText("No recently closed tabs")

    def next_tab(self):
        count = self.tabbar.count()
        if count > 1:
            self.tabbar.setCurrentIndex((self.tabbar.currentIndex() + 1) % count)

    def previous_tab(self):
        count = self.tabbar.count()
        if count > 1:
            self.tabbar.setCurrentIndex((self.tabbar.currentIndex() - 1) % count)

    def current_tab(self):
        idx = self.tabbar.currentIndex()
        if idx < 0:
            return None
        w = self.stack.widget(idx)
        return w if isinstance(w, BrowserTab) else None

    def current_view(self):
        tab = self.current_tab()
        return tab.view if tab else None

    # ------------------------------------------------------------------
    # Tab events
    # ------------------------------------------------------------------
    def sync_current_tab(self, _idx=0):
        tab = self.current_tab()
        if not tab:
            self.address_bar.clear()
            self.setWindowTitle("Internet Explorer")
            return
        url = tab.view.url()
        self.address_bar.setText("" if tab.is_custom_new_tab else url.toString())
        self.lock_label.setVisible(url.scheme() == "https")
        icon = tab.view.icon()
        if icon and not icon.isNull():
            self.favicon_label.setPixmap(icon.pixmap(16, 16))
            self.favicon_label.setText("")
        else:
            self.favicon_label.setPixmap(QPixmap())
            self.favicon_label.setText("🌐")
        self.update_navigation_state()
        self.update_zone_label(url)
        title = (tab.view.title() or "").strip()
        self.setWindowTitle((title + " - Internet Explorer") if title else "Internet Explorer")
        self.status_label.setText("Done")

    def on_url_changed(self, tab, url):
        if url.scheme() == "ie11-error":
            action = url.path() or url.toString().split(":", 1)[-1]
            if "refresh" in action: tab.view.setUrl(QUrl(tab.failed_url)); return
            if "diagnose" in action: self.diagnose_connection(); return
            if "more" in action: QMessageBox.information(self, "More information", tab.error_detail or "The webpage could not be reached."); return
        if tab.is_custom_new_tab and url.scheme() in ("http", "https"):
            tab.is_custom_new_tab = False
        if url.scheme() in ("http", "https"):
            self._play_sound("click")
            self._apply_site_zoom(tab, url)
        if tab is self.current_tab():
            self.address_bar.setText("" if tab.is_custom_new_tab else url.toString())
            self.lock_label.setVisible(url.scheme() == "https")
            self.update_zone_label(url)
            self.update_navigation_state()

    def on_title_changed(self, tab, title):
        index = self.stack.indexOf(tab)
        if index >= 0:
            label = "New tab" if (isinstance(tab, BrowserTab) and tab.is_custom_new_tab) \
                else (title.strip() or "New tab")
            self._paint_loading_tab(tab)
            if tab is self.current_tab():
                self.setWindowTitle((label + " - Internet Explorer") if label else "Internet Explorer")

    def on_load_progress(self, tab, progress):
        if progress < 100 and not tab.loading:
            tab.loading = True; tab.loading_frame = 0; tab.slow_timer = QTimer(tab); tab.slow_timer.setSingleShot(True)
            tab.slow_timer.timeout.connect(lambda t=tab: self._show_slow_infobar(t)); tab.slow_timer.start(20000)
        self._paint_loading_tab(tab)
        if tab is self.current_tab():
            self.progress.show()
            self.progress.setValue(progress)
            self.status_label.setText(f"Opening page… {progress}%")

    def on_load_finished(self, tab, ok):
        tab.loading = False
        if hasattr(tab, "slow_timer"): tab.slow_timer.stop()
        self._paint_loading_tab(tab)
        if self.infobar.isVisible() and getattr(self, "_slow_tab", None) is tab: self.infobar.hide()
        if tab is self.current_tab():
            self.progress.hide()
            self.status_label.setText("Done" if ok else "Internet Explorer cannot display the webpage")
            self.update_navigation_state()
        if ok:
            if tab is self.current_tab() and not self._first_load: self._play_sound("complete")
            self._first_load = False
            self._install_link_interpreter(tab)
            self.discover_feed(tab)
            url = tab.view.url().toString()
            if url and not url.startswith("about:") and not tab.is_private:
                self.history.append((tab.view.title() or url, url))
                self.history = self.history[-500:]
                self.save_state()
        # qtwebview2 reports some successful navigations with a completion
        # enum that is not PageLoadEvent.Finished.  Only replace the page when
        # a backend supplied an actual error string; otherwise leave Chromium's
        # document in place instead of turning every page into an error page.
        elif getattr(tab, "error_detail", "") and not tab.is_custom_new_tab and tab.view.url().scheme() not in ("file", "about", "ie11-error"):
            tab.failed_url = tab.view.url().toString(); tab.error_detail = "The network request failed or the rendering process ended."
            tab.view.setHtml(build_error_html(tab.failed_url)); self.address_bar.setText(tab.failed_url)

    def on_icon_changed(self, tab, icon):
        if tab is self.current_tab():
            if icon and not icon.isNull():
                self.favicon_label.setPixmap(icon.pixmap(16, 16))
                self.favicon_label.setText("")
            else:
                self.favicon_label.setPixmap(QPixmap())
                self.favicon_label.setText("🌐")

    def on_link_hovered(self, tab, url):
        """The nostalgic bottom-left link preview."""
        if tab is self.current_tab():
            self.status_label.setText(url if url else "Done")

    def update_navigation_state(self):
        view = self.current_view()
        can_back = bool(view and view.history().canGoBack())
        can_fwd = bool(view and view.history().canGoForward())
        self.back_btn.setEnabled(can_back)
        self.back_drop.setEnabled(can_back)
        self.forward_btn.setEnabled(can_fwd)
        self.forward_drop.setEnabled(can_fwd)
        self.update_zoom_label()

    def update_zone_label(self, url=None):
        if self.offline:
            self.zone_label.setText("Work Offline")
            return
        scheme = (url or (self.current_view().url() if self.current_view() else QUrl())).scheme()
        if scheme == "file":
            self.zone_label.setText("Local intranet | Protected Mode: Off")
        else:
            self.zone_label.setText("Internet | Protected Mode: On")

    def update_zoom_label(self):
        view = self.current_view()
        pct = int(round(view.zoomFactor() * 100)) if view else 100
        self.zoom_btn.setText(f"{pct}%")

    def status_context_menu(self, pos):
        menu = QMenu(self)
        mb = self.action(menu, "Menu bar", self.toggle_menu_bar); mb.setCheckable(True); mb.setChecked(self._menubar.isVisible())
        fb = self.action(menu, "Favorites bar", self.toggle_favorites_bar); fb.setCheckable(True); fb.setChecked(self.fav_bar.isVisible())
        sb = self.action(menu, "Status bar", lambda: self.status.setVisible(not self.status.isVisible())); sb.setCheckable(True); sb.setChecked(self.status.isVisible())
        menu.exec_(self.status.mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def go_back(self):
        view = self.current_view()
        if view:
            view.back()

    def go_forward(self):
        view = self.current_view()
        if view:
            view.forward()

    def reload_page(self):
        view = self.current_view()
        if view:
            view.reload()

    def navigate_to_url(self):
        text = self.address_bar.text().strip()
        if not text:
            return
        if " " in text and "://" not in text:
            self.navigate(BING_SEARCH_URL + quote_plus(text))
        else:
            if not text.startswith(("http://", "https://", "file://", "about:")):
                text = "https://" + text
            self.navigate(text)
        # IE11 kept focus in the address box after navigating — do the same.
        self.address_bar.setFocus()
        self.address_bar.selectAll()

    def navigate(self, url):
        if self.suggest_popup.isVisible():
            self.dismiss_suggestions()
        view = self.current_view()
        if view:
            if self.offline and str(url).startswith(("http://", "https://")):
                tab = self.current_tab(); tab.failed_url = str(url); tab.error_detail = "Work Offline is enabled."
                view.setHtml(build_error_html(str(url))); self.address_bar.setText(str(url)); return
            view.setUrl(QUrl(url))

    def search_bing(self):
        query = self.search_bar.text().strip()
        if query:
            self.navigate(BING_SEARCH_URL + quote_plus(query))
            self.focus_search()

    def focus_address(self):
        self.address_bar.setFocus()
        self.address_bar.selectAll()

    def focus_search(self):
        self.search_bar.setFocus()
        self.search_bar.selectAll()

    def page_context_menu(self, tab, pos):
        view = tab.view
        menu = QMenu(self)
        back = QAction("Back", menu)
        back.setEnabled(view.history().canGoBack())
        back.triggered.connect(view.back)
        fwd = QAction("Forward", menu)
        fwd.setEnabled(view.history().canGoForward())
        fwd.triggered.connect(view.forward)
        menu.addAction(back)
        menu.addAction(fwd)
        menu.addSeparator()
        rel = QAction("Refresh", menu)
        rel.triggered.connect(view.reload)
        menu.addAction(rel)
        menu.addSeparator()
        save = QAction("Save page as...", menu)
        save.triggered.connect(self.save_page)
        menu.addAction(save)
        prn = QAction("Print...", menu)
        prn.triggered.connect(self.print_to_pdf)
        menu.addAction(prn)
        menu.addSeparator()
        insp = QAction("Inspect element", menu)
        insp.triggered.connect(self.open_devtools)
        menu.addAction(insp)
        menu.exec_(view.mapToGlobal(pos))

    # ------------------------------------------------------------------
    # Back / Forward history dropdowns
    # ------------------------------------------------------------------
    def _history_menu(self, items, order_reverse):
        menu = QMenu(self)
        view = self.current_view()
        if not view:
            return menu
        entries = list(reversed(items)) if order_reverse else list(items)
        for it in entries:
            act = QAction(it.title() or it.url().toString(), menu)
            act.setToolTip(it.url().toString())
            act.triggered.connect(lambda checked=False, item=it: view.history().goToItem(item))
            menu.addAction(act)
        return menu

    def show_back_history(self):
        view = self.current_view()
        if not view or not view.history().canGoBack():
            return
        menu = self._history_menu(view.history().backItems(8), False)
        menu.exec_(self.back_drop.mapToGlobal(QPoint(0, self.back_drop.height())))

    def show_forward_history(self):
        view = self.current_view()
        if not view or not view.history().canGoForward():
            return
        menu = self._history_menu(view.history().forwardItems(8), True)
        menu.exec_(self.forward_drop.mapToGlobal(QPoint(0, self.forward_drop.height())))

    # ------------------------------------------------------------------
    # Bing Suggestions dropdown
    # ------------------------------------------------------------------
    def show_address_dropdown(self):
        if self.suggest_popup.isVisible():
            self.dismiss_suggestions()
            return
        self._suggest_suppressed_text = None
        self.suggest_popup.populate(self.address_bar.text(), want_bing=False)
        self.suggest_popup.show_at(self.address_frame)

    def dismiss_suggestions(self):
        """Dismiss until the user changes input or explicitly reopens it."""
        self._suggest_suppressed_text = self.suggest_popup._last_text
        self._suggest_token += 1
        self.suggest_popup.hide()

    def _on_address_typed(self, text):
        previous = getattr(self, "_address_literal", "")
        self._address_literal = text
        if self._suggest_suppressed_text is not None:
            if text == self._suggest_suppressed_text:
                return
            self._suggest_suppressed_text = None
        # Only complete additions; deletion and a selected suggestion are left alone.
        if len(text) > len(previous) and not (self.suggest_popup.isVisible() and self.suggest_popup.list.currentRow() >= 0):
            low = text.lower()
            choices = [u for _t, u in reversed(self.history)]
            for candidate in choices:
                bare = candidate.split("://", 1)[-1].rstrip("/")
                if bare.lower().startswith(low) and bare.lower() != low:
                    self.address_bar.blockSignals(True); self.address_bar.setText(bare); self.address_bar.setSelection(len(text), len(bare)-len(text)); self.address_bar.blockSignals(False); break
        if not self.suggestions_enabled:
            self.suggest_popup.hide()
            return
        stripped = text.strip()
        if not stripped:
            self._suggest_token += 1
            self.suggest_popup.hide()
            return
        if stripped == self.suggest_popup._last_text and self.suggest_popup.isVisible():
            return  # nothing changed — don't rebuild anything
        self._suggest_token += 1
        cached = self._suggest_cache_get(stripped)
        self.suggest_popup.populate(stripped, want_bing=True,
                                    pending=(cached is None), results=cached)
        self.suggest_popup.show_at(self.address_frame)
        if cached is None:
            self._suggest_worker.submit(self._suggest_token, stripped)

    def _on_search_typed(self, text):
        if self._suggest_suppressed_text is not None:
            if text == self._suggest_suppressed_text:
                return
            self._suggest_suppressed_text = None
        if not self.suggestions_enabled:
            self.suggest_popup.hide()
            return
        stripped = text.strip()
        if not stripped:
            self._suggest_token += 1
            self.suggest_popup.hide()
            return
        if stripped == self.suggest_popup._last_text and self.suggest_popup.isVisible():
            return
        self._suggest_token += 1
        cached = self._suggest_cache_get(stripped)
        self.suggest_popup.populate(stripped, want_bing=True,
                                    pending=(cached is None), results=cached)
        self.suggest_popup.show_at(self.search_bar)
        if cached is None:
            self._suggest_worker.submit(self._suggest_token, stripped)

    

    def _suggest_cache_get(self, query):
        cache = getattr(self, "_suggest_cache", None)
        if cache is None:
            return None
        return cache.get(query.lower())

    def _suggest_cache_put(self, query, results):
        cache = getattr(self, "_suggest_cache", None)
        order = getattr(self, "_suggest_cache_order", None)
        if cache is None or order is None:
            return
        key = query.lower()
        if key in order:
            order.remove(key)
        order.append(key)
        cache[key] = results
        while len(order) > 60:
            cache.pop(order.pop(0), None)

    

    def _on_suggestions(self, token, query, results):
        # Cache successful results even if the user kept typing, so going
        # back to that prefix shows them instantly.
        if results is not None:
            self._suggest_cache_put(query, results)
        if token != self._suggest_token:
            return
        if not self.suggest_popup.isVisible():
            return
        self.suggest_popup.apply_results(query, results)


    def set_suggestions_enabled(self, enabled):
        self.suggestions_enabled = enabled
        self.save_state()
        if hasattr(self, "suggest_action"):
            self.suggest_action.setText("Turn off suggestions" if enabled else "Turn on suggestions")
        self.status_label.setText(
            "Suggestions: on — addresses are sent to Bing as you type" if enabled
            else "Suggestions: off — keystrokes are no longer sent to Bing")
        if not enabled:
            self.suggest_popup.hide()

    def toggle_suggestions(self):
        self.set_suggestions_enabled(not self.suggestions_enabled)

    # ------------------------------------------------------------------
    # Favorites bar + Favorites Center
    # ------------------------------------------------------------------
    def rebuild_favorites_bar(self):
        while self.fav_links.count():
            item = self.fav_links.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for title, url in self.favorites[:12]:
            btn = QToolButton()
            btn.setObjectName("FavBarLink")
            btn.setText(title.replace("🌐", "").strip() or title)
            btn.setToolTip(url)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, target=url: self.navigate(target))
            self.fav_links.addWidget(btn)
        self.fav_links.addStretch(1)

    def toggle_favorites_center(self):
        visible = not self.fav_center.isVisible()
        self.fav_center.setVisible(visible)
        if visible:
            self.refresh_favorites_center()

    def toggle_favorites_bar(self):
        self.fav_bar.setVisible(not self.fav_bar.isVisible())
        if hasattr(self, "favbar_action"):
            self.favbar_action.setChecked(self.fav_bar.isVisible())
        if hasattr(self, "_mb_favbar"):
            self._mb_favbar.setChecked(self.fav_bar.isVisible())

    def toggle_menu_bar(self):
        self._menubar.setVisible(not self._menubar.isVisible())
        if hasattr(self, "menubar_action"):
            self.menubar_action.setChecked(self._menubar.isVisible())
        if hasattr(self, "_mb_menubar"):
            self._mb_menubar.setChecked(self._menubar.isVisible())

    def refresh_favorites_center(self):
        self.fav_tree.clear()
        links = QTreeWidgetItem(["📁  Links"])
        self.fav_tree.addTopLevelItem(links)
        for title, url in self.favorites:
            child = QTreeWidgetItem([title])
            child.setData(0, Qt.UserRole, url)
            child.setToolTip(0, url)
            links.addChild(child)
        links.setExpanded(True)
        self.hist_tree.clear()
        today = QTreeWidgetItem(["Today"])
        self.hist_tree.addTopLevelItem(today)
        for title, url in reversed(self.history[-200:]):
            child = QTreeWidgetItem([f"{title}  —  {url}"])
            child.setData(0, Qt.UserRole, url)
            child.setToolTip(0, url)
            today.addChild(child)
        today.setExpanded(True)

    def _fav_tree_open(self, item, _col):
        url = item.data(0, Qt.UserRole)
        if url:
            self.navigate(url)

    def _fav_tree_menu(self, pos):
        item = self.fav_tree.itemAt(pos)
        if item is None or item.parent() is None:
            return
        url = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        self.action(menu, "Open", lambda: self.navigate(url))
        self.action(menu, "Delete", lambda: self._delete_favorite(url))
        menu.exec_(self.fav_tree.mapToGlobal(pos))

    def _delete_favorite(self, url):
        self.favorites = [(t, u) for (t, u) in self.favorites if u != url]
        self.save_state()
        self.rebuild_favorites_bar()
        self.refresh_favorites_center()

    def add_favorite(self):
        view = self.current_view()
        if not view:
            return
        default_title = view.title() or view.url().host() or "Favorite"
        title, ok = QInputDialog.getText(self, "Add to Favorites", "Name:", text=default_title)
        if ok and title.strip():
            self.favorites.append((f"🌐  {title.strip()}", view.url().toString()))
            self.save_state()
            self.rebuild_favorites_bar()
            self.refresh_favorites_center()
            self.status_label.setText("Added to Favorites")

    def add_favorite_direct(self, title, url):
        self.favorites.append(("🌐  " + (title.strip() or url), url))
        self.save_state(); self.rebuild_favorites_bar(); self.refresh_favorites_center(); self.status_label.setText("Added to Favorites")

    # ------------------------------------------------------------------
    # IE additions: notifications, recovery, feeds, sound, and sessions
    # ------------------------------------------------------------------
    def _show_slow_infobar(self, tab):
        if tab.loading:
            self._slow_tab = tab
            self.infobar.show_message("A webpage is slowing down your browser.", [("Recover webpage", tab.view.reload)])

    def _paint_loading_tab(self, tab):
        index = self.stack.indexOf(tab)
        if index < 0: return
        title = "New tab" if tab.is_custom_new_tab else (tab.view.title().strip() or "New tab")
        if tab.is_private: title = "[InPrivate] " + title
        prefix = ["◐", "◓", "◑", "◒"][tab.loading_frame % 4] + " " if tab.loading else ""
        self.tabbar.setTabText(index, (prefix + title)[:28])
        self.tabbar.setTabToolTip(index, "%s\n%s" % (tab.view.title() or "New tab", tab.view.url().toString()))

    def _tick_loading_icons(self):
        for i in range(self.stack.count()):
            tab = self.stack.widget(i)
            if isinstance(tab, BrowserTab) and tab.loading:
                tab.loading_frame += 1; self._paint_loading_tab(tab)

    def _show_restore_infobar(self):
        self.infobar.show_message("Your last browsing session closed unexpectedly.", [("Restore session", self.restore_session)], [("Don't show again", self._dismiss_restore)])
    def _dismiss_restore(self): self.saved_session = {"tabs": [], "active": 0}; self.infobar.hide(); self.save_state()
    def restore_session(self):
        tabs = self.saved_session.get("tabs", [])
        for url in tabs:
            if url and url != HOME_URL: self.add_tab(url, background=True)
        active = min(int(self.saved_session.get("active", 0)) + 1, self.tabbar.count()-1)
        self.tabbar.setCurrentIndex(active); self.infobar.hide(); self.save_state()

    def _session_data(self):
        tabs=[]
        for i in range(self.stack.count()):
            tab=self.stack.widget(i)
            if isinstance(tab, BrowserTab) and not tab.is_private:
                u=tab.view.url().toString()
                if u and not u.startswith("about:"): tabs.append(u)
        return {"tabs":tabs, "active":self.tabbar.currentIndex()}

    def diagnose_connection(self):
        def check():
            try:
                with urlopen("http://www.msftconnecttest.com/connecttest.txt", timeout=3) as response: ok = response.read(128).decode("utf-8", "replace").strip() == "Microsoft Connect Test"
                msg = "Your Internet connection is working." if ok else "A connection was made, but the connectivity test returned an unexpected response."
            except Exception as exc: msg = "Internet connection check failed:\n" + str(exc)
            QTimer.singleShot(0, lambda: QMessageBox.information(self, "Diagnose Connection Problems", msg))
        threading.Thread(target=check, daemon=True).start()

    def new_private_tab(self): self.add_tab(NEW_TAB_URL, is_private=True, focus_address=True)
    def show_quick_tabs(self): QuickTabsDialog(self).exec_()
    def toggle_caret_browsing(self):
        wanted = not self.caret_browsing
        answer = QMessageBox.question(self, "Caret Browsing", "Do you want to turn caret browsing %s?\n\nWhen caret browsing is turned on, you can use the keyboard to move a text-insertion point through the page." % ("on" if wanted else "off"), QMessageBox.Yes|QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.caret_browsing=wanted; view=self.current_view()
            if view:
                try: view.widget.eval_js("document.body.contentEditable=%s;document.body.spellcheck=false" % ("true" if wanted else "false"))
                except Exception: pass
            self.save_state()

    def _init_sounds(self):
        self._sounds={}
        if not QSoundEffect: return
        for name, freq in (("click",760),("popup",430),("complete",920)):
            path=find_resource(name+".wav") or os.path.join(self.data_dir, name+".wav")
            if not os.path.exists(path):
                try:
                    with wave.open(path,"w") as f:
                        f.setparams((1,2,22050,0,"NONE","not compressed")); frames=bytearray()
                        for n in range(1600): frames.extend(int(8000*math.sin(2*math.pi*freq*n/22050)*(1-n/1600)).to_bytes(2,"little",signed=True))
                        f.writeframes(bytes(frames))
                except Exception: continue
            try: effect=QSoundEffect(self); effect.setSource(QUrl.fromLocalFile(path)); effect.setVolume(.22); self._sounds[name]=effect
            except Exception: pass
    def _play_sound(self, name):
        if self.sounds_enabled and name in getattr(self,"_sounds",{}):
            try: self._sounds[name].play()
            except Exception: pass

    def _apply_site_zoom(self, tab, url):
        domain=url.host().lower()
        if domain: tab.view.setZoomFactor(float(self.zoom_sites.get(domain, 1.0)))
    def discover_feed(self, tab):
        try: tab.view.widget.eval_js("(document.querySelector('link[rel~=alternate][type=\\\"application/rss+xml\\\"],link[rel~=alternate][type=\\\"application/atom+xml\\\"]')||{}).href||''", lambda url, t=tab:self._feed_found(t,url))
        except Exception: pass
    def _feed_found(self, tab, url):
        tab.feed_url=str(url or "");
        if tab is self.current_tab(): self.feed_btn.setVisible(bool(tab.feed_url))
    def open_discovered_feed(self):
        tab=self.current_tab(); url=getattr(tab,"feed_url","") if tab else ""
        if not url: return
        self.center_tabs.setCurrentIndex(1); self.fav_center.show(); self.feed_list.clear(); self.feed_list.addItem("Loading feed…")
        def load():
            try:
                import xml.etree.ElementTree as ET
                root=ET.fromstring(urlopen(url,timeout=5).read()); items=[]
                for node in root.findall('.//item')[:15] + root.findall('.//{http://www.w3.org/2005/Atom}entry')[:15]:
                    title=node.findtext('title') or node.findtext('{http://www.w3.org/2005/Atom}title') or 'Untitled'; link=node.findtext('link') or ''
                    if not link:
                        e=node.find('{http://www.w3.org/2005/Atom}link'); link=e.get('href','') if e is not None else ''
                    items.append((title,link))
                QTimer.singleShot(0,lambda:self._feed_loaded(items))
            except Exception: QTimer.singleShot(0,lambda:self._feed_loaded([]))
        threading.Thread(target=load,daemon=True).start()
    def _feed_loaded(self, items):
        self.feed_list.clear()
        if not items: self.feed_list.addItem("Feed could not be loaded.")
        for title,url in items:
            it=QListWidgetItem(title); it.setData(Qt.UserRole,url); self.feed_list.addItem(it)

    def _try_aero_glass(self):
        if not sys.platform.startswith("win"): return
        try:
            import ctypes
            class MARGINS(ctypes.Structure): _fields_=[("cxLeftWidth",ctypes.c_int),("cxRightWidth",ctypes.c_int),("cyTopHeight",ctypes.c_int),("cyBottomHeight",ctypes.c_int)]
            ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(int(self.winId()), ctypes.byref(MARGINS(0,0,0,1)))
        except Exception: pass

    def import_export_info(self):
        QMessageBox.information(self, "Import and export",
                                "Favorites can be managed in the Favorites Center (★ button).")

    def suggested_sites_info(self):
        QMessageBox.information(
            self, "Suggested Sites",
            "Suggested Sites is taking a trip down memory lane and is not\n"
            "available in this nostalgia edition.")

    # ------------------------------------------------------------------
    # Menus
    # ------------------------------------------------------------------
    def create_tools_menu(self):
        menu = QMenu(self)
        print_menu = menu.addMenu("Print")
        self.action(print_menu, "Print...\tCtrl+P", self.print_to_pdf)
        self.action(print_menu, "Print preview (save as PDF)", self.print_to_pdf)
        file_menu = menu.addMenu("File")
        self.action(file_menu, "New tab\tCtrl+T", lambda: self.add_tab(NEW_TAB_URL))
        self.action(file_menu, "Open location...\tCtrl+L", self.focus_address)
        self.action(file_menu, "Open...\tCtrl+O", self.open_local_file)
        offline = self.action(file_menu, "Work Offline", self.toggle_offline)
        offline.setCheckable(True); offline.setChecked(self.offline)
        self.action(file_menu, "Save page as...\tCtrl+S", self.save_page)
        self.action(file_menu, "Close tab\tCtrl+W",
                    lambda: self.close_tab(self.tabbar.currentIndex()))
        self.action(file_menu, "Exit", self.close)
        zoom_menu = menu.addMenu("Zoom")
        self.action(zoom_menu, "Zoom in\tCtrl++", lambda: self.zoom(1.1))
        self.action(zoom_menu, "Zoom out\tCtrl+-", lambda: self.zoom(0.9))
        self.action(zoom_menu, "Reset zoom\tCtrl+0", lambda: self.set_zoom(1.0))
        safety_menu = menu.addMenu("Safety")
        self.action(safety_menu, "Delete browsing history...", self.clear_browsing_data)
        self.action(safety_menu, "Find on this page...\tCtrl+F", self.find_on_page)
        self.action(menu, "New InPrivate tab\tCtrl+Shift+N", self.new_private_tab)
        sounds = self.action(menu, "Sounds", self.toggle_sounds); sounds.setCheckable(True); sounds.setChecked(self.sounds_enabled)
        modes = menu.addMenu("Browser mode")
        mode_group = __import__('PyQt5.QtWidgets', fromlist=['QActionGroup']).QActionGroup(modes)
        for key, label in (("modern", "Microsoft Edge WebView2 (recommended)"),
                           ("ie11", "IE11 compatibility user-agent")):
            item = QAction(label, modes); item.setCheckable(True); item.setChecked(self.browser_mode == key)
            mode_group.addAction(item); modes.addAction(item); item.triggered.connect(lambda checked=False, k=key: self.set_browser_mode(k))
        menu.addSeparator()
        self.favbar_action = self.action(menu, "Favorites bar", self.toggle_favorites_bar)
        self.favbar_action.setCheckable(True)
        fav_bar = getattr(self, "fav_bar", None)
        self.favbar_action.setChecked(True if fav_bar is None else fav_bar.isVisible())
        self.menubar_action = self.action(menu, "Menu bar", self.toggle_menu_bar)
        self.menubar_action.setCheckable(True)
        menubar = getattr(self, "_menubar", None)
        self.menubar_action.setChecked(False if menubar is None else menubar.isVisible())
        self.suggest_action = self.action(menu, "Turn off suggestions" if self.suggestions_enabled
                                          else "Turn on suggestions", self.toggle_suggestions)
        menu.addSeparator()
        self.action(menu, "Add site to Apps", self.add_favorite)
        self.action(menu, "View downloads\tCtrl+J", self.show_downloads)
        self.action(menu, "Manage add-ons", self.about_engine)
        self.action(menu, "Website permissions...", self.show_permission_center)
        self.action(menu, "Password Manager...", self.show_password_manager)
        self.action(menu, "Developer Tools\tF12", self.open_devtools)
        self.action(menu, "Go to pinned sites", lambda: self.navigate(HOME_URL))
        self.action(menu, "History\tCtrl+H", self.show_history)
        self.action(menu, "Toggle dark mode", self.toggle_dark_mode)
        self.action(menu, "Internet options", self.internet_options)
        self.action(menu, "Compatibility View settings", self.compatibility_info)
        menu.addSeparator()
        self.action(menu, "About Internet Explorer", self.about)
        return menu

    def refresh_favorites_menu(self, menu):
        menu.clear()
        links = QAction("📂  Links", menu)
        links.setEnabled(False)
        menu.addAction(links)
        menu.addSeparator()
        for title, url in self.favorites:
            action = QAction(title, menu)
            action.triggered.connect(lambda checked=False, target=url: self.navigate(target))
            menu.addAction(action)
        menu.addSeparator()
        add = QAction("Add current page to Favorites…", menu)
        add.triggered.connect(self.add_favorite)
        menu.addAction(add)

    def action(self, menu, text, callback, shortcut=None):
        action = QAction(text, self)
        if shortcut:
            action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(callback)
        menu.addAction(action)
        return action

    # ------------------------------------------------------------------
    # F12 Developer Tools (embedded inspector + robust fallback)
    # ------------------------------------------------------------------
    def open_devtools(self):
        tab = self.current_tab()
        if not tab:
            return
        try:
            tab.view.open_devtools()
        except Exception as exc:
            QMessageBox.warning(self, "Developer Tools", f"Could not open Edge DevTools.\n\n{exc}")


    # ------------------------------------------------------------------
    # Zoom / misc browser features
    # ------------------------------------------------------------------
    def zoom(self, factor):
        view = self.current_view()
        if view:
            view.setZoomFactor(max(0.25, min(5.0, view.zoomFactor() * factor)))
            self._save_current_site_zoom()
            self.update_zoom_label()

    def set_zoom(self, value):
        view = self.current_view()
        if view:
            view.setZoomFactor(value)
            self._save_current_site_zoom()
            self.update_zoom_label()

    def _save_current_site_zoom(self):
        view=self.current_view()
        if view and view.url().host(): self.zoom_sites[view.url().host().lower()] = view.zoomFactor(); self.save_state()

    def open_local_file(self):
        filename,_=QFileDialog.getOpenFileName(self,"Open", "", "Web pages (*.htm *.html);;All files (*.*)")
        if filename: self.navigate(QUrl.fromLocalFile(filename).toString())
    def toggle_offline(self):
        self.offline=not self.offline; self.update_zone_label(); self.save_state()
    def toggle_sounds(self): self.sounds_enabled=not self.sounds_enabled; self.save_state()
    @staticmethod
    def _user_agent_for_mode(mode):
        """Only override WebView2's modern UA when compatibility is requested."""
        if mode == "ie11":
            return "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko"
        return None

    def set_browser_mode(self, mode):
        if mode not in ("modern", "ie11"):
            mode = "modern"
        self.browser_mode = mode
        self.web_user_agent = self._user_agent_for_mode(mode)
        self.save_state()
        self.status_label.setText(
            "Engine mode saved. New tabs use Microsoft Edge WebView2; reopen existing tabs to apply it.")

    def find_on_page(self):
        text, ok = QInputDialog.getText(self, "Find on this page", "Find:")
        if ok and text and self.current_view():
            self.current_view().findText(text)

    def save_page(self):
        view = self.current_view()
        if not view:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save page", "webpage.html",
                                                  "HTML files (*.html);;All files (*.*)")
        if filename:
            view.page().toHtml(lambda html: self._write_text_file(filename, html))

    def _write_text_file(self, filename, content):
        try:
            with open(filename, "w", encoding="utf-8") as handle:
                handle.write(content)
            self.status_label.setText("Saved page: " + os.path.basename(filename))
        except OSError as exc:
            QMessageBox.warning(self, "Save page", str(exc))

    def print_to_pdf(self):
        view = self.current_view()
        if not view:
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Save page as PDF", "ie11-page.pdf",
                                                  "PDF files (*.pdf)")
        if filename:
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            view.page().printToPdf(filename)
            self.status_label.setText("Exporting PDF…")

    # ------------------------------------------------------------------
    # Downloads ("View Downloads - Internet Explorer")
    # ------------------------------------------------------------------
    def _connect_downloads(self):
        # Each WebView2 control registers its download callbacks at construction.
        pass

    def on_download_requested(self, download):
        suggested = download.downloadFileName() or "download"
        folder = os.path.join(os.path.expanduser("~"), "Downloads")
        filename, ok = QInputDialog.getText(self, "Download", "Save as:",
                                            text=os.path.join(folder, suggested))
        if not ok or not filename:
            download.cancel()
            return
        directory, basename = os.path.split(filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        download.setDownloadDirectory(directory or os.getcwd())
        download.setDownloadFileName(basename or suggested)
        download.accept()
        rec = {"name": basename or suggested, "dir": directory or os.getcwd(),
               "path": filename, "item": download, "done": False, "ok": None,
               "received": 0, "total": 0, "row": None}
        self.download_records.append(rec)
        self.downloads.append(filename)
        self.downloads = self.downloads[-200:]
        self.save_state()
        download.downloadProgress.connect(lambda r, t, rec=rec: self._on_dl_progress(rec, r, t))
        download.finished.connect(lambda rec=rec: self._on_dl_finished(rec))
        dlg = getattr(self, "_downloads_dialog", None)
        if dlg is not None and dlg.isVisible():
            dlg.refresh()
        self.status_label.setText("Downloading: " + rec["name"])

    def _on_dl_progress(self, rec, received, total):
        rec["received"] = received
        rec["total"] = total
        dlg = getattr(self, "_downloads_dialog", None)
        if dlg is not None and dlg.isVisible():
            dlg.update_row(rec)
        if total > 0:
            self.status_label.setText(f'Downloading {rec["name"]} — {int(received * 100 / total)}%')

    def _on_dl_finished(self, rec):
        try:
            ok = True
        except Exception:
            ok = True
        rec["done"] = True
        rec["ok"] = ok
        dlg = getattr(self, "_downloads_dialog", None)
        if dlg is not None and dlg.isVisible():
            dlg.refresh()
        self.status_label.setText(("Download finished: " if ok else "Download canceled: ") + rec["name"])
        if ok:
            self.infobar.show_message("Download of %s completed." % rec["name"], [("Open", lambda r=rec: QDesktopServices.openUrl(QUrl.fromLocalFile(r["path"]))), ("Open folder", lambda r=rec: QDesktopServices.openUrl(QUrl.fromLocalFile(r["dir"])))])

    def show_downloads(self):
        dlg = getattr(self, "_downloads_dialog", None)
        if dlg is None:
            dlg = DownloadsDialog(self)
            self._downloads_dialog = dlg
        dlg.refresh()
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    # ------------------------------------------------------------------
    # Safety / about
    # ------------------------------------------------------------------
    def clear_browsing_data(self):
        answer = QMessageBox.question(
            self, "Delete browsing history",
            "Clear cookies and cached website data?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.profile.cookieStore().deleteAllCookies()
            self.profile.clearHttpCache()
            self.history.clear()
            QMessageBox.information(self, "Safety", "Cookies and cached data cleared.")

    def internet_options(self):
        QMessageBox.information(
            self, "Internet options",
            "This is a Chromium-based IE11-style browser. Windows Internet Options,\n"
            "ActiveX controls, and Compatibility View are not available in Chromium.")

    def compatibility_info(self):
        QMessageBox.information(
            self, "Compatibility View settings",
            "Compatibility View was specific to Internet Explorer.\n"
            "This Chromium browser cannot enable it.")

    def about(self):
        QMessageBox.about(
            self, "About Internet Explorer",
            "Internet Explorer 11 Nostalgia UI\n\n"
            "A fan-made browser interface inspired by Internet Explorer 11.\n"
            "Web pages are rendered by Microsoft Edge WebView2; this is not\n"
            "the original Microsoft Internet Explorer browser.")

    def about_engine(self):
        QMessageBox.information(
            self, "Manage add-ons / Developer tools",
            "Rendering engine: Microsoft Edge WebView2 (Chromium).\n"
            "IE ActiveX add-ons are not supported. Press F12 for developer tools.")

    def show_permission_center(self):
        dialog=QDialog(self); dialog.setWindowTitle("Permission Center - Internet Explorer"); dialog.setWindowIcon(self.windowIcon()); dialog.resize(540,330)
        layout=QVBoxLayout(dialog); layout.addWidget(QLabel("Website permissions"))
        listing=QListWidget(); layout.addWidget(listing)
        def refill():
            listing.clear()
            for key,value in sorted(self.site_permissions.items()): listing.addItem("%s — %s" % (key,value.title()))
            if not self.site_permissions: listing.addItem("No saved website permissions.")
        remove=QPushButton("Remove selected"); close=QPushButton("Close")
        def remove_selected():
            item=listing.currentItem()
            if item and " — " in item.text(): self.site_permissions.pop(item.text().split(" — ",1)[0],None); self.save_state(); refill()
        remove.clicked.connect(remove_selected); close.clicked.connect(dialog.accept); buttons=QHBoxLayout(); buttons.addWidget(remove); buttons.addStretch(1); buttons.addWidget(close); layout.addLayout(buttons); refill(); dialog.exec_()

    def show_website_identification(self):
        view = self.current_view()
        if not view:
            return
        url = view.url(); host = url.host() or "This page"; https = url.scheme().lower() == "https"
        panel = QDialog(self, Qt.Popup); panel.setWindowTitle("Website Identification"); panel.setMinimumWidth(410)
        layout = QVBoxLayout(panel)
        layout.addWidget(QLabel("<b>%s</b><br>Website Identification" % host))
        note = QLabel("This connection to the website is encrypted." if https else "Not secure — this connection is not encrypted.")
        note.setStyleSheet("background:#fff4c5;border:1px solid #d7b85a;padding:7px" if https else "background:#eeeeee;border:1px solid #aaaaaa;padding:7px")
        layout.addWidget(note); layout.addWidget(QLabel("Website permissions"))
        for feature, label in (("camera", "Camera"), ("microphone", "Microphone"), ("location", "Location"), ("notifications", "Notifications")):
            row = QHBoxLayout(); row.addWidget(QLabel(label)); combo = QComboBox(); combo.addItems(["Ask each time", "Always allow", "Always block"])
            key = host.lower() + ":" + feature; combo.setCurrentIndex({"allow": 1, "block": 2}.get(self.site_permissions.get(key), 0))
            combo.currentIndexChanged.connect(lambda index, k=key: self._set_permission_default(k, index)); row.addWidget(combo); layout.addLayout(row)
        more = QPushButton("More information")
        more.clicked.connect(lambda: QMessageBox.information(panel, "Website Identification", "Website: %s\nScheme: %s\nEncryption: %s" % (host, url.scheme().upper(), "TLS" if https else "None")))
        layout.addWidget(more); panel.adjustSize(); panel.move(self.address_frame.mapToGlobal(QPoint(0, self.address_frame.height()))); panel.show()

    def _set_permission_default(self, key, index):
        if index == 0: self.site_permissions.pop(key, None)
        else: self.site_permissions[key] = "allow" if index == 1 else "block"
        self.save_state()

    def _load_password_vault(self):
        try:
            with open(self.password_vault_file, "r", encoding="utf-8") as handle:
                self.passwords = json.loads(_dpapi_unprotect(handle.read()))
            if not isinstance(self.passwords, list): self.passwords = []
        except (OSError, ValueError, TypeError): self.passwords = []

    def _save_password_vault(self):
        try:
            encrypted = _dpapi_protect(json.dumps(self.passwords, ensure_ascii=False))
            with open(self.password_vault_file, "w", encoding="utf-8") as handle: handle.write(encrypted)
        except OSError as exc: QMessageBox.warning(self, "Password Manager", "Could not save the password vault.\n\n" + str(exc))

    def show_password_manager(self):
        dialog=QDialog(self); dialog.setWindowTitle("Password Manager - Internet Explorer"); dialog.setWindowIcon(self.windowIcon()); dialog.resize(610,360)
        layout=QVBoxLayout(dialog); layout.addWidget(QLabel("Saved passwords are encrypted for this Windows account."))
        listing=QTreeWidget(); listing.setHeaderLabels(["Website", "Username"]); listing.header().setSectionResizeMode(0,QHeaderView.Stretch); layout.addWidget(listing)
        def refill():
            listing.clear()
            for entry in self.passwords:
                item=QTreeWidgetItem([entry.get("origin", ""),entry.get("username", "")]); item.setData(0,Qt.UserRole,entry); listing.addTopLevelItem(item)
        def add():
            view=self.current_view(); origin=(view.url().scheme()+"://"+view.url().host()) if view and view.url().host() else ""
            site,ok=QInputDialog.getText(dialog,"Save password","Website:",text=origin)
            if not ok or not site: return
            user,ok=QInputDialog.getText(dialog,"Save password","Username:")
            if not ok: return
            password,ok=QInputDialog.getText(dialog,"Save password","Password:",QLineEdit.Password)
            if ok: self.passwords=[p for p in self.passwords if not (p.get("origin")==site and p.get("username")==user)]+[{"origin":site,"username":user,"password":password}]; self._save_password_vault(); refill()
        def remove():
            item=listing.currentItem(); entry=item.data(0,Qt.UserRole) if item else None
            if entry in self.passwords: self.passwords.remove(entry); self._save_password_vault(); refill()
        def fill():
            item=listing.currentItem(); entry=item.data(0,Qt.UserRole) if item else None; view=self.current_view()
            if not entry or not view: return
            u=json.dumps(entry["username"]); p=json.dumps(entry["password"])
            view.widget.eval_js("(function(){var a=document.querySelector('input[type=email],input[type=text],input[name*=user i]');var b=document.querySelector('input[type=password]');if(a)a.value="+u+";if(b)b.value="+p+";})()")
            self.status_label.setText("Saved credentials filled. Review before signing in.")
        row=QHBoxLayout(); addb=QPushButton("Add current site..."); fillb=QPushButton("Fill"); removeb=QPushButton("Remove"); close=QPushButton("Close")
        addb.clicked.connect(add); fillb.clicked.connect(fill); removeb.clicked.connect(remove); close.clicked.connect(dialog.accept); row.addWidget(addb);row.addWidget(fillb);row.addWidget(removeb);row.addStretch();row.addWidget(close);layout.addLayout(row);refill();dialog.exec_()

    # ------------------------------------------------------------------
    # Theme / state
    # ------------------------------------------------------------------
    def _apply_theme(self):
        self.setStyleSheet((DARK_QSS + CHROME_DARK_QSS) if self.dark_mode else (LIGHT_QSS + CHROME_LIGHT_QSS))
        if hasattr(self, "infobar"): self.infobar.apply_theme(self.dark_mode)
        try:
            pass  # WebView2 uses Edge runtime settings; page theme is handled by the browser UI.
        except Exception:
            pass

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self._apply_theme()
        for index in range(self.stack.count()):
            tab = self.stack.widget(index)
            if isinstance(tab, BrowserTab) and tab.is_custom_new_tab:
                tab.view.setHtml(build_new_tab_html(self.dark_mode))
        self.save_state()
        self.status_label.setText("Dark mode enabled" if self.dark_mode else "Light mode enabled")

    def toggle_fullscreen(self):
        leaving = self.isFullScreen()
        self.showNormal() if leaving else self.showFullScreen()
        if hasattr(self, "titlebar"): self.titlebar.setVisible(leaving)

    def _escape_pressed(self):
        if self.suggest_popup.isVisible():
            self.dismiss_suggestions()
            return
        view = self.current_view()
        if view:
            view.stop()

    def _load_state(self):
        try:
            with open(self.state_file, "r", encoding="utf-8") as handle:
                state = json.load(handle)
            self.favorites = state.get("favorites", self.favorites)
            self.history = state.get("history", [])[-500:]
            self.downloads = state.get("downloads", [])[-200:]
            self.dark_mode = bool(state.get("dark_mode", False))
            self.suggestions_enabled = bool(state.get("suggestions", True))
            self.sounds_enabled = bool(state.get("sounds", True)); self.offline = bool(state.get("offline", False))
            self.caret_browsing = bool(state.get("caret_browsing", False))
            # Older releases persisted their default IE11 UA.  Migrate those
            # installations to WebView2's native, current UA once.
            self.browser_mode = (state.get("browser_mode", "modern")
                                 if state.get("webview2_mode_selection") else "modern")
            if self.browser_mode not in ("modern", "ie11"):
                self.browser_mode = "modern"
            self.zoom_sites = state.get("zoom_sites", {}); self.popup_whitelist = state.get("popup_whitelist", [])
            self.site_permissions = state.get("site_permissions", {})
            self.saved_session = state.get("session", self.saved_session); self._was_unclean = not bool(state.get("clean_exit", True))
        except (OSError, ValueError, TypeError):
            pass

    def _mark_running(self):
        """Clear clean_exit immediately without destroying the pre-start session."""
        try:
            with open(self.state_file, "r", encoding="utf-8") as handle: state=json.load(handle)
            state["clean_exit"] = False
            with open(self.state_file, "w", encoding="utf-8") as handle: json.dump(state, handle, ensure_ascii=False, indent=2)
        except Exception: pass

    def save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as handle:
                json.dump({"favorites": self.favorites, "history": self.history[-500:],
                           "downloads": self.downloads[-200:], "dark_mode": self.dark_mode,
                           "suggestions": self.suggestions_enabled, "sounds": self.sounds_enabled, "offline": self.offline,
                           "caret_browsing": self.caret_browsing, "browser_mode": self.browser_mode, "zoom_sites": self.zoom_sites,
                           "webview2_mode_selection": True,
                           "popup_whitelist": self.popup_whitelist, "session": self._session_data() if hasattr(self, "stack") else self.saved_session,
                           "site_permissions": self.site_permissions,
                           "clean_exit": False},
                          handle, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def show_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("History")
        dialog.setWindowIcon(self.windowIcon())
        dialog.resize(680, 420)
        layout = QVBoxLayout(dialog)
        listing = QListWidget(dialog)
        for title, url in reversed(self.history[-500:]):
            item = QListWidgetItem(f"{title}   —   {url}")
            item.setData(Qt.UserRole, url)
            listing.addItem(item)
        listing.itemDoubleClicked.connect(
            lambda item: (self.navigate(item.data(Qt.UserRole)), dialog.accept()))
        layout.addWidget(QLabel("Double-click an entry to open it."))
        layout.addWidget(listing)
        buttons = QHBoxLayout()
        clear_button = QPushButton("Clear history")
        close_button = QPushButton("Close")
        clear_button.clicked.connect(lambda: self._clear_history_from_dialog(listing))
        close_button.clicked.connect(dialog.accept)
        buttons.addWidget(clear_button)
        buttons.addStretch(1)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        dialog.exec_()

    def _clear_history_from_dialog(self, listing):
        self.history.clear()
        listing.clear()
        self.save_state()

    # ------------------------------------------------------------------
    # Address bar events (focus ring, suggestion keyboard navigation)
    # ------------------------------------------------------------------
    @staticmethod
    def _repolish(widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def eventFilter(self, obj, event):
        if obj is getattr(self, "lock_label", None) and event.type() == QEvent.MouseButtonRelease:
            self.show_website_identification()
            return True
        if hasattr(self, "suggest_popup") and self.suggest_popup.isVisible():
            if event.type() == QEvent.MouseButtonPress:
                gp = getattr(event, "globalPos", None)
                if callable(gp):
                    gp = gp()
                if gp:
                    if not self.suggest_popup.geometry().contains(gp):
                        target = getattr(self.suggest_popup, "_current_target", None) or self.address_frame
                        tgt_rect = QRect(target.mapToGlobal(QPoint(0, 0)), target.size())
                        if not tgt_rect.contains(gp):
                            self.dismiss_suggestions()
            elif event.type() == QEvent.WindowDeactivate:
                self.dismiss_suggestions()

        address_bar = getattr(self, "address_bar", None)
        search_bar = getattr(self, "search_bar", None)
        if (obj is address_bar or obj is search_bar) and obj is not None:
            if event.type() == QEvent.FocusIn:
                if obj is self.address_bar:
                    self.address_frame.setProperty("focus", True)
                    self._repolish(self.address_frame)
            elif event.type() == QEvent.FocusOut:
                if obj is self.address_bar:
                    self.address_frame.setProperty("focus", False)
                    self._repolish(self.address_frame)
            elif event.type() == QEvent.KeyPress:
                key = event.key()
                if self.suggest_popup.isVisible():
                    if key == Qt.Key_Escape:
                        self.dismiss_suggestions()
                        return True
                    if key == Qt.Key_Down:
                        self.suggest_popup.move_selection(1)
                        return True
                    if key == Qt.Key_Up:
                        self.suggest_popup.move_selection(-1)
                        return True
                    if key in (Qt.Key_Return, Qt.Key_Enter):
                        if self.suggest_popup.trigger_current():
                            return True
                        self.suggest_popup.hide()
                elif key == Qt.Key_Down:
                    mods = event.modifiers()
                    if obj is self.address_bar and ((mods & Qt.AltModifier) or not self.address_bar.text().strip()):
                        self.show_address_dropdown()
                        return True
        return super().eventFilter(obj, event)

    def moveEvent(self, event):
        super().moveEvent(event)
        if hasattr(self, "suggest_popup") and self.suggest_popup.isVisible():
            self.suggest_popup.show_at()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_chrome_title()
        if hasattr(self, "suggest_popup") and self.suggest_popup.isVisible():
            self.suggest_popup.show_at()

    def add_shortcut(self, sequence, callback):
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.setContext(Qt.ApplicationShortcut)
        shortcut.activated.connect(callback)
        self._shortcuts.append(shortcut)

    def closeEvent(self, event):
        self.save_state()
        try:
            with open(self.state_file, "r", encoding="utf-8") as handle: state=json.load(handle)
            state["clean_exit"] = True
            with open(self.state_file, "w", encoding="utf-8") as handle: json.dump(state, handle, ensure_ascii=False, indent=2)
        except Exception: pass
        event.accept()

# ═══════════════════════════════════════════════════════════════════════════
#  IE11 Nostalgia — feature pack: universal keybinds, Ctrl+Shift+T,
#  F11 fullscreen, and a Chrome-style local password manager (DPAPI + Hello)
#  Paste this block at the bottom of ie11.py, ABOVE the __main__ guard.
# ═══════════════════════════════════════════════════════════════════════════
import time
import uuid as _uuid
from ctypes import wintypes as _wintypes
from PyQt5.QtCore import QAbstractNativeEventFilter
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QScrollArea, QCheckBox, QGridLayout

PASSWORD_AGENT_JS = r'''
(function(){
  if (window.__ie11pw) return;
  var S={seq:1,fields:{},ev:[],dd:null,ddFor:null};
  function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
  function visible(el){if(!el||!el.getClientRects||!el.getClientRects().length)return false;var s=getComputedStyle(el);return s.visibility!=='hidden'&&s.display!=='none';}
  function userish(el){
    if(!el||el.tagName!=='INPUT')return false;
    var t=(el.getAttribute('type')||'text').toLowerCase();
    if(t==='password'||t==='hidden'||t==='checkbox'||t==='radio'||t==='submit'||t==='button'||t==='file')return false;
    return !(el.disabled||el.readOnly);
  }
  function usernameFor(pw){
    var form=pw.form,cand=null;
    if(form){
      var els=Array.prototype.slice.call(form.elements),i=els.indexOf(pw);
      for(var j=i-1;j>=0;j--){if(userish(els[j])&&visible(els[j])){cand=els[j];break;}}
      if(!cand)for(var k=i+1;k<els.length;k++){if(userish(els[k])&&visible(els[k])){cand=els[k];break;}}
    }
    if(!cand){
      var inputs=document.querySelectorAll('input:not([type=password])');
      for(var m=0;m<inputs.length;m++){
        var el=inputs[m];
        if(userish(el)&&visible(el)&&(pw.compareDocumentPosition(el)&Node.DOCUMENT_POSITION_PRECEDING)){cand=el;break;}
      }
    }
    return cand;
  }
  function tag(el){if(!el)return null;if(!el.__ie11pwId)el.__ie11pwId='f'+(S.seq++);S.fields[el.__ie11pwId]=el;return el.__ie11pwId;}
  function hideDD(){if(S.dd){if(S.dd.parentNode)S.dd.parentNode.removeChild(S.dd);S.dd=null;S.ddFor=null;}}
  function showDD(fid,users){
    var el=S.fields[fid];if(!el||!visible(el))return;
    hideDD();
    var d=document.createElement('div');
    d.style.cssText='position:absolute;z-index:2147483647;background:#fff;border:1px solid #dadce0;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.28);font:13px/1.5 "Segoe UI",Arial,sans-serif;color:#202124;min-width:240px;max-width:340px;padding:5px 0;';
    users.forEach(function(u){
      var row=document.createElement('div');
      row.style.cssText='display:flex;align-items:center;gap:10px;padding:7px 14px;cursor:pointer;white-space:nowrap;overflow:hidden;';
      row.innerHTML='<span style="flex:0 0 auto;display:inline-grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#e8f0fe;color:#1a73e8;font-size:11px;font-weight:700;">'+esc((u.username||'?').charAt(0).toUpperCase())+'</span>'
        +'<span style="overflow:hidden;text-overflow:ellipsis;">'+esc(u.username)+'</span>'
        +'<span style="margin-left:auto;color:#5f6368;font-size:11px;">&#9679;&#9679;&#9679;</span>';
      row.addEventListener('mousedown',function(ev){ev.preventDefault();ev.stopPropagation();S.ev.push({type:'pick',fid:fid,username:u.username});hideDD();});
      row.addEventListener('mouseover',function(){row.style.background='#f1f3f4';});
      row.addEventListener('mouseout',function(){row.style.background='transparent';});
      d.appendChild(row);
    });
    var hr=document.createElement('div');hr.style.cssText='height:1px;background:#e0e0e0;margin:4px 0;';d.appendChild(hr);
    var mg=document.createElement('div');
    mg.style.cssText='display:flex;align-items:center;gap:10px;padding:7px 14px;cursor:pointer;color:#1a73e8;font-weight:600;';
    mg.innerHTML='<span style="width:22px;text-align:center;">&#128273;</span><span>Passwords&hellip;</span>';
    mg.addEventListener('mousedown',function(ev){ev.preventDefault();ev.stopPropagation();S.ev.push({type:'manage'});hideDD();});
    mg.addEventListener('mouseover',function(){mg.style.background='#f1f3f4';});
    mg.addEventListener('mouseout',function(){mg.style.background='transparent';});
    d.appendChild(mg);
    document.body.appendChild(d);
    var r=el.getBoundingClientRect(),dr=d.getBoundingClientRect();
    var top=r.bottom+window.scrollY+4,left=r.left+window.scrollX;
    if(r.bottom+dr.height+8>window.innerHeight)top=r.top+window.scrollY-dr.height-4;
    d.style.top=top+'px';d.style.left=left+'px';
    S.dd=d;S.ddFor=fid;
  }
  function setVal(el,v){
    if(!el)return;
    try{var d=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value');d.set.call(el,v);}catch(e){el.value=v;}
    el.dispatchEvent(new Event('input',{bubbles:true}));
    el.dispatchEvent(new Event('change',{bubbles:true}));
  }
  function grab(pw){
    if(!pw||!pw.value)return;
    var u=usernameFor(pw);
    S.ev.push({type:'submit',url:location.href,username:u?u.value:'',password:pw.value});
  }
  document.addEventListener('submit',function(e){
    var f=e.target;if(!f||!f.querySelectorAll)return;
    var pws=f.querySelectorAll('input[type=password]');
    if(pws.length)grab(pws[0]);
  },true);
  document.addEventListener('click',function(e){
    var b=e.target&&e.target.closest?e.target.closest('button,input[type=submit],input[type=button],[role=button]'):null;
    if(!b)return;
    var form=b.form||(b.closest?b.closest('form'):null);
    if(!form)return;
    var pws=form.querySelectorAll('input[type=password]');
    for(var i=0;i<pws.length;i++){if(visible(pws[i])){grab(pws[i]);break;}}
  },true);
  document.addEventListener('focusin',function(e){
    var el=e.target;
    var isPw=el&&el.getAttribute&&(el.getAttribute('type')||'').toLowerCase()==='password';
    if(el&&(isPw||userish(el))){
      var fid=tag(el);
      if(fid)S.ev.push({type:'suggest',fid:fid});
    } else if(S.dd&&el&&!S.dd.contains(el)&&el!==S.fields[S.ddFor]){hideDD();}
  });
  document.addEventListener('mousedown',function(e){
    if(S.dd&&e.target&&!S.dd.contains(e.target)&&e.target!==S.fields[S.ddFor])hideDD();
  },true);
  window.addEventListener('scroll',hideDD,true);
  window.addEventListener('resize',hideDD);
  document.addEventListener('keydown',function(e){if(e.key==='Escape')hideDD();},true);
  window.__ie11pw_poll=function(){
    var n=document.querySelectorAll('input[type=password]').length;
    var out=S.ev.splice(0,S.ev.length);
    return JSON.stringify({events:out,fields:n});
  };
  window.__ie11pw_cmd=function(cmd){
    try{
      if(!cmd||!cmd.op)return 'bad';
      if(cmd.op==='show'){showDD(cmd.fid,cmd.users||[]);return 'ok';}
      if(cmd.op==='hide'){hideDD();return 'ok';}
      if(cmd.op==='fill'){
        var pwEl=S.fields[cmd.fid];
        if(pwEl)setVal(pwEl,cmd.password||'');
        var uEl=cmd.ufid?S.fields[cmd.ufid]:null;
        if(uEl&&cmd.username!=null)setVal(uEl,cmd.username);
        hideDD();
        return 'ok';
      }
      if(cmd.op==='fields'){
        var pws=document.querySelectorAll('input[type=password]'),pairs=[];
        for(var i=0;i<pws.length&&i<5;i++){
          var p=pws[i];if(!visible(p))continue;
          var u=usernameFor(p);
          pairs.push({pfid:tag(p),ufid:u?tag(u):null});
        }
        return JSON.stringify({pairs:pairs});
      }
      return 'unknown';
    }catch(err){return 'err:'+err.message;}
  };
  window.__ie11pw=true;
})();
'''


# ───────────────────────────── Windows Hello gate ───────────────────────────
class WindowsHello(QObject):
    """Gates password fill/reveal/copy behind Windows Hello
    (fingerprint / face / PIN) via WinRT UserConsentVerifier.  Successful
    verification unlocks a 60-second grace period, like Chrome's re-auth."""
    GRACE_SECONDS = 60
    _finished = pyqtSignal(bool, str)

    def __init__(self):
        super().__init__()
        self._unlocked_until = 0.0
        self._pending = None
        self._finished.connect(self._on_finished)

    @staticmethod
    def _modules():
        try:
            try:
                from winrt.windows.security.credentials.ui import UserConsentVerifier  # noqa
            except Exception:
                from winsdk.windows.security.credentials.ui import UserConsentVerifier  # noqa
            return UserConsentVerifier
        except Exception:
            return None

    @classmethod
    def availability(cls):
        ucv = cls._modules()
        if ucv is None:
            return False, "winrt not installed — confirmation prompts are used instead"
        try:
            import asyncio
            res = asyncio.run(ucv.check_availability_async())
            name = getattr(res, "name", "") or str(res)
            if "Available" in name and "Not" not in name:
                return True, "Protected by Windows Hello"
            return False, "Windows Hello not available (%s)" % (name or "unknown")
        except Exception as exc:
            return False, "Windows Hello unavailable: %s" % exc

    def unlocked(self):
        return time.time() < self._unlocked_until

    def mark_verified(self):
        self._unlocked_until = time.time() + self.GRACE_SECONDS

    def require(self, parent, reason, callback):
        """callback(ok: bool, message: str) always runs on the GUI thread."""
        if self.unlocked():
            callback(True, "already verified"); return
        ucv = self._modules()
        if ucv is None:
            _, why = self.availability()
            box = QMessageBox(parent)
            box.setWindowTitle("Verify it's you")
            box.setIcon(QMessageBox.Warning)
            box.setText("%s\n\nWindows Hello is not available on this device (%s).\n"
                        "Continue with a simple confirmation instead?" % (reason, why))
            verify = box.addButton("Verify", QMessageBox.AcceptRole)
            box.addButton(QMessageBox.Cancel)
            box.exec_()
            if box.clickedButton() is verify:
                self.mark_verified(); callback(True, "confirmed")
            else:
                callback(False, "canceled")
            return
        self._pending = callback
        threading.Thread(target=self._run, args=(ucv, reason), daemon=True).start()

    def _run(self, ucv, reason):
        try:
            import asyncio
            res = asyncio.run(ucv.request_verification_async(reason))
            name = getattr(res, "name", "") or str(res)
            ok = ("Verified" in name) and ("Not" not in name)
            self._finished.emit(ok, name)
        except Exception as exc:
            self._finished.emit(False, "error: %s" % exc)

    def _on_finished(self, ok, msg):
        cb = self._pending; self._pending = None
        if ok:
            self.mark_verified()
        if cb:
            cb(ok, msg)


# ───────────────────────────── local password vault ─────────────────────────
def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class PasswordVault:
    """Chrome-like store in <data_dir>/passwords.json.  Only the password
    field is encrypted (DPAPI, bound to the current Windows account)."""
    def __init__(self, path):
        self.path = path
        self.data = {"offer_to_save": True, "auto_sign_in": False,
                     "never_save": [], "sites": {}}
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                stored = json.load(fh)
            if isinstance(stored, dict):
                self.data.update(stored)
        except Exception:
            pass
        self.data.setdefault("sites", {})
        self.data.setdefault("never_save", [])
        self.data.setdefault("offer_to_save", True)
        self.data.setdefault("auto_sign_in", False)

    def save(self):
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self.data, fh, indent=1)
            os.replace(tmp, self.path)
        except Exception:
            pass

    @staticmethod
    def site_key(url):
        try:
            parts = urlsplit(url if "://" in url else "http://" + url)
        except Exception:
            return None
        host = (parts.hostname or "").lower()
        if not host:
            return None
        if host.startswith("www."):
            host = host[4:]
        return host

    def entries(self, url):
        host = self.site_key(url)
        return list(self.data["sites"].get(host, [])) if host else []

    def add(self, url, username, password):
        host = self.site_key(url)
        if not host:
            return None
        lst = self.data["sites"].setdefault(host, [])
        for e in lst:
            if e.get("username") == username:
                e["password_enc"] = _dpapi_protect(password)
                e["updated"] = _now_iso()
                self.save(); return e
        e = {"id": _uuid.uuid4().hex, "username": username,
             "password_enc": _dpapi_protect(password),
             "created": _now_iso(), "last_used": None, "display": url}
        lst.append(e); self.save(); return e

    def update_entry(self, old_host, entry, new_host, new_user, new_password):
        sites = self.data["sites"]
        lst = sites.get(old_host, [])
        sites[old_host] = [x for x in lst if x is not entry]
        if old_host in sites and not sites[old_host]:
            del sites[old_host]
        entry["username"] = new_user
        entry["password_enc"] = _dpapi_protect(new_password)
        entry["updated"] = _now_iso()
        sites.setdefault(new_host, []).append(entry)
        self.save()

    def remove(self, host, entry_id):
        sites = self.data["sites"]
        sites[host] = [x for x in sites.get(host, []) if x.get("id") != entry_id]
        if not sites[host]:
            del sites[host]
        self.save()

    def never(self, url):
        host = self.site_key(url)
        if host and host not in self.data["never_save"]:
            self.data["never_save"].append(host); self.save()

    def is_never(self, url):
        host = self.site_key(url)
        return bool(host and host in self.data["never_save"])

    def reveal(self, entry):
        pw = _dpapi_unprotect(entry["password_enc"])
        entry["last_used"] = _now_iso(); self.save()
        return pw

    def matches(self, entry, password):
        try:
            return _dpapi_unprotect(entry["password_enc"]) == password
        except Exception:
            return False


# ─────────────────────── Chrome-like manager dialog ─────────────────────────
def _pw_label(text, name=None):
    l = QLabel(text)
    if name:
        l.setObjectName(name)
    return l


class _PwEntryDialog(QDialog):
    def __init__(self, parent, title, site="", user="", pw=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(420, 170)
        v = QGridLayout(self)
        v.addWidget(QLabel("Site"), 0, 0);      self.site = QLineEdit(site)
        self.site.setPlaceholderText("example.com");   v.addWidget(self.site, 0, 1)
        v.addWidget(QLabel("Username"), 1, 0);  self.user = QLineEdit(user); v.addWidget(self.user, 1, 1)
        v.addWidget(QLabel("Password"), 2, 0);  self.pw = QLineEdit(pw)
        self.pw.setEchoMode(QLineEdit.Password);       v.addWidget(self.pw, 2, 1)
        show = QCheckBox("Show password")
        show.toggled.connect(lambda on: self.pw.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password))
        v.addWidget(show, 3, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        v.addWidget(bb, 4, 0, 1, 2)

    def values(self):
        return self.site.text().strip(), self.user.text().strip(), self.pw.text()


# ──────────────────────────────── find bar ──────────────────────────────────
class FindBar(QFrame):
    def __init__(self, browser):
        super().__init__(browser)
        self.browser = browser; self.setObjectName("FindBar")
        dark = getattr(browser, "dark_mode", False)
        self.setStyleSheet("QFrame#FindBar{background:%s;border:1px solid %s;border-radius:4px;}"
                           % ("#2B2B2B" if dark else "#FFFFFF", "#555" if dark else "#9A9A9A"))
        h = QHBoxLayout(self); h.setContentsMargins(6, 3, 6, 3); h.setSpacing(4)
        self.edit = QLineEdit(); self.edit.setPlaceholderText("Find on page")
        self.edit.setClearButtonEnabled(True); self.edit.setFixedWidth(220)
        nxt = QPushButton("Next")
        close = QToolButton(); close.setText("✕")
        h.addWidget(self.edit); h.addWidget(nxt); h.addWidget(close)
        nxt.clicked.connect(self.next_match)
        close.clicked.connect(self.hide)
        self.edit.returnPressed.connect(self.next_match)
        self.edit.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self.edit and ev.type() == QEvent.KeyRelease and ev.key() == Qt.Key_Escape:
            self.hide(); return True
        return False

    def open(self):
        tab = self.browser.current_tab()
        if tab is None:
            return
        self.adjustSize()
        tc = self.browser.findChild(QWidget, "ToolbarContainer")
        y = tc.geometry().bottom() + 2 if tc is not None else 4
        self.move(max(8, self.parentWidget().width() - self.width() - 28), y)
        self.show(); self.raise_(); self.edit.setFocus(); self.edit.selectAll()

    def next_match(self):
        tab = self.browser.current_tab()
        if tab is not None and self.edit.text():
            tab.view.findText(self.edit.text())


# ─────────────────────── universal keyboard routing ─────────────────────────
_FKEYS = {0x70 + i: Qt.Key_F1 + i for i in range(12)}


def _ext_qtkey(vk):
    if 0x30 <= vk <= 0x39: return Qt.Key_0 + (vk - 0x30)
    if 0x41 <= vk <= 0x5A: return Qt.Key_A + (vk - 0x41)
    if vk == 0x20: return Qt.Key_Space
    if vk == 0x0D: return Qt.Key_Return
    if vk == 0x08: return Qt.Key_Backspace
    if vk == 0x09: return Qt.Key_Tab
    if vk == 0x1B: return Qt.Key_Escape
    if vk in (0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28):
        return {0x21: Qt.Key_PageUp, 0x22: Qt.Key_PageDown, 0x23: Qt.Key_End,
                0x24: Qt.Key_Home, 0x25: Qt.Key_Left, 0x26: Qt.Key_Up,
                0x27: Qt.Key_Right, 0x28: Qt.Key_Down}[vk]
    if vk in _FKEYS: return _FKEYS[vk]
    if vk == 0xBB: return Qt.Key_Plus
    if vk == 0xBD: return Qt.Key_Minus
    if vk == 0xBC: return Qt.Key_Comma
    if vk == 0xBE: return Qt.Key_Period
    if vk == 0xBF: return Qt.Key_Slash
    return None


def _ext_key_text(vk, shift):
    if 0x41 <= vk <= 0x5A: return chr(vk) if shift else chr(vk + 32)
    if 0x30 <= vk <= 0x39: return chr(vk)
    if vk == 0x20: return " "
    return ""


def _ext_builtin_command(ctrl, shift, alt, vk):
    if ctrl and not alt:
        if not shift:
            if vk == 0x4C: return 'focus_address'      # Ctrl+L
            if vk == 0x45: return 'focus_search'       # Ctrl+E
            if vk == 0x44: return 'add_favorite'       # Ctrl+D
            if vk == 0x48: return 'history'            # Ctrl+H
            if vk == 0x4A: return 'downloads'          # Ctrl+J
            if vk == 0x4E: return 'new_window'         # Ctrl+N
            if vk == 0x50: return 'print'              # Ctrl+P
            if vk == 0x46: return 'find'               # Ctrl+F
            if vk == 0x52: return 'reload'             # Ctrl+R / Ctrl+F5
            if vk == 0x54: return 'new_tab'            # Ctrl+T
            if vk == 0x57: return 'close_tab'          # Ctrl+W
            if vk == 0x53: return 'save_page'          # Ctrl+S
            if vk == 0x55: return 'view_source'        # Ctrl+U
            if vk == 0x74: return 'reload'             # Ctrl+F5
            if vk == 0x2E: return 'delete_browsing_data'
            if vk in (0xBB, 0x6B): return 'zoom_in'
            if vk in (0xBD, 0x6D): return 'zoom_out'
            if vk in (0x30, 0x60): return 'zoom_reset'
            if 0x31 <= vk <= 0x38: return 'tab_%d' % (vk - 0x30)
            if vk == 0x39: return 'tab_last'
        else:
            if vk in (0x4E, 0x50): return 'inprivate'          # Ctrl+Shift+N / +P
            if vk == 0x4F: return 'password_manager'           # Ctrl+Shift+O
            if vk == 0x2E: return 'delete_browsing_data'       # Ctrl+Shift+Del
    elif alt and not ctrl and not shift:
        if vk == 0x25: return 'back'                    # Alt+Left
        if vk == 0x27: return 'forward'                 # Alt+Right
        if vk == 0x24: return 'home'                    # Alt+Home
    elif not ctrl and not alt and not shift:
        if vk == 0x74: return 'reload'                  # F5
        if vk == 0x7B: return 'devtools'                # F12
        if vk == 0x72: return 'find_next'               # F3
    return None


class GlobalKeyFilter(QAbstractNativeEventFilter):
    """See every raw Windows key message before WebView2 consumes it and turn
    the browser's shortcuts back on while a web page owns the keyboard."""
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    def nativeEventFilter(self, eventType, message):
        # PyQt5 >= 5.15.7 (sip >= 6) wraps the C++ `long *result` out-parameter,
        # so a reimplementation must return (handled, result).  Returning a bare
        # bool makes Qt abort every message with
        # "TypeError: invalid result from ... nativeEventFilter()".
        try:
            handled = self._filter_key_message(eventType, message)
        except BaseException:
            handled = False
        return (True, 0) if handled else (False, 0)

    def _filter_key_message(self, eventType, message):
        if eventType not in (b"windows_generic_MSG", "windows_generic_MSG"):
            return False
        msg = _wintypes.MSG.from_address(int(message))
        if msg.message not in (0x0100, 0x0104):          # WM_KEYDOWN / WM_SYSKEYDOWN
            return False
        vk = msg.wParam & 0xFFFFFFFF
        if vk in (0x10, 0x11, 0x12, 0x5B, 0x5C):         # modifier keys themselves
            return False
        pid = _wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(msg.hwnd, ctypes.byref(pid))
        if pid.value != os.getpid():
            return False
        if QApplication.activeWindow() is None:
            return False
        user32 = ctypes.windll.user32
        ctrl = bool(user32.GetKeyState(0x11) & 0x8000)
        shift = bool(user32.GetKeyState(0x10) & 0x8000)
        alt = bool(user32.GetKeyState(0x12) & 0x8000)
        if not (ctrl or alt or 0x70 <= vk <= 0x7B):      # plain typing: never touch
            return False
        win = QApplication.activeWindow()
        target = win if hasattr(win, "_ext_handle_key") else self.browser
        repeat = (msg.lParam >> 30) & 1
        return bool(target._ext_handle_key(ctrl, shift, alt, vk, repeat))


class _TabPwCtx:
    __slots__ = ("tab", "timer", "miss", "pair", "suggest_fid", "host")
    def __init__(self, tab):
        self.tab = tab; self.timer = None; self.miss = 0
        self.pair = None; self.suggest_fid = None; self.host = ""


# ─────────────────── methods mixed into the main window class ───────────────
class BrowserExtras:
    """Attached to IE11Nostalgia by install_ie11_extras() below."""

    # ---------- key routing ----------
    def _ext_handle_key(self, ctrl, shift, alt, vk, repeat=0):
        app = QApplication.instance()
        if ctrl and not shift and not alt and vk == 0x09:            # Ctrl+Tab
            self._ext_cycle(+1); return True
        if ctrl and shift and not alt and vk == 0x09:                # Ctrl+Shift+Tab
            self._ext_cycle(-1); return True
        if ctrl and shift and not alt and vk == 0x54:                # Ctrl+Shift+T
            self.reopen_closed_tab(); return True
        if not ctrl and not shift and not alt and vk == 0x7A:        # F11
            self.toggle_fullscreen(); return True
        mods = Qt.NoModifier
        if ctrl:  mods |= Qt.ControlModifier
        if shift: mods |= Qt.ShiftModifier
        if alt:   mods |= Qt.AltModifier
        qtkey = _ext_qtkey(vk)
        if qtkey is None:
            return False
        combo = (int(qtkey) | int(mods)) & 0xFFFFFFFF
        target = QApplication.focusWidget() or self
        ev = QKeyEvent(QEvent.KeyPress, qtkey, mods, _ext_key_text(vk, shift), bool(repeat), 1)
        # 1) replay into Qt so the app's own QShortcuts / QAction shortcuts fire
        for sc in app.findChildren(QShortcut):
            for seq in sc.keys():
                if seq.count() and (seq[0] & 0xFFFFFFFF) == combo:
                    QApplication.sendEvent(target, ev); return True
        for act in app.findChildren(QAction):
            seq = act.shortcut()
            if not seq.isEmpty() and seq.count() and (seq[0] & 0xFFFFFFFF) == combo:
                QApplication.sendEvent(target, ev); return True
        # 2) built-ins for the classics nobody bound yet
        cmd = _ext_builtin_command(ctrl, shift, alt, vk)
        if cmd:
            self.exec_browser_command(cmd); return True
        return False

    # ---------- tab helpers ----------
    def _ext_new_tab(self, url=NEW_TAB_URL, private=False):
        for name in ('new_tab', 'add_tab', 'open_new_tab', 'create_tab', 'new_browser_tab'):
            f = getattr(self, name, None)
            if callable(f):
                for args in ((url, private), (url,), ()):
                    try:
                        return f(*args)
                    except TypeError:
                        continue
        t = BrowserTab(self, url, is_private=private)
        i = self.stack.addWidget(t)
        self.tabbar.addTab("New tab")
        self.stack.setCurrentIndex(i); self.tabbar.setCurrentIndex(i)
        return t

    def reopen_closed_tab(self):
        while self._closed_tabs:
            url, title = self._closed_tabs.pop()
            if url and url not in (NEW_TAB_URL, 'about:blank'):
                t = self._ext_new_tab(url)
                try:
                    if t is not None and title:
                        self.tabbar.setTabText(self.stack.indexOf(t), title)
                except Exception:
                    pass
                self.status_label.setText("Reopened: %s" % (title or url))
                return
        self.status_label.setText("No recently closed tab")

    def record_closed_tab(self, tab):
        try:
            if tab is None or getattr(tab, 'is_private', False):
                return
            url = tab.view.url().toString()
            if not url or url in (NEW_TAB_URL, 'about:blank') or url.startswith('ie11-error'):
                return
            self._closed_tabs.append((url, tab.view.title() or url))
            del self._closed_tabs[:-25]
        except Exception:
            pass

    def _ext_cycle(self, step):
        n = self.stack.count()
        if n >= 2:
            self.tabbar.setCurrentIndex((self.tabbar.currentIndex() + step) % n)

    def _ext_goto_tab(self, n):
        count = self.stack.count()
        idx = count - 1 if n == 9 else min(n - 1, count - 1)
        if idx >= 0:
            self.tabbar.setCurrentIndex(idx)

    def _ext_on_tab_added(self, idx):
        w = self.stack.widget(idx)
        if w is None or w in self._tab_mirror:
            return
        while len(self._tab_mirror) < idx:
            self._tab_mirror.append(None)
        if len(self._tab_mirror) == idx:
            self._tab_mirror.append(w)
        else:
            self._tab_mirror.insert(idx, w)
        if isinstance(w, BrowserTab):
            self._pw_attach_tab(w)

    def _ext_on_tab_removed(self, idx):
        w = self._tab_mirror.pop(idx) if 0 <= idx < len(self._tab_mirror) else None
        if w is None:
            return
        ctx = self._pw_ctx.pop(w, None)
        if ctx and ctx.timer:
            ctx.timer.stop()
        self.record_closed_tab(w)

    # ---------- fullscreen ----------
    def toggle_fullscreen(self):
        if self.isFullScreen():
            for w in self._fs_hidden or []:
                try:
                    w.setVisible(True)
                except Exception:
                    pass
            self._fs_hidden = []
            (self.showMaximized if self._fs_prev_max else self.showNormal)()
        else:
            self._fs_prev_max = self.isMaximized()
            self._fs_hidden = []
            for w in self._ext_fullscreen_widgets():
                if w.isVisible():
                    self._fs_hidden.append(w); w.setVisible(False)
            self.showFullScreen()
            self._ext_toast("Press F11 to exit full screen")

    def _ext_fullscreen_widgets(self):
        out = []
        tc = self.findChild(QWidget, "ToolbarContainer")
        if tc is not None:
            out.append(tc)
        fb = self.findChild(QWidget, "FavoritesBar")
        if fb is not None:
            out.append(fb)
        for mb in self.findChildren(QMenuBar):
            out.append(mb)
        for sb in self.findChildren(QStatusBar):
            out.append(sb)
        if self._find_bar is not None and self._find_bar.isVisible():
            out.append(self._find_bar)
        return out

    def _ext_toast(self, text):
        lbl = getattr(self, '_toast', None)
        if lbl is None:
            lbl = QLabel(self); lbl.setObjectName("Toast"); lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("QLabel#Toast{background:#333;color:white;padding:8px 18px;"
                              "border-radius:16px;font-size:12px;}")
            self._toast = lbl
        lbl.setText(text); lbl.adjustSize()
        lbl.move((self.width() - lbl.width()) // 2, 24)
        lbl.show(); lbl.raise_()
        QTimer.singleShot(2800, lbl.hide)

    # ---------- command router ----------
    def exec_browser_command(self, cmd):
        tab = self.current_tab()
        view = getattr(tab, 'view', None)
        try:
            if cmd == 'new_tab':            self._ext_new_tab(); return
            if cmd == 'reopen_closed_tab':  self.reopen_closed_tab(); return
            if cmd == 'next_tab':           self._ext_cycle(+1); return
            if cmd == 'prev_tab':           self._ext_cycle(-1); return
            if cmd.startswith('tab_'):
                n = cmd.split('_')[1]
                self._ext_goto_tab(9 if n == 'last' else int(n)); return
            if cmd == 'focus_address':
                self.address_bar.setFocus(Qt.ShortcutFocusReason); self.address_bar.selectAll(); return
            if cmd == 'focus_search':
                sb = getattr(self, 'search_bar', None)
                (sb or self.address_bar).setFocus(Qt.ShortcutFocusReason)
                if sb: sb.selectAll()
                return
            if cmd == 'close_tab':
                for name in ('close_tab', 'close_current_tab', 'closeTab'):
                    f = getattr(self, name, None)
                    if callable(f):
                        for args in ((tab,), (self.tabbar.currentIndex(),), ()):
                            try:
                                return f(*args)
                            except TypeError:
                                continue
                return
            if view is None:
                return
            if cmd == 'reload':      view.reload(); return
            if cmd == 'back':        view.back(); return
            if cmd == 'forward':     view.forward(); return
            if cmd == 'home':        view.setUrl(QUrl(HOME_URL)); return
            if cmd == 'zoom_in':     view.setZoomFactor(min(5.0, view.zoomFactor() * 1.1)); return
            if cmd == 'zoom_out':    view.setZoomFactor(max(0.25, view.zoomFactor() / 1.1)); return
            if cmd == 'zoom_reset':  view.setZoomFactor(1.0); return
            if cmd == 'devtools':
                try: view.open_devtools()
                except Exception: pass
                return
            if cmd == 'print':
                try: view.printToPdf()
                except Exception: self.status_label.setText("Print is not available here")
                return
            if cmd == 'find':        self.show_find_bar(); return
            if cmd == 'find_next':
                if self._find_bar: self._find_bar.next_match()
                return
            if cmd == 'history':
                if not self._ext_open_dialog(('show_history', 'open_history', 'history_dialog')):
                    self.status_label.setText("History view is not wired up in this build")
                return
            if cmd == 'downloads':
                if not self._ext_open_dialog(('show_downloads', 'open_downloads', 'downloads_dialog')):
                    dlg = getattr(self, '_downloads_dialog', None)
                    if dlg is not None:
                        dlg.show(); dlg.raise_()
                return
            if cmd == 'add_favorite':      self._ext_add_favorite(tab); return
            if cmd == 'password_manager':  self.open_password_manager(); return
            if cmd == 'fullscreen':        self.toggle_fullscreen(); return
            if cmd == 'new_window':
                if not self._ext_call_new_window(HOME_URL):
                    self.open_new_window_url(HOME_URL)
                return
            if cmd == 'inprivate':
                for name in ('new_private_window', 'new_inprivate_window', 'open_private_window'):
                    f = getattr(self, name, None)
                    if callable(f):
                        for args in ((HOME_URL,), ()):
                            try:
                                return f(*args)
                            except TypeError:
                                continue
                self.status_label.setText("InPrivate window is not wired up in this build")
                return
            if cmd == 'save_page':
                for name in ('save_page', 'save_as', 'savePageAs'):
                    f = getattr(self, name, None)
                    if callable(f):
                        for args in ((tab,), ()):
                            try:
                                return f(*args)
                            except TypeError:
                                continue
                self.infobar.show_message(
                    "To save a page, press Ctrl+P and pick 'Microsoft Print to PDF'.", [])
                return
            if cmd == 'view_source':
                try: view.open_devtools(); return
                except Exception: return
            if cmd == 'delete_browsing_data':
                try: self.history.clear()
                except Exception: pass
                try: self.profile.cookieStore().deleteAllCookies()
                except Exception: pass
                try: self.profile.clearHttpCache()
                except Exception: pass
                self.infobar.show_message("Cookies, cache and browsing history have been cleared.", [])
                return
        except Exception as exc:
            try: self.status_label.setText("Command failed: %s" % exc)
            except Exception: pass

    def _ext_open_dialog(self, names):
        for name in names:
            f = getattr(self, name, None)
            if callable(f):
                try:
                    f(); return True
                except Exception:
                    continue
        return False

    def _ext_call_new_window(self, url):
        for name in ('new_window', 'open_new_window', 'new_browser_window'):
            f = getattr(self, name, None)
            if callable(f):
                for args in ((url,), ()):
                    try:
                        f(*args); return True
                    except TypeError:
                        continue
        return False

    def _ext_add_favorite(self, tab):
        if tab is None:
            return
        url = tab.view.url().toString()
        if not url.startswith(('http://', 'https://')):
            return
        title = tab.view.title() or url
        for name in ('add_favorite', 'add_to_favorites', 'bookmark_page'):
            f = getattr(self, name, None)
            if callable(f):
                for args in ((title, url), (url,), ()):
                    try:
                        return f(*args)
                    except TypeError:
                        continue
        text, ok = QInputDialog.getText(self, "Add to Favorites", "Name:", QLineEdit.Normal, title)
        if ok and text:
            self.add_favorite_direct(text, url)

    def show_find_bar(self):
        if self._find_bar:
            self._find_bar.open()

    def open_password_manager(self):
        dlg = getattr(self, '_pw_dialog', None)
        if dlg is not None and dlg.isVisible():
            dlg.raise_(); dlg.activateWindow(); return
        dlg = PasswordManagerDialog(self)
        self._pw_dialog = dlg
        dlg.show()

    # ---------- password-manager plumbing ----------
    def _run_js(self, view, script, callback=None):
        widget = getattr(view, 'widget', None)
        if widget is None:
            if callback: callback(None)
            return
        if callback is None:
            try: return widget.eval_js(script)
            except Exception: return None
        if hasattr(widget, 'evaluate_js'):
            try:
                widget.evaluate_js(script, callback); return
            except Exception:
                pass
        try:
            callback(widget.eval_js(script))
        except Exception:
            callback(None)

    @staticmethod
    def _pw_parse(res):
        if isinstance(res, dict):
            return res
        if isinstance(res, str):
            s = res.strip()
            if s.startswith('{'):
                try: return json.loads(s)
                except Exception: return None
        return None

    def _pw_attach_tab(self, tab):
        if tab is None or getattr(tab, '_pw_attached', False):
            return
        try:
            if tab.is_private:
                return
        except Exception:
            return
        tab._pw_attached = True
        try:
            tab.view.loadFinished.connect(lambda ok, t=tab: self._pw_on_loaded(t, ok))
        except Exception:
            pass
        try:
            url = tab.view.url().toString()
        except Exception:
            url = ''
        if url.startswith(('http://', 'https://')):
            self._pw_on_loaded(tab, True)

    def _pw_on_loaded(self, tab, ok=True):
        try:
            if tab.is_private:
                return
            url = tab.view.url().toString()
        except Exception:
            return
        if not url.startswith(('http://', 'https://')):
            self._pw_stop_poll(tab); return
        self._run_js(tab.view, PASSWORD_AGENT_JS)
        self._pw_ensure_poll(tab)
        self._pw_auto_sign_in(tab)

    def _pw_ensure_poll(self, tab):
        ctx = self._pw_ctx.get(tab)
        if ctx is None:
            ctx = self._pw_ctx[tab] = _TabPwCtx(tab)
        if ctx.timer is None:
            t = QTimer(self)
            t.timeout.connect(lambda c=ctx: self._pw_poll_tick(c))
            ctx.timer = t
        ctx.miss = 0
        ctx.timer.start(700)

    def _pw_stop_poll(self, tab):
        ctx = self._pw_ctx.pop(tab, None)
        if ctx and ctx.timer:
            ctx.timer.stop()

    def _pw_poll_tick(self, ctx):
        tab = ctx.tab
        try:
            if self.stack.indexOf(tab) < 0:
                self._pw_stop_poll(tab); return
        except Exception:
            self._pw_stop_poll(tab); return
        self._run_js(tab.view, "window.__ie11pw_poll?window.__ie11pw_poll():null",
                     lambda res, c=ctx, t=tab: self._pw_poll_result(t, c, res))

    def _pw_poll_result(self, tab, ctx, res):
        data = self._pw_parse(res)
        if not data:
            ctx.miss += 1
        else:
            events = data.get("events") or []
            fields = data.get("fields") or 0
            ctx.miss = 0 if (events or fields) else ctx.miss + 1
            for ev in events:
                try: self._pw_event(tab, ctx, ev)
                except Exception: pass
        if ctx.timer:
            ctx.timer.setInterval(500 if ctx.miss < 4 else 2000)

    def _pw_event(self, tab, ctx, ev):
        t = ev.get("type")
        if t == "suggest":
            self._pw_suggest(tab, ctx, ev.get("fid"))
        elif t == "pick":
            self._pw_pick(tab, ctx, ev.get("fid"), ev.get("username"))
        elif t == "submit":
            self._pw_offer_save(tab, ev.get("url") or tab.view.url().toString(),
                                ev.get("username") or "", ev.get("password") or "")
        elif t == "manage":
            self.open_password_manager()

    def _pw_suggest(self, tab, ctx, fid):
        if not fid:
            return
        url = tab.view.url().toString()
        if not url.startswith(('http://', 'https://')):
            return
        entries = self.vault.entries(url)
        if not entries:
            return                                   # nothing saved → no dropdown (Chrome behaviour)
        ctx.suggest_fid = fid
        ctx.host = self.vault.site_key(url) or url
        self._run_js(tab.view, "window.__ie11pw_cmd(%s)" % json.dumps({"op": "fields"}),
                     lambda res, c=ctx, f=fid, e=entries, t=tab: self._pw_suggest2(t, c, f, e, res))

    def _pw_suggest2(self, tab, ctx, fid, entries, res):
        data = self._pw_parse(res) or {}
        pairs = data.get("pairs") or []
        pair = next((p for p in pairs if p.get("pfid") == fid or p.get("ufid") == fid),
                    pairs[0] if pairs else None)
        ctx.pair = pair
        users = [{"username": (e.get("username") or "")} for e in entries]
        self._run_js(tab.view, "window.__ie11pw_cmd(%s)" % json.dumps(
            {"op": "show", "fid": fid, "users": users}))

    def _pw_pick(self, tab, ctx, fid, username):
        url = tab.view.url().toString()
        entries = self.vault.entries(url)
        if not entries:
            return
        entry = next((e for e in entries if (e.get("username") or "") == (username or "")), entries[0])
        host = self.vault.site_key(url) or url
        self._run_js(tab.view, "window.__ie11pw_cmd(%s)" % json.dumps({"op": "fields"}),
                     lambda res, c=ctx, f=fid: self._pw_pick2(tab, c, f, host, entry, res))

    def _pw_pick2(self, tab, ctx, fid, host, entry, res):
        if ctx.pair is None:
            data = self._pw_parse(res) or {}
            pairs = data.get("pairs") or []
            ctx.pair = next((p for p in pairs if p.get("pfid") == fid or p.get("ufid") == fid),
                            pairs[0] if pairs else {})
        self.hello.require(
            self, "Verify to fill the password for %s" % host,
            lambda ok, msg, c=ctx, f=fid, e=entry:
            self._pw_fill(tab, c, f, e) if ok else self.status_label.setText("Password fill canceled"))

    def _pw_fill(self, tab, ctx, fid, entry):
        try:
            password = self.vault.reveal(entry)
        except Exception as exc:
            self.status_label.setText("Could not decrypt saved password: %s" % exc); return
        pair = ctx.pair or {}
        cmd = json.dumps({"op": "fill", "fid": pair.get("pfid") or fid,
                          "ufid": pair.get("ufid"),
                          "username": entry.get("username") or "",
                          "password": password})
        self._run_js(tab.view, "window.__ie11pw_cmd(%s)" % cmd)
        self.status_label.setText("Password filled for %s" % (ctx.host or "site"))

    def _pw_auto_sign_in(self, tab):
        if not self.vault.data.get("auto_sign_in"):
            return
        url = tab.view.url().toString()
        entries = self.vault.entries(url)
        if not entries or not self.hello.unlocked():
            return
        self._run_js(tab.view, "window.__ie11pw_cmd(%s)" % json.dumps({"op": "fields"}),
                     lambda res, e=entries[0]: self._pw_auto_fill(tab, e, res))

    def _pw_auto_fill(self, tab, entry, res):
        data = self._pw_parse(res) or {}
        pairs = data.get("pairs") or []
        if not pairs:
            return
        try:
            password = self.vault.reveal(entry)
        except Exception:
            return
        ctx = self._pw_ctx.setdefault(tab, _TabPwCtx(tab))
        ctx.pair = pairs[0]
        cmd = json.dumps({"op": "fill", "fid": pairs[0].get("pfid"),
                          "ufid": pairs[0].get("ufid"),
                          "username": entry.get("username") or "", "password": password})
        self._run_js(tab.view, "window.__ie11pw_cmd(%s)" % cmd)

    def _pw_offer_save(self, tab, url, username, password):
        if not url.startswith(('http://', 'https://')) or not password:
            return
        if getattr(tab, 'is_private', False):
            return
        if not self.vault.data.get("offer_to_save", True):
            return
        host = self.vault.site_key(url)
        if not host or self.vault.is_never(url):
            return
        now = time.time()
        if self._pw_last_offer and self._pw_last_offer[:3] == (host, username, password) \
                and now - self._pw_last_offer[3] < 6:
            return
        self._pw_last_offer = (host, username, password, now)
        existing = self.vault.entries(url)
        if any(self.vault.matches(e, password) for e in existing if e.get("username") == username):
            return                                        # already saved, unchanged
        update = next((e for e in existing if e.get("username") == username), None)
        verb = "Update" if update else "Save"
        self.infobar.show_message(
            "%s password for %s?" % (verb, host),
            [("%s" % verb, lambda _=False, u=url, un=username, p=password, up=update:
              self._pw_do_save(u, un, p, up)),
             ("Never for this site", lambda _=False, u=url: self._pw_never(u))],
            options=[("Open password manager", self.open_password_manager)])

    def _pw_do_save(self, url, username, password, update=None):
        host = self.vault.site_key(url)
        if not host:
            return
        self.vault.add(url, username, password)
        try: self.infobar.hide()
        except Exception: pass
        self.status_label.setText("Password saved for %s" % host)
        dlg = getattr(self, '_pw_dialog', None)
        if dlg is not None and dlg.isVisible():
            dlg._refresh()

    def _pw_never(self, url):
        self.vault.never(url)
        try: self.infobar.hide()
        except Exception: pass
        self.status_label.setText("Passwords will not be saved on this site")

    # ---------- boot ----------
    def _ext_post_init(self):
        self._closed_tabs = []
        self._pw_ctx = {}
        self._pw_last_offer = None
        self._pw_dialog = None
        self._find_bar = None
        self._toast = None
        self._fs_hidden = []; self._fs_prev_max = False
        self._pw_hello_note = WindowsHello.availability()[1]
        self.vault = PasswordVault(os.path.join(self.data_dir, 'passwords.json'))
        self.hello = WindowsHello()
        self._tab_mirror = []
        try:
            self.stack.widgetAdded.connect(self._ext_on_tab_added)
            self.stack.widgetRemoved.connect(self._ext_on_tab_removed)
        except Exception:
            pass
        for i in range(self.stack.count()):
            self._ext_on_tab_added(i)
        # widen every existing QShortcut so it also fires when plain Qt widgets
        # hold focus anywhere in the app (native-WebView focus is handled below)
        for sc in self.findChildren(QShortcut):
            try: sc.setContext(Qt.ApplicationShortcut)
            except Exception: pass
        # the real fix: intercept raw key messages before WebView2 eats them
        self._key_filter = GlobalKeyFilter(self)
        QApplication.instance().installNativeEventFilter(self._key_filter)
        self._find_bar = FindBar(self)
        self._find_bar.hide()


def install_ie11_extras():
    """Wire everything into the main window class without editing its body."""
    if getattr(IE11Nostalgia, "_ie11_extras_installed", False):
        return
    IE11Nostalgia._ie11_extras_installed = True
    for name, val in list(vars(BrowserExtras).items()):
        if callable(val) and not name.startswith("__"):
            setattr(IE11Nostalgia, name, val)
    _orig_init = IE11Nostalgia.__init__

    def _patched_init(self, *a, **k):
        _orig_init(self, *a, **k)
        try:
            self._ext_post_init()
        except Exception:
            pass                      # never brick the browser over extras

    IE11Nostalgia.__init__ = _patched_init


install_ie11_extras()   # must run before the first IE11Nostalgia() is created

# ═══════════════════════════════════════════════════════════════════════════
#  Password manager v2 — entries can be opened, revealed and copied easily.
#  Paste BELOW the first feature-pack block (after install_ie11_extras())
#  and ABOVE `if __name__ == "__main__":`
# ═══════════════════════════════════════════════════════════════════════════


class _PwRow(QFrame):
    """Row that emits doubleClicked on a left double-click."""
    doubleClicked = pyqtSignal()

    def mouseDoubleClickEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            self.doubleClicked.emit()
        super().mouseDoubleClickEvent(ev)


class _PwDetailsDialog(QDialog):
    """Chrome-style 'Password details' sheet — view/reveal/copy/edit/remove."""

    def __init__(self, parent, browser, host, entry, on_changed):
        super().__init__(parent)
        self.browser, self.entry, self.on_changed = browser, entry, on_changed
        self.host = host
        self._real_pw = None
        self.setWindowTitle("Password details")
        self.setWindowIcon(browser.windowIcon())
        self.resize(480, 250)
        dark = getattr(browser, "dark_mode", False)
        fg = '#E8E8E8' if dark else '#202124'
        bg = '#1F1F1F' if dark else '#FFFFFF'
        sub = '#9AA0A6' if dark else '#5F6368'
        line = '#3A3F45' if dark else '#DADCE0'
        card = '#2B2F34' if dark else '#F1F3F4'
        self.setStyleSheet(
            "QDialog{background:%(bg)s;color:%(fg)s}"
            "QLabel{color:%(fg)s}QLabel#Sub{color:%(sub)s;font-size:11px}"
            "QLineEdit{background:%(card)s;border:1px solid %(line)s;border-radius:8px;padding:7px 12px;color:%(fg)s}"
            "QPushButton{background:%(card)s;border:1px solid %(line)s;border-radius:14px;padding:6px 16px;color:%(fg)s}"
            "QPushButton:hover{border-color:#8AB4F8}"
            % dict(bg=bg, fg=fg, sub=sub, line=line, card=card))

        grid = QGridLayout(self)
        grid.setContentsMargins(24, 20, 24, 16)
        grid.setHorizontalSpacing(14); grid.setVerticalSpacing(12)

        grid.addWidget(QLabel("Site"), 0, 0)
        self.site_lbl = QLabel(host)
        self.site_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        grid.addWidget(self.site_lbl, 0, 1)

        grid.addWidget(QLabel("Username"), 1, 0)
        user = QLabel(entry.get("username") or "(no username)")
        user.setTextInteractionFlags(Qt.TextSelectableByMouse)
        grid.addWidget(user, 1, 1)
        self.cu_btn = QPushButton("Copy"); self.cu_btn.clicked.connect(self._copy_user)
        grid.addWidget(self.cu_btn, 1, 2)

        grid.addWidget(QLabel("Password"), 2, 0)
        self.pw_lbl = QLabel("••••••••••")
        self.pw_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        grid.addWidget(self.pw_lbl, 2, 1)
        self.show_btn = QPushButton("Show password")
        self.show_btn.clicked.connect(self._toggle_show)
        grid.addWidget(self.show_btn, 2, 2)

        self.cp_btn = QPushButton("Copy password")
        self.cp_btn.clicked.connect(self._copy_pw)
        grid.addWidget(self.cp_btn, 3, 1)

        btns = QHBoxLayout()
        self.edit_btn = QPushButton("Edit…"); self.edit_btn.clicked.connect(self._edit)
        remove = QPushButton("Remove"); remove.clicked.connect(self._remove)
        done = QPushButton("Done"); done.setDefault(True); done.clicked.connect(self.accept)
        btns.addWidget(self.edit_btn); btns.addWidget(remove)
        btns.addStretch(1); btns.addWidget(done)
        grid.addLayout(btns, 4, 0, 1, 3)

    def _authed(self, reason, cb):
        if not self.browser.vault.data.get("require_auth", True):
            cb(True); return
        self.browser.hello.require(self, reason, lambda ok, msg: cb(ok))

    def _flash(self, btn, temp):
        old = btn.text(); btn.setText(temp)
        QTimer.singleShot(1200, lambda: btn.setText(old))

    def _toggle_show(self):
        if self._real_pw is not None:                       # shown → hide
            self._real_pw = None
            self.pw_lbl.setText("••••••••••")
            self.show_btn.setText("Show password")
            return
        def do(ok):
            if not ok:
                return
            try:
                self._real_pw = self.browser.vault.reveal(self.entry)
            except Exception as exc:
                QMessageBox.warning(self, "Password", "Could not decrypt: %s" % exc); return
            self.pw_lbl.setText(self._real_pw)
            self.show_btn.setText("Hide password")
        self._authed("Verify to show the password for %s" % self.host, do)

    def _copy_user(self):
        QApplication.clipboard().setText(self.entry.get("username") or "")
        self._flash(self.cu_btn, "Copied ✓")

    def _copy_pw(self):
        def do(ok):
            if not ok:
                return
            try:
                pw = self.browser.vault.reveal(self.entry)
            except Exception as exc:
                QMessageBox.warning(self, "Password", "Could not decrypt: %s" % exc); return
            QApplication.clipboard().setText(pw)
            self._flash(self.cp_btn, "Copied ✓")
            QTimer.singleShot(30000, lambda: QApplication.clipboard().setText(""))
        self._authed("Verify to copy the password for %s" % self.host, do)

    def _edit(self):
        def do(ok):
            if not ok:
                return
            try:
                pw = self.browser.vault.reveal(self.entry)
            except Exception as exc:
                QMessageBox.warning(self, "Password", "Could not decrypt: %s" % exc); return
            dlg = _PwEntryDialog(self, "Edit password", self.host,
                                 self.entry.get("username", ""), pw)
            if dlg.exec_() != QDialog.Accepted:
                return
            site, user, npw = dlg.values()
            if not site or not npw:
                QMessageBox.warning(self, "Password", "Site and password are required."); return
            new_host = self.browser.vault.site_key(site) or site
            self.browser.vault.update_entry(self.host, self.entry, new_host, user, npw)
            self.host = new_host
            self.site_lbl.setText(new_host)
            self.on_changed()
            self._flash(self.edit_btn, "Saved ✓")
        self._authed("Verify to edit this password", do)

    def _remove(self):
        if QMessageBox.question(self, "Remove password",
                                "Delete the password for %s?" % self.host) != QMessageBox.Yes:
            return
        self.browser.vault.remove(self.host, self.entry.get("id"))
        self.on_changed()
        self.accept()


class PasswordManagerDialog(QDialog):
    """chrome://password-manager, local edition — v2 with openable entries."""

    def __init__(self, browser):
        super().__init__(browser)
        self.browser = browser
        self._site_rows = {}
        self._footer_base = ""
        self.setWindowTitle("Passwords — Internet Explorer 11")
        self.setWindowIcon(browser.windowIcon())
        self.resize(680, 540); self.setMinimumSize(560, 420)
        dark = getattr(browser, "dark_mode", False)
        fg = '#E8E8E8' if dark else '#202124'; bg = '#1F1F1F' if dark else '#FFFFFF'
        sub = '#9AA0A6' if dark else '#5F6368'; card = '#2B2F34' if dark else '#F1F3F4'
        line = '#3A3F45' if dark else '#DADCE0'; inputbg = '#17191C' if dark else '#FFFFFF'
        self.setStyleSheet("""
          QDialog{background:%(bg)s;color:%(fg)s} QLabel{color:%(fg)s}
          QLabel#Title{font-size:20px;font-weight:700;padding:18px 24px 2px 24px;}
          QLabel#Muted{color:%(sub)s;font-size:11px;}
          QLineEdit{background:%(inputbg)s;border:1px solid %(line)s;border-radius:8px;padding:7px 12px;color:%(fg)s;}
          QCheckBox{spacing:8px;color:%(fg)s}
          QToolButton{border:none;border-radius:14px;background:transparent;color:%(fg)s;padding:2px;font-size:13px;}
          QToolButton:hover{background:%(card)s}
          QFrame#Row{border:1px solid %(line)s;border-radius:10px;background:%(bg)s;}
          QLabel#SiteHead{font-size:13px;font-weight:600;}
          QPushButton{background:%(card)s;border:1px solid %(line)s;border-radius:14px;padding:6px 16px;color:%(fg)s;}
          QPushButton:hover{border-color:#8AB4F8;}
          QFrame#Footer{border-top:1px solid %(line)s;}
          QMenu{background:%(card)s;color:%(fg)s;border:1px solid %(line)s;}
          QMenu::item:selected{background:#4B5158;}
          QScrollArea{border:none;background:transparent;}
        """ % dict(bg=bg, fg=fg, sub=sub, card=card, line=line, inputbg=inputbg))
        root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        header = QWidget(); hv = QVBoxLayout(header)
        hv.setContentsMargins(24, 16, 24, 10); hv.setSpacing(10)
        hv.addWidget(_pw_label("Passwords", "Title"))
        toggles = QHBoxLayout()
        self.cb_save = QCheckBox("Offer to save passwords")
        self.cb_save.setChecked(bool(self.browser.vault.data.get("offer_to_save", True)))
        self.cb_auto = QCheckBox("Auto sign-in")
        self.cb_auto.setChecked(bool(self.browser.vault.data.get("auto_sign_in", False)))
        self.cb_auth = QCheckBox("Require verification to show passwords")
        self.cb_auth.setChecked(bool(self.browser.vault.data.get("require_auth", True)))
        self.cb_save.toggled.connect(self._toggle_save)
        self.cb_auto.toggled.connect(self._toggle_auto)
        self.cb_auth.toggled.connect(self._toggle_auth)
        toggles.addWidget(self.cb_save); toggles.addWidget(self.cb_auto)
        toggles.addWidget(self.cb_auth); toggles.addStretch(1)
        hv.addLayout(toggles)
        srow = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Search passwords")
        self.search.textChanged.connect(self._refresh)
        add_btn = QPushButton(" Add password"); add_btn.clicked.connect(self._add_password)
        srow.addWidget(self.search, 1); srow.addWidget(add_btn)
        hv.addLayout(srow); root.addWidget(header)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        holder = QWidget(); self.list_v = QVBoxLayout(holder)
        self.list_v.setContentsMargins(24, 4, 24, 16); self.list_v.setSpacing(6)
        self.scroll.setWidget(holder); root.addWidget(self.scroll, 1)
        footer = QFrame(); footer.setObjectName("Footer")
        fh = QHBoxLayout(footer); fh.setContentsMargins(24, 8, 24, 8)
        self.footer_lbl = _pw_label("", "Muted"); fh.addWidget(self.footer_lbl); fh.addStretch(1)
        root.addWidget(footer)
        self._refresh()

    # ---- helpers -----------------------------------------------------------
    def _note(self, msg):
        self.footer_lbl.setText(msg)
        QTimer.singleShot(3500, lambda: self.footer_lbl.setText(self._footer_base))

    def _copy(self, text):
        QApplication.clipboard().setText(text or "")
        self._note("Copied to clipboard")

    def _authed(self, reason, cb):
        if not self.browser.vault.data.get("require_auth", True):
            cb(True); return
        self.browser.hello.require(self, reason, lambda ok, msg: cb(ok))

    def _toggle_save(self, on):
        self.browser.vault.data["offer_to_save"] = bool(on); self.browser.vault.save()

    def _toggle_auto(self, on):
        self.browser.vault.data["auto_sign_in"] = bool(on); self.browser.vault.save()

    def _toggle_auth(self, on):
        self.browser.vault.data["require_auth"] = bool(on); self.browser.vault.save()

    def _collapse(self, rows, show, arrow):
        for r in rows:
            r.setVisible(show)
        arrow.setText("▾" if show else "▸")

    # ---- rows --------------------------------------------------------------
    def _entry_row(self, host, e):
        row = _PwRow(); row.setObjectName("Row"); row.setCursor(Qt.PointingHandCursor)
        h = QHBoxLayout(row); h.setContentsMargins(12, 8, 8, 8); h.setSpacing(10)
        user = QLabel(e.get("username") or "(no username)"); user.setMinimumWidth(140)
        pw = QLabel("••••••••••")
        eye = QToolButton(); eye.setText("👁"); eye.setToolTip("Show / hide password")
        det = QToolButton(); det.setText("ⓘ"); det.setToolTip("Open details (double-click also works)")
        more = QToolButton(); more.setText("⋮"); more.setToolTip("More actions")
        h.addWidget(user, 1); h.addWidget(pw, 1); h.addWidget(eye); h.addWidget(det); h.addWidget(more)
        row.doubleClicked.connect(lambda hst=host, en=e: self.open_details(hst, en))
        eye.clicked.connect(lambda _=False, l=pw, b=eye, hst=host, en=e: self._toggle_pw(l, b, hst, en))
        det.clicked.connect(lambda _=False, hst=host, en=e: self.open_details(hst, en))
        menu = QMenu(self)
        menu.addAction("Open details").triggered.connect(
            lambda hst=host, en=e: self.open_details(hst, en))
        menu.addAction("Copy username").triggered.connect(
            lambda un=e.get("username", ""): self._copy(un))
        menu.addAction("Copy password").triggered.connect(
            lambda hst=host, en=e: self._copy_pw_authed(hst, en))
        menu.addAction("Edit password…").triggered.connect(
            lambda hst=host, en=e: self.open_details(hst, en))
        menu.addSeparator()
        menu.addAction("Remove").triggered.connect(
            lambda hst=host, en=e: self._remove(hst, en))
        more.setMenu(menu); more.setPopupMode(QToolButton.InstantPopup)
        return row

    def _refresh(self, *_):
        self._site_rows.clear()
        while self.list_v.count():
            it = self.list_v.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        q = self.search.text().strip().lower()
        sites = self.browser.vault.data.get("sites", {})
        n = 0
        for host in sorted(sites):
            entries = [e for e in sites[host]
                       if not q or q in host.lower() or q in (e.get("username") or "").lower()]
            if not entries:
                continue
            n += len(entries)
            head = _PwRow()
            hh = QHBoxLayout(head); hh.setContentsMargins(2, 10, 2, 2); hh.setSpacing(8)
            av = QLabel((host[:1] or "?").upper()); av.setFixedSize(26, 26)
            av.setAlignment(Qt.AlignCenter)
            av.setStyleSheet("background:#1A73E8;color:white;border-radius:13px;font-weight:700;")
            arrow = QToolButton(); arrow.setText("▾")
            arrow.setCheckable(True); arrow.setChecked(True)
            hh.addWidget(av); hh.addWidget(_pw_label(host, "SiteHead")); hh.addStretch(1)
            hh.addWidget(_pw_label("%d saved" % len(entries), "Muted")); hh.addWidget(arrow)
            rows = []
            head.doubleClicked.connect(arrow.toggle)
            arrow.toggled.connect(lambda on, rs=rows, a=arrow: self._collapse(rs, on, a))
            self.list_v.addWidget(head)
            for e in entries:
                r = self._entry_row(host, e)
                rows.append(r)
                self.list_v.addWidget(r)
            self._site_rows[host] = rows
        if n == 0:
            empty = QLabel("No passwords saved yet.\nWhen you sign in to a website, "
                           "Internet Explorer 11 will offer to save it.")
            empty.setAlignment(Qt.AlignCenter); empty.setObjectName("Muted")
            self.list_v.addWidget(empty)
        self._footer_base = "%d password%s saved · %s" % (
            n, "" if n == 1 else "s", getattr(self.browser, "_pw_hello_note", ""))
        self.footer_lbl.setText(self._footer_base)

    # ---- actions -----------------------------------------------------------
    def open_details(self, host, e):
        _PwDetailsDialog(self, self.browser, host, e, self._refresh).exec_()

    def _toggle_pw(self, pw_lbl, eye, host, e):
        if getattr(pw_lbl, "_real", None) is not None:      # currently shown → hide
            pw_lbl._real = None
            pw_lbl.setText("••••••••••"); eye.setText("👁")
            return
        def do(ok):
            if not ok:
                self._note("Verification canceled"); return
            try:
                pw = self.browser.vault.reveal(e)
            except Exception as exc:
                self._note("Could not decrypt: %s" % exc); return
            pw_lbl._real = pw
            pw_lbl.setText(pw); eye.setText("🙈")
        self._authed("Verify to show the password for %s" % host, do)

    def _copy_pw_authed(self, host, e):
        def do(ok):
            if not ok:
                self._note("Verification canceled"); return
            try:
                pw = self.browser.vault.reveal(e)
            except Exception as exc:
                self._note("Could not decrypt: %s" % exc); return
            QApplication.clipboard().setText(pw)
            self._note("Password copied — clipboard clears in 30 s")
            QTimer.singleShot(30000, lambda: QApplication.clipboard().setText(""))
        self._authed("Verify to copy the password for %s" % host, do)

    def _remove(self, host, e):
        if QMessageBox.question(self, "Remove password",
                                "Delete the password for %s?" % host) != QMessageBox.Yes:
            return
        self.browser.vault.remove(host, e.get("id"))
        self._refresh(); self._note("Password removed")

    def _add_password(self):
        dlg = _PwEntryDialog(self, "Add password")
        if dlg.exec_() != QDialog.Accepted:
            return
        site, user, pw = dlg.values()
        if not site or not pw:
            self._note("Site and password are required"); return
        self.browser.vault.add(site, user, pw)
        self._refresh(); self._note("Password saved")

    def showEvent(self, ev):
        self._refresh(); super().showEvent(ev)

if __name__ == "__main__":
    if hasattr(Qt, "AA_ShareOpenGLContexts"):
        QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    app.setApplicationName("IE11 Nostalgia")
    app.setFont(QFont("Segoe UI", 9))
    app.setWindowIcon(load_ie_icon())
    splash_pm = QPixmap(320, 180); splash_pm.fill(QColor("#f7f7f7"))
    splash = QSplashScreen(splash_pm, Qt.FramelessWindowHint)
    splash.showMessage("\n\n\nInternet Explorer 11\nNostalgia Edition\n\nLoading...", Qt.AlignCenter, QColor("#176fae"))
    splash.setWindowIcon(load_ie_icon()); splash.show(); app.processEvents()
    window = IE11Nostalgia()
    window.show()
    QTimer.singleShot(1200, splash.close)
    sys.exit(app.exec_())
