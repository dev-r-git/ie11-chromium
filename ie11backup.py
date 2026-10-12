"""
Internet Explorer 11 — Nostalgia Edition (full version)
A fan-made browser with the classic IE11 desktop UI, using Microsoft Edge WebView2 via QtWebView2.

Install:
    py -m pip install PyQt5
    py -m pip install --pre qtwebview2

Run:
    py backuppy.py

Optional: place ie11.ico (or ie11.png) next to this file to use it as the app icon.
"""
import sys
import os
import json
import threading
from urllib.parse import quote_plus, urlsplit
from urllib.request import urlopen, Request
import http.client
import queue
import threading

from PyQt5.QtCore import (Qt, QUrl, QPoint, QPointF, QRect, QRectF, QSize, QTimer, QEvent,
                          QObject, pyqtSignal, QStandardPaths)
from PyQt5.QtGui import (QKeySequence, QFont, QColor, QBrush, QIcon, QPainter,
                         QPen, QPixmap, QPolygonF, QDesktopServices)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QToolButton, QMenu, QAction, QLabel,
    QTabBar, QTabWidget, QStackedWidget, QStatusBar, QProgressBar, QMessageBox,
    QInputDialog, QDialog, QShortcut, QListWidget, QListWidgetItem, QFrame,
    QFileDialog, QTreeWidget, QTreeWidgetItem, QMenuBar, QHeaderView)
from qtwebview2 import QtWebViewWidget, PageLoadEvent

HOME_URL = "https://msn.com"
BING_SEARCH_URL = "https://www.bing.com/search?q="
SUGGEST_URL = "https://api.bing.com/osjson.aspx?query="
_s = urlsplit(SUGGEST_URL)
_BING_SUGGEST_HOST = _s.netloc
_BING_SUGGEST_PATH = _s.path + ("?" + _s.query if _s.query else "")
NEW_TAB_URL = "ie11://newtab"


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
BACK_BUTTON_SIZE = 46
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
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser=browser; self._url=QUrl('about:blank'); self._title=''; self._icon=QIcon()
        self._history=[]; self._history_index=-1; self._zoom=1.0; self._last_progress=0
        self.widget=QtWebViewWidget(parent=self, user_data_folder=os.path.join(browser.data_dir,'webview2'),
            debug=True, lazyload=False, download_started_handler=self._download_started,
            download_completed_handler=self._download_completed)
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0); layout.addWidget(self.widget)
        browser.profile.views.append(self)
        self.widget.signals.navigation_requested.connect(self._on_navigation)
        self.widget.signals.title_changed.connect(self._on_title)
        self.widget.signals.page_loaded.connect(self._on_loaded)
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
    def setUrl(self, url):
        self._url=url if isinstance(url,QUrl) else QUrl(str(url)); self.widget.load_url(self._url.toString())
    def setHtml(self, html, base_url=None):
        # Resolve the optional logo locally before loading HTML in WebView2.
        if base_url:
            try:
                base = base_url.toLocalFile() if isinstance(base_url,QUrl) else str(base_url)
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
    def __init__(self, browser, url=NEW_TAB_URL):
        super().__init__()
        self.browser=browser
        self.view=BrowserViewAdapter(browser,self)
        self.page=self.view
        layout=QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0); layout.addWidget(self.view)
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


class IE11Nostalgia(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Internet Explorer")
        self.setWindowIcon(load_ie_icon())
        self.resize(1250, 790)
        self.setMinimumSize(780, 500)
        self.data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        if not self.data_dir:
            self.data_dir = os.path.join(os.path.expanduser("~"), ".ie11_nostalgia")
        os.makedirs(self.data_dir, exist_ok=True)
        self.state_file = os.path.join(self.data_dir, "browser_state.json")
        self.dark_mode = False
        self.suggestions_enabled = True
        self.favorites = [("🌐  Bing", "https://www.bing.com/"), ("🌐  MSN", HOME_URL)]
        self.history = []
        self.closed_tabs = []
        self.downloads = []
        self.download_records = []
        self._suggest_token = 0
        self._load_state()
        self.profile = _Profile()
        self.profile.setPersistentStoragePath(os.path.join(self.data_dir, "webdata"))
        self.profile.setCachePath(os.path.join(self.data_dir, "cache"))
        os.makedirs(self.profile.persistentStoragePath(), exist_ok=True)
        os.makedirs(self.profile.cachePath(), exist_ok=True)
        self._build_ui()
        self._apply_theme()
        self._connect_downloads()
        self.add_tab(HOME_URL)

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
        col = QVBoxLayout(toolbar)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

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
        self.favicon_label = QLabel("🌐")
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
        self.addr_drop = QToolButton()
        self.addr_drop.setObjectName("AddressDrop")
        self.addr_drop.setText("▾")
        self.addr_drop.setToolTip("View recent sites")
        self.addr_drop.setCursor(Qt.PointingHandCursor)
        self.addr_drop.clicked.connect(self.show_address_dropdown)
        ah.addWidget(self.favicon_label)
        ah.addWidget(self.address_bar, 1)
        ah.addWidget(self.lock_label)
        ah.addWidget(self.addr_drop)
        ar.addWidget(self.address_frame, 1)

        self.refresh_btn = QToolButton()
        self.refresh_btn.setObjectName("CommandButton")
        self.refresh_btn.setText("⟳")
        self.refresh_btn.setFixedSize(32, 28)
        self.refresh_btn.setToolTip("Refresh (F5)")
        self.refresh_btn.clicked.connect(self.reload_page)
        ar.addWidget(self.refresh_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#D0D0D0;")
        ar.addWidget(sep)

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
        ts.addWidget(self.home_btn)

        self.star_btn = QToolButton()
        self.star_btn.setObjectName("CommandButton")
        self.star_btn.setText("★")
        self.star_btn.setFixedSize(34, 28)
        self.star_btn.setToolTip("View your favorites")
        self.star_btn.setStyleSheet(
            "QToolButton { color:#D89B00; } QToolButton:hover { color:#B37700; }")
        self.star_btn.clicked.connect(self.toggle_favorites_center)
        ts.addWidget(self.star_btn)

        self.tools_btn = QToolButton()
        self.tools_btn.setObjectName("CommandButton")
        self.tools_btn.setText("⚙")
        self.tools_btn.setFixedSize(34, 28)
        self.tools_btn.setToolTip("Tools")
        self.tools_btn.setPopupMode(QToolButton.InstantPopup)
        ts.addWidget(self.tools_btn)

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
        ts.addWidget(self.smile_btn)
        col.addWidget(tabstrip)

        # ---- Favorites bar (the bookmark bar) ----
        self.fav_bar = QWidget()
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

        # ---- Hidden classic menu bar (File / View / Favorites / Tools / Help) ----
        self._build_menu_bar()

        # ---- Keyboard shortcuts ----
        self._shortcuts = []
        self.add_shortcut("Ctrl+L", self.focus_address)
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
        feeds = QLabel("This page has no feeds.\n\nFeeds let you follow updates\n"
                       "from your favorite websites.")
        feeds.setWordWrap(True)
        feeds.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        feeds.setStyleSheet("color:#777777; background:transparent; padding:8px;")
        self.hist_tree = QTreeWidget()
        self.hist_tree.setHeaderHidden(True)
        self.hist_tree.itemDoubleClicked.connect(
            lambda item, col=0: self.navigate(item.data(0, Qt.UserRole)))
        self.center_tabs.addTab(self.fav_tree, "Favorites")
        self.center_tabs.addTab(feeds, "Feeds")
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

    def add_tab(self, url=NEW_TAB_URL, focus_address=False):
        tab = BrowserTab(self, url)
        idx = self.stack.addWidget(tab)
        self.tabbar.addTab("New tab")
        self.tabbar.setCurrentIndex(idx)
        self.update_new_tab_icon()
        if focus_address:
            self.focus_address()

    def create_popup_page(self):
        self.add_tab(NEW_TAB_URL)
        return self.current_tab().page

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
        if tab.is_custom_new_tab and url.scheme() in ("http", "https"):
            tab.is_custom_new_tab = False
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
            self.tabbar.setTabText(index, label[:24])
            if tab is self.current_tab():
                self.setWindowTitle((label + " - Internet Explorer") if label else "Internet Explorer")

    def on_load_progress(self, tab, progress):
        if tab is self.current_tab():
            self.progress.show()
            self.progress.setValue(progress)
            self.status_label.setText(f"Opening page… {progress}%")

    def on_load_finished(self, tab, ok):
        if tab is self.current_tab():
            self.progress.hide()
            self.status_label.setText("Done" if ok else "Internet Explorer cannot display the webpage")
            self.update_navigation_state()
        if ok:
            url = tab.view.url().toString()
            if url and not url.startswith("about:"):
                self.history.append((tab.view.title() or url, url))
                self.history = self.history[-500:]
                self.save_state()

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
        scheme = (url or (self.current_view().url() if self.current_view() else QUrl())).scheme()
        if scheme == "file":
            self.zone_label.setText("Local intranet | Protected Mode: Off")
        else:
            self.zone_label.setText("Internet | Protected Mode: On")

    def update_zoom_label(self):
        view = self.current_view()
        pct = int(round(view.zoomFactor() * 100)) if view else 100
        self.zoom_btn.setText(f"{pct}%")

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
            self.suggest_popup.hide()
        view = self.current_view()
        if view:
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
        self.suggest_popup.populate(self.address_bar.text(), want_bing=False)
        self.suggest_popup.show_at(self.address_frame)

    def _on_address_typed(self, text):
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
            self.update_zoom_label()

    def set_zoom(self, value):
        view = self.current_view()
        if view:
            view.setZoomFactor(value)
            self.update_zoom_label()

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

    # ------------------------------------------------------------------
    # Theme / state
    # ------------------------------------------------------------------
    def _apply_theme(self):
        self.setStyleSheet(DARK_QSS if self.dark_mode else LIGHT_QSS)
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
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def _escape_pressed(self):
        if self.suggest_popup.isVisible():
            self.suggest_popup.hide()
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
        except (OSError, ValueError, TypeError):
            pass

    def save_state(self):
        try:
            with open(self.state_file, "w", encoding="utf-8") as handle:
                json.dump({"favorites": self.favorites, "history": self.history[-500:],
                           "downloads": self.downloads[-200:], "dark_mode": self.dark_mode,
                           "suggestions": self.suggestions_enabled},
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
                            self.suggest_popup.hide()
            elif event.type() == QEvent.WindowDeactivate:
                self.suggest_popup.hide()

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
                        self.suggest_popup.hide()
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
        if hasattr(self, "suggest_popup") and self.suggest_popup.isVisible():
            self.suggest_popup.show_at()

    def add_shortcut(self, sequence, callback):
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.setContext(Qt.ApplicationShortcut)
        shortcut.activated.connect(callback)
        self._shortcuts.append(shortcut)

    def closeEvent(self, event):
        self.save_state()
        event.accept()


if __name__ == "__main__":
    if hasattr(Qt, "AA_ShareOpenGLContexts"):
        QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    app.setApplicationName("IE11 Nostalgia")
    app.setFont(QFont("Segoe UI", 9))
    app.setWindowIcon(load_ie_icon())
    window = IE11Nostalgia()
    window.show()
    sys.exit(app.exec_())
