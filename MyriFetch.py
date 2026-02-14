import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import os
import json
import threading
import time
from urllib.parse import unquote, quote
from PIL import Image
import urllib3
import shutil
import traceback
import subprocess
import platform
import sys
import re
import webbrowser
from datetime import datetime

# Windows sound import (conditional)
try:
    import winsound
except ImportError:
    winsound = None

# App Configuration
ctk.set_appearance_mode('Dark')
ctk.set_default_color_theme('dark-blue')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

APP_NAME = 'MyriFetch'

if os.name == 'nt':
    APP_DATA = os.path.join(os.environ['APPDATA'], APP_NAME)
else:
    APP_DATA = os.path.join(os.path.expanduser('~'), '.config', APP_NAME)

if not os.path.exists(APP_DATA):
    try:
        os.makedirs(APP_DATA, exist_ok=True)
    except Exception as e:
        print(f"Failed to create config folder: {e}")

# Mappings
LB_NAMES = {
    'PlayStation 3': 'Sony Playstation 3',
    'PlayStation 2': 'Sony Playstation 2',
    'GameCube': 'Nintendo GameCube',
    'Wii': 'Nintendo Wii',
    'Dreamcast': 'Sega Dreamcast',
    'Xbox': 'Microsoft Xbox',
    'PSP': 'Sony PSP',
    'PlayStation 1': 'Sony Federation',
    'SNES': 'Super Nintendo (SNES)',
    'GBA': 'Nintendo Game Boy Advance',
    'Nintendo DS': 'Nintendo DS',
    'Nintendo 3DS': 'Nintendo 3DS'
}

CONSOLES = {
    'PlayStation 3': 'Redump/Sony - PlayStation 3/',
    'PlayStation 2': 'Redump/Sony - PlayStation 2/',
    'GameCube': 'Redump/Nintendo - GameCube - NKit RVZ [zstd-19-128k]/',
    'Wii': 'Redump/Nintendo - Wii - NKit RVZ [zstd-19-128k]/',
    'Dreamcast': 'Redump/Sega - Dreamcast/',
    'Xbox': 'Redump/Microsoft - Xbox/',
    'PSP': 'Redump/Sony - PlayStation Portable/',
    'PlayStation 1': 'Redump/Sony - PlayStation/',
    'SNES': 'No-Intro/Nintendo - Super Nintendo Entertainment System/',
    'GBA': 'No-Intro/Nintendo - Game Boy Advance/',
    'Nintendo DS': 'No-Intro/Nintendo - Nintendo DS (Decrypted)/',
    'Nintendo 3DS': 'No-Intro/Nintendo - Nintendo 3DS (Decrypted)/'
}

SHORT_NAMES = {
    'PlayStation 3': 'PS3',
    'PlayStation 2': 'PS2',
    'PlayStation 1': 'PS1',
    'GameCube': 'GameCube',
    'Wii': 'Wii',
    'Dreamcast': 'Dreamcast',
    'Xbox': 'Xbox',
    'PSP': 'PSP',
    'SNES': 'SNES',
    'GBA': 'GBA',
    'Nintendo DS': 'NDS',
    'Nintendo 3DS': '3DS'
}

CONFIG_FILE = os.path.join(APP_DATA, 'myrient_ultimate.json')
ICON_DIR = os.path.join(APP_DATA, 'icons')
BASE_URL = 'https://myrient.erista.me/files/'
NUM_THREADS = 4

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': '*/*',
    'Referer': 'https://myrient.erista.me/',
    'Origin': 'https://myrient.erista.me',
    'Connection': 'keep-alive'
}

THEMES = {
    'Cyber Dark': {
        'bg': '#09090b', 'card': '#18181b', 'cyan': '#00f2ff',
        'pink': '#ff0055', 'text': '#ffffff', 'dim': '#71717a', 'success': '#00e676'
    },
    'Gruvbox': {
        'bg': '#282828', 'card': '#3c3836', 'cyan': '#d79921',
        'pink': '#cc241d', 'text': '#ebdbb2', 'dim': '#a89984', 'success': '#98971a'
    },
    'Matrix': {
        'bg': '#000000', 'card': '#111111', 'cyan': '#00ff41',
        'pink': '#008f11', 'text': '#e0e0e0', 'dim': '#333333', 'success': '#003b00'
    },
    'Nord': {
        'bg': '#2e3440', 'card': '#3b4252', 'cyan': '#88c0d0',
        'pink': '#bf616a', 'text': '#eceff4', 'dim': '#4c566a', 'success': '#a3be8c'
    }
}

C = THEMES['Cyber Dark'].copy()

class RAManager:
    def __init__(self, username, api_key):
        self.username = username
        self.api_key = api_key
        self.base_url = "https://retroachievements.org/API/"

    def get_user_summary(self):
        if not self.username or not self.api_key: 
            return "Missing Credentials", None
        params = {'z': self.username, 'y': self.api_key, 'u': self.username}
        try:
            r = requests.get(f"{self.base_url}API_GetUserSummary.php", params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if "error" in data:
                    return data["error"], None
                return None, data
            return f"Server Error ({r.status_code})", None
        except Exception as e:
            return str(e), None

class TwitchManager:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.expires_at = 0
        
    def authenticate(self):
        if not self.client_id or not self.client_secret: return False
        try:
            r = requests.post('https://id.twitch.tv/oauth2/token', params={
                'client_id': self.client_id, 'client_secret': self.client_secret, 'grant_type': 'client_credentials'
            }, timeout=10)
            r.raise_for_status()
            data = r.json()
            self.access_token = data['access_token']
            self.expires_at = time.time() + data['expires_in']
            return True
        except: return False

    def get_headers(self):
        if not self.access_token or time.time() >= self.expires_at:
            if not self.authenticate(): return None
        return {'Client-ID': self.client_id, 'Authorization': f'Bearer {self.access_token}', 'Accept': 'application/json'}

    def search_game(self, query):
        headers = self.get_headers()
        if not headers: return None
        try:
            r = requests.post("https://api.igdb.com/v4/games", headers=headers, 
                            data=f'search "{query}"; fields name, cover.url, summary, first_release_date, genres.name, involved_companies.company.name; limit 1;', timeout=10)
            r.raise_for_status()
            data = r.json()
            if data: return data[0]
            return None
        except: return None


class GameTooltip(ctk.CTkToplevel):
    def __init__(self, parent, title, details, x, y):
        super().__init__(parent)
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.geometry(f"+{x+15}+{y+15}")
        self.frame = ctk.CTkFrame(self, fg_color=C['bg'], border_width=1, border_color=C['cyan'])
        self.frame.pack()
        ctk.CTkLabel(self.frame, text=title, font=('Arial', 14, 'bold'), text_color=C['cyan']).pack(anchor='w', padx=10, pady=(10, 5))
        for label, value in details.items():
            row = ctk.CTkFrame(self.frame, fg_color='transparent')
            row.pack(fill='x', padx=10, pady=1)
            ctk.CTkLabel(row, text=f"{label}: ", font=('Arial', 12, 'bold'), text_color=C['dim']).pack(side='left')
            ctk.CTkLabel(row, text=value, font=('Arial', 12), text_color='white', wraplength=300, justify='left').pack(side='left')
        ctk.CTkLabel(self.frame, text=" ", font=('Arial', 2)).pack()


class CustomPopup(ctk.CTkToplevel):
    def __init__(self, parent, title, message, buttons=('OK',)):
        super().__init__(parent)
        self.title(title)
        self.result = None
        w, h = 400, 200
        x = parent.winfo_x() + parent.winfo_width() // 2 - w // 2
        y = parent.winfo_y() + parent.winfo_height() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color=C['bg'])
        label = ctk.CTkLabel(self, text=message, wraplength=350, font=('Arial', 14), text_color=C['text'])
        label.pack(pady=(40, 20), padx=20, fill='both', expand=True)
        btn_frame = ctk.CTkFrame(self, fg_color='transparent')
        btn_frame.pack(pady=(0, 20))
        for btn_text in buttons:
            btn = ctk.CTkButton(btn_frame, text=btn_text, command=lambda b=btn_text: self.on_btn(b),
                fg_color=C['cyan'], text_color='black', hover_color=C['pink'], width=100)
            btn.pack(side='left', padx=10)
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def on_btn(self, text):
        self.result = text
        self.destroy()


class ThemedDirBrowser(ctk.CTkToplevel):
    def __init__(self, parent, title="Select Folder", initial_dir=None):
        super().__init__(parent)
        self.title(title)
        self.result = None
        self.parent = parent
        w, h = 550, 700
        x = parent.winfo_x() + parent.winfo_width() // 2 - w // 2
        y = parent.winfo_y() + parent.winfo_height() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(fg_color=C['bg'])
        if initial_dir and os.path.exists(initial_dir): self.current_dir = os.path.abspath(initial_dir)
        else: self.current_dir = os.path.expanduser("~")
        
        header = ctk.CTkFrame(self, fg_color='transparent')
        header.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(header, text="⬆ Up", width=60, command=self.go_up, fg_color=C['card'], hover_color=C['dim']).pack(side='left', padx=(0, 5))
        self.path_var = tk.StringVar(value=self.current_dir)
        self.entry = ctk.CTkEntry(header, textvariable=self.path_var, fg_color=C['card'], text_color='white', border_color=C['dim'])
        self.entry.pack(side='left', fill='x', expand=True, padx=5)
        self.entry.bind('<Return>', self.on_enter_path)
        ctk.CTkButton(header, text="Go", width=40, command=self.on_enter_path, fg_color=C['cyan'], text_color='black').pack(side='left', padx=5)
        
        if os.name == 'nt':
            self.drives = self.get_drives()
            current_drive = os.path.splitdrive(self.current_dir)[0] + '\\'
            self.drive_var = tk.StringVar(value=current_drive)
            if self.drives:
                ctk.CTkOptionMenu(header, variable=self.drive_var, values=self.drives, command=self.change_drive, width=70, fg_color=C['card'], button_color=C['dim']).pack(side='left', padx=5)
        
        toolbar = ctk.CTkFrame(self, fg_color='transparent', height=30)
        toolbar.pack(fill='x', padx=15, pady=(0, 5))
        ctk.CTkButton(toolbar, text="+ New Folder", width=100, height=24, font=('Arial', 11), fg_color=C['card'], hover_color=C['dim'], command=self.create_folder).pack(side='left')
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=C['card'])
        self.scroll.pack(fill='both', expand=True, padx=10, pady=5)
        self.bind_scroll(self.scroll, self.scroll)
        
        footer = ctk.CTkFrame(self, fg_color='transparent')
        footer.pack(fill='x', padx=10, pady=10)
        ctk.CTkButton(footer, text="Cancel", fg_color=C['pink'], hover_color='#990033', width=100, command=self.destroy).pack(side='right', padx=5)
        ctk.CTkButton(footer, text="Select This Folder", fg_color=C['success'], text_color='black', hover_color='#00b359', width=150, command=self.select_current).pack(side='right', padx=5)
        self.refresh_list()
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def bind_scroll(self, widget, target_frame):
        widget.bind("<Button-4>", lambda e, t=target_frame: self._on_mouse_scroll(e, t, -1))
        widget.bind("<Button-5>", lambda e, t=target_frame: self._on_mouse_scroll(e, t, 1))
        widget.bind("<MouseWheel>", lambda e, t=target_frame: self._on_mouse_scroll(e, t, 0))

    def _on_mouse_scroll(self, event, widget, direction):
        if direction == 0: widget._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else: widget._parent_canvas.yview_scroll(direction, "units")

    def get_drives(self):
        drives = []
        for x in range(65, 91):
            drive = chr(x) + ":\\"
            if os.path.exists(drive): drives.append(drive)
        return drives

    def change_drive(self, drive):
        self.current_dir = drive
        self.path_var.set(self.current_dir)
        self.refresh_list()

    def go_up(self):
        parent = os.path.dirname(self.current_dir)
        if parent == self.current_dir: return
        self.current_dir = parent
        self.path_var.set(self.current_dir)
        self.refresh_list()

    def on_enter_path(self, event=None):
        p = self.path_var.get()
        if os.path.exists(p) and os.path.isdir(p):
            self.current_dir = p
            self.refresh_list()
        else: self.entry.configure(border_color=C['pink'])

    def create_folder(self):
        dialog = ctk.CTkInputDialog(text="New Folder Name:", title="Create Folder")
        name = dialog.get_input()
        if not name: return
        new_path = os.path.join(self.current_dir, name)
        try:
            os.makedirs(new_path)
            self.refresh_list()
        except Exception as e: print(e)

    def enter_folder(self, folder_name):
        new_path = os.path.join(self.current_dir, folder_name)
        if os.path.isdir(new_path):
            try:
                os.listdir(new_path)
                self.current_dir = new_path
                self.path_var.set(self.current_dir)
                self.refresh_list()
            except: pass

    def select_current(self):
        self.result = self.current_dir
        self.destroy()

    def refresh_list(self):
        for w in self.scroll.winfo_children(): w.destroy()
        self.entry.configure(border_color=C['dim'])
        try:
            items = os.scandir(self.current_dir)
            dirs = [i.name for i in sorted(items, key=lambda i: i.name) if i.is_dir()]
            if not dirs:
                lbl = ctk.CTkLabel(self.scroll, text="(Empty or No Subfolders)", text_color=C['dim'])
                lbl.pack(pady=20)
                self.bind_scroll(lbl, self.scroll)
                return
            for d in dirs:
                btn = ctk.CTkButton(self.scroll, text=f"📁 {d}", anchor="w", fg_color="transparent", text_color=C['text'], hover_color=C['dim'], height=28, command=lambda f=d: self.enter_folder(f))
                btn.pack(fill="x", padx=2, pady=1)
                self.bind_scroll(btn, self.scroll)
        except Exception as e:
            err = ctk.CTkLabel(self.scroll, text=f"Access Denied: {e}", text_color=C['pink'])
            err.pack(pady=20)
            self.bind_scroll(err, self.scroll)


class UltimateApp(ctk.CTk):
    def __init__(self):
        self.load_config()
        self.twitch = TwitchManager(self.folder_mappings.get('twitch_id', ''), self.folder_mappings.get('twitch_secret', ''))
        self.ra = RAManager(self.folder_mappings.get('ra_user', ''), self.folder_mappings.get('ra_key', ''))
        self.apply_saved_theme()
        super().__init__()
        
        # App Info
        self.app_version = "1.4.0"
        self.github_url = "https://github.com/crabbiemike/MyriFetch"
        
        self.title(f"MYRIFETCH v{self.app_version} // ROM MANAGER")
        self.geometry("1100x850")
        self.configure(bg_color=C['bg'])
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.current_path = ""
        self.file_cache = []
        self.filtered_cache = []
        self.download_list = []
        self.pending_stage_queue = [] # Master staging queue
        self.is_downloading = False
        self.cancel_download = False
        self.is_paused = False
        self.console_icons = {}
        self.current_page = 0
        self.items_per_page = 100
        self.home_widgets = []
        self.browser_widgets = []
        self.queue_widgets = []
        self.settings_widgets = []
        self.library_widgets = []
        
        self.tooltip_window = None
        self.tooltip_job = None
        self.game_metadata_cache = {}
        
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.setup_sidebar()
        self.setup_main()
        threading.Thread(target=self.icon_manager, daemon=True).start()
        self.show_home()
        self.status_txt.configure(text=f"v{self.app_version}")
        self.net_log("System Initialized")
        try: self.refresh_dir("") 
        except: pass

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f: self.folder_mappings = json.load(f)
            except: self.folder_mappings = {}
        else: self.folder_mappings = {}

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f: json.dump(self.folder_mappings, f)
        except: pass

    def apply_saved_theme(self):
        saved_theme = self.folder_mappings.get('app_theme', 'Cyber Dark')
        if saved_theme in THEMES: C.update(THEMES[saved_theme])

    def change_theme(self, new_theme):
        self.folder_mappings['app_theme'] = new_theme
        self.save_config()
        popup = CustomPopup(self, "Theme Changed", "The theme has been updated.\n\nA restart is required to apply the changes fully.\nWould you like to restart now?", ['Restart Now', 'Later'])
        if popup.result == 'Restart Now': self.restart_app()

    def restart_app(self):
        self.destroy()
        try:
            if getattr(sys, 'frozen', False): os.execl(sys.executable, sys.executable, *sys.argv[1:])
            else: os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e: print(f"Restart failed: {e}")

    def change_default_region(self, new_region):
        self.folder_mappings['default_region'] = new_region
        self.save_config()
        self.region_var.set(new_region)
        self.filter_list()

    def net_log(self, msg):
        self.after(0, lambda: self.net_status.configure(text=f"Net: {msg}"))

    def icon_manager(self):
        if not os.path.exists(ICON_DIR):
            try: shutil.rmtree(ICON_DIR)
            except: pass
            time.sleep(0.5)
            os.makedirs(ICON_DIR, exist_ok=True)
        self.net_log("Connecting to LaunchBox DB...")
        lb_urls = {}
        try:
            icon_headers = HEADERS.copy()
            icon_headers['Referer'] = 'https://gamesdb.launchbox-app.com/'
            r = requests.get('https://gamesdb.launchbox-app.com/platforms/index', headers=icon_headers, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                cards = soup.find_all('div', class_='white-card')
                for card in cards:
                    title_tag = card.find('a', class_='list-item-title')
                    if title_tag:
                        lb_name = title_tag.text.strip()
                        img_tag = card.find('img')
                        if img_tag and 'src' in img_tag.attrs:
                            img_url = img_tag['src']
                            for my_name, target_lb_name in LB_NAMES.items():
                                if lb_name.lower() == target_lb_name.lower(): lb_urls[my_name] = img_url
            for name in CONSOLES.keys():
                safe_name = "".join(x for x in name if x.isalnum()) + ".png"
                local_path = os.path.join(ICON_DIR, safe_name)
                if not os.path.exists(local_path) or os.path.getsize(local_path) > 500: pass
                if name in lb_urls:
                    self.net_log(f"Downloading: {name}")
                    try:
                        r = requests.get(lb_urls[name], headers=HEADERS, stream=True, timeout=10)
                        if r.status_code == 200:
                            with open(local_path, 'wb') as f:
                                for chunk in r.iter_content(1024): f.write(chunk)
                    except: pass
                if os.path.exists(local_path) and os.path.getsize(local_path) > 500:
                    try:
                        pil_img = Image.open(local_path)
                        self.console_icons[name] = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(100,100))
                    except: pass
            self.net_log("Icons Loaded")
            self.after(0, self.render_home_grid)
            self.after(3000, lambda: self.net_log("Idle"))
        except Exception as e: print(f"LaunchBox Scrape Error: {e}")

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color='#101014')
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_rowconfigure(8, weight=1)
        ctk.CTkLabel(self.sidebar, text="👾 MYRIFETCH", font=('Arial', 22, 'bold'), text_color='white').grid(row=0, column=0, padx=20, pady=30)
        
        self.btn_home = self.nav_btn("Home", 1, self.show_home)
        self.btn_library = self.nav_btn("Library", 2, self.show_library)
        self.btn_browser = self.nav_btn("Browser", 3, lambda: self.show_browser())
        self.btn_bios = self.nav_btn("BIOS Files", 4, self.show_bios)
        self.btn_queue = self.nav_btn("Downloads", 5, self.show_queue)
        self.btn_ra = self.nav_btn("Achievements", 6, self.show_achievements)
        self.btn_settings = self.nav_btn("Settings", 7, self.show_settings)
        
        self.btn_update = ctk.CTkButton(self.sidebar, text="Check for Updates ↗", height=32, 
                                        fg_color=C['card'], hover_color=C['pink'], 
                                        font=('Arial', 11, 'bold'),
                                        command=lambda: webbrowser.open(self.github_url))
        self.btn_update.grid(row=8, column=0, padx=20, pady=(10, 0), sticky='s')

        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color=C['card'])
        self.status_frame.grid(row=9, column=0, padx=20, pady=10, sticky='ew')
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color=C['success'], font=('Arial', 16))
        self.status_dot.pack(side='left', padx=(10, 5))
        self.status_txt = ctk.CTkLabel(self.status_frame, text=f"v{self.app_version}", text_color=C['dim'])
        self.status_txt.pack(side='left')
        
        self.net_status = ctk.CTkLabel(self.sidebar, text="Net: Idle", text_color=C['dim'], font=('Consolas', 10), anchor='w')
        self.net_status.grid(row=10, column=0, padx=15, pady=(0, 10), sticky='ew')

    def nav_btn(self, text, row, cmd):
        btn = ctk.CTkButton(self.sidebar, text=text, height=40, fg_color='transparent', anchor='w', font=('Arial', 13, 'bold'), hover_color='#27272a', command=cmd)
        btn.grid(row=row, column=0, padx=5, pady=5, sticky='ew')
        return btn

    def setup_main(self):
        self.main_area = ctk.CTkFrame(self, fg_color='transparent')
        self.main_area.grid(row=0, column=1, sticky='nsew', padx=20, pady=20)
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.search_container = ctk.CTkFrame(self.main_area, fg_color='transparent', height=40)
        self.search_container.grid_columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        self.entry_search = ctk.CTkEntry(self.search_container, placeholder_text="Search (Press Enter)...", height=40, fg_color=C['card'], border_width=2, border_color=C['cyan'], corner_radius=20, text_color='white', textvariable=self.search_var)
        self.entry_search.grid(row=0, column=0, sticky='ew', padx=(0, 10))
        self.entry_search.bind('<Return>', self.filter_list)
        default_region = self.folder_mappings.get('default_region', 'All Regions')
        self.region_var = ctk.StringVar(value=default_region)
        self.region_filter = ctk.CTkOptionMenu(self.search_container, variable=self.region_var, values=['All Regions', 'USA', 'Europe', 'Japan', 'World'], command=self.filter_list, fg_color=C['card'], button_color=C['cyan'], button_hover_color=C['pink'], text_color='white', width=140, height=40, corner_radius=20)
        self.region_filter.grid(row=0, column=2, sticky='e')
        self.status_var = ctk.StringVar(value="All Status")
        self.status_filter = ctk.CTkOptionMenu(self.search_container, variable=self.status_var, values=['All Status', 'Missing Only', 'Owned Only'], command=self.filter_list, fg_color=C['card'], button_color=C['cyan'], button_hover_color=C['pink'], text_color='white', width=140, height=40, corner_radius=20)
        self.status_filter.grid(row=0, column=2, sticky='e')
        self.frame_home = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_library = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_details = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_browser = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_queue = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_settings = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_bios = ctk.CTkFrame(self.main_area, fg_color='transparent')
        self.frame_achievements = ctk.CTkFrame(self.main_area, fg_color='transparent')
        
        ctk.CTkLabel(self.frame_home, text="QUICK JUMP", font=('Arial', 16, 'bold'), text_color=C['dim']).pack(anchor='w', pady=10)
        self.grid_consoles = ctk.CTkScrollableFrame(self.frame_home, fg_color='transparent')
        self.grid_consoles.pack(fill='both', expand=True)
        self.bind_scroll(self.grid_consoles, self.grid_consoles)
        self.render_home_grid()
        self.lib_header = ctk.CTkFrame(self.frame_library, fg_color='transparent')
        self.lib_header.pack(fill='x', pady=10)
        ctk.CTkLabel(self.lib_header, text="GAME LIBRARY", font=('Arial', 20, 'bold'), text_color=C['cyan']).pack(side='left')
        self.lib_sort_var = ctk.StringVar(value="All Consoles")
        self.lib_sort_menu = ctk.CTkOptionMenu(self.lib_header, variable=self.lib_sort_var, values=['All Consoles'], command=self.render_library_grid, fg_color=C['card'], button_color=C['cyan'], button_hover_color=C['pink'], text_color='white', width=160)
        self.lib_sort_menu.pack(side='right')
        self.lib_scroll = ctk.CTkScrollableFrame(self.frame_library, fg_color=C['card'])
        self.lib_scroll.pack(fill='both', expand=True)
        self.bind_scroll(self.lib_scroll, self.lib_scroll)
        self.frame_browser.grid_rowconfigure(1, weight=1)
        self.frame_browser.grid_columnconfigure(0, weight=1)
        nav = ctk.CTkFrame(self.frame_browser, fg_color='transparent')
        nav.pack(fill='x', pady=5)
        ctk.CTkButton(nav, text="⬅ Back", width=60, fg_color=C['card'], command=self.go_up).pack(side='left')
        self.lbl_path = ctk.CTkLabel(nav, text="/", text_color=C['dim'], padx=10)
        self.lbl_path.pack(side='left')
        self.btn_open = ctk.CTkButton(nav, text="↗ Open", width=60, fg_color=C['card'], hover_color=C['dim'], command=self.open_current_folder)
        self.btn_open.pack(side='right', padx=(5,0))
        self.btn_map = ctk.CTkButton(nav, text="📂 Set Folder", fg_color='transparent', border_width=1, border_color=C['cyan'], text_color=C['cyan'], command=self.set_mapping)
        self.btn_map.pack(side='right')
        self.storage_frame = ctk.CTkFrame(self.frame_browser, fg_color='transparent', height=20)
        self.storage_frame.pack(fill='x', padx=10)
        self.storage_label = ctk.CTkLabel(self.storage_frame, text="Storage: Checking...", font=('Arial', 10), text_color=C['dim'])
        self.storage_label.pack(side='left')
        self.storage_bar = ctk.CTkProgressBar(self.storage_frame, height=8, progress_color=C['dim'])
        self.storage_bar.set(0)
        self.storage_bar.pack(side='left', fill='x', expand=True, padx=10)
        self.list_frame = ctk.CTkScrollableFrame(self.frame_browser, fg_color=C['card'])
        self.list_frame.pack(fill='both', expand=True, pady=10)
        self.bind_scroll(self.list_frame, self.list_frame)
        self.loading_frame = ctk.CTkFrame(self.frame_browser, fg_color='transparent')
        self.loading_label = ctk.CTkLabel(self.loading_frame, text="ACCESSING DATABANK...", font=('Arial', 18, 'bold'), text_color=C['cyan'])
        self.loading_label.place(relx=0.5, rely=0.4, anchor='center')
        self.loading_bar = ctk.CTkProgressBar(self.loading_frame, width=300, height=20, progress_color=C['pink'], mode='indeterminate')
        self.loading_bar.place(relx=0.5, rely=0.5, anchor='center')
        self.page_controls = ctk.CTkFrame(self.frame_browser, fg_color='transparent', height=40)
        self.page_controls.pack(fill='x', pady=5)
        self.btn_prev = ctk.CTkButton(self.page_controls, text="< Previous", width=100, fg_color=C['card'], command=self.prev_page)
        self.btn_prev.pack(side='left')
        self.lbl_page = ctk.CTkLabel(self.page_controls, text="Page 1", text_color=C['dim'])
        self.lbl_page.pack(side='left', expand=True)
        self.btn_next = ctk.CTkButton(self.page_controls, text="Next >", width=100, fg_color=C['card'], command=self.next_page)
        self.btn_next.pack(side='right')
        dl_frame = ctk.CTkFrame(self.frame_browser, fg_color='transparent')
        dl_frame.pack(fill='x')
        self.btn_dl = ctk.CTkButton(dl_frame, text="DOWNLOAD SELECTED [0]", height=50, fg_color=C['cyan'], text_color='black', font=('Arial', 14, 'bold'), command=self.add_to_queue)
        self.btn_dl.pack(side='left', fill='x', expand=True, padx=(0,5))
        self.btn_dl_all = ctk.CTkButton(dl_frame, text="⬇ Download All Listed", height=50, fg_color=C['card'], text_color='white', font=('Arial', 14, 'bold'), hover_color=C['pink'], command=self.add_all_to_queue)
        self.btn_dl_all.pack(side='right', fill='x', expand=True, padx=(5,0))
        ctk.CTkLabel(self.frame_queue, text="ACTIVE DOWNLOAD", font=('Arial', 20, 'bold')).pack(anchor='w', pady=10)
        self.queue_controls = ctk.CTkFrame(self.frame_queue, fg_color='transparent')
        self.queue_controls.pack(fill='x', pady=5)
        self.lbl_speed = ctk.CTkLabel(self.queue_controls, text="IDLE", font=('Consolas', 14), text_color=C['cyan'])
        self.lbl_speed.pack(side='left')
        
        # UI Elements for Batches and Stop
        self.btn_pause = ctk.CTkButton(self.queue_controls, text="Pause Download", fg_color=C['card'], width=120, height=30, command=self.toggle_pause, state='disabled')
        self.btn_pause.pack(side='right', padx=(5, 0))
        self.btn_stop = ctk.CTkButton(self.queue_controls, text="Stop Download", fg_color=C['pink'], width=120, height=30, command=self.cancel_current, state='disabled')
        self.btn_stop.pack(side='right')

        # Batch Status Labels
        self.lbl_batches_left = ctk.CTkLabel(self.queue_controls, text="Batches Left: 0", font=('Arial', 12, 'bold'), text_color=C['pink'])
        self.lbl_batches_left.pack(side='right', padx=10)
        self.lbl_total_left = ctk.CTkLabel(self.queue_controls, text="Total Left: 0", font=('Arial', 12, 'bold'), text_color=C['cyan'])
        self.lbl_total_left.pack(side='right', padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.frame_queue, height=15, progress_color=C['cyan'])
        self.progress_bar.set(0)
        self.progress_bar.pack(fill='x', pady=10)
        self.log_box = ctk.CTkTextbox(self.frame_queue, fg_color=C['card'], font=('Consolas', 12), height=100)
        self.log_box.pack(fill='x', pady=(0, 10))
        ctk.CTkLabel(self.frame_queue, text="PENDING QUEUE", font=('Arial', 20, 'bold'), text_color=C['dim']).pack(anchor='w', pady=10)
        self.queue_list_frame = ctk.CTkScrollableFrame(self.frame_queue, fg_color=C['card'])
        self.queue_list_frame.pack(fill='both', expand=True)
        self.bind_scroll(self.queue_list_frame, self.queue_list_frame)
        ctk.CTkLabel(self.frame_settings, text="SETTINGS & PATHS", font=('Arial', 20, 'bold')).pack(anchor='w', pady=10)
        self.settings_scroll = ctk.CTkScrollableFrame(self.frame_settings, fg_color='transparent')
        self.settings_scroll.pack(fill='both', expand=True, pady=10)
        self.bind_scroll(self.settings_scroll, self.settings_scroll)
        self.setup_bios_ui()

    def setup_bios_ui(self):
        url = 'https://archive.org/download/retroarch_bios/system.7z'
        ctk.CTkLabel(self.frame_bios, text="RETROARCH BIOS PACKS", font=('Arial', 20, 'bold'), text_color=C['cyan']).pack(anchor='w', pady=20, padx=20)
        info = ctk.CTkLabel(self.frame_bios, text="Download complete BIOS packs for RetroArch and other emulators.\nThese files are required for many systems (PS1, PS2, Sega CD, etc) to run.", font=('Arial', 14), text_color=C['dim'], justify='left')
        info.pack(anchor='w', padx=20, pady=(0, 30))
        dl_frame = ctk.CTkFrame(self.frame_bios, fg_color=C['card'])
        dl_frame.pack(fill='x', padx=20, pady=10)
        ctk.CTkLabel(dl_frame, text="RetroArch System BIOS Pack (Complete)", font=('Arial', 16, 'bold'), text_color='white').pack(side='left', padx=20, pady=20)
        ctk.CTkButton(dl_frame, text="Download", fg_color=C['cyan'], text_color='black', font=('Arial', 14, 'bold'), command=lambda: self.queue_direct_item("RetroArch_BIOS_Pack", url, "system.7z")).pack(side='right', padx=20)
        instr_container = ctk.CTkFrame(self.frame_bios, fg_color='transparent')
        instr_container.pack(fill='both', expand=True, padx=20, pady=10)
        ctk.CTkLabel(instr_container, text="SETUP INSTRUCTIONS", font=('Arial', 14, 'bold'), text_color=C['cyan']).pack(anchor='w', pady=(10, 5))
        instr_scroll = ctk.CTkScrollableFrame(instr_container, fg_color=C['card'])
        instr_scroll.pack(fill='both', expand=True)
        instructions = [('PlayStation 1 (DuckStation/SwanStation)', "Copy 'scph5501.bin' (USA), 'scph5502.bin' (EUR), 'scph5500.bin' (JPN) to your emulator's 'bios' folder."), ('PlayStation 2 (PCSX2)', "Copy 'scph39001.bin' (or similar) to the 'bios' folder. Select it in PCSX2 settings."), ('Sega Dreamcast (Flycast/Redream)', "Copy 'dc_boot.bin' and 'dc_flash.bin' to the 'system/dc' folder."), ('Sega Saturn (Beetle Saturn)', "Copy 'sega_101.bin' (JPN), 'mpr-17933.bin' (USA) to the 'system' folder."), ('Nintendo DS (MelonDS)', "Copy 'bios7.bin', 'bios9.bin', and 'firmware.bin' to the 'system' folder."), ('General RetroArch', "Extract the contents of 'system.7z' directly into your RetroArch 'system' directory.")]
        for title, text in instructions:
            row = ctk.CTkFrame(instr_scroll, fg_color='transparent')
            row.pack(fill='x', pady=5)
            ctk.CTkLabel(row, text=title, font=('Arial', 13, 'bold'), text_color='white').pack(anchor='w')
            ctk.CTkLabel(row, text=text, font=('Arial', 12), text_color=C['dim'], wraplength=600, justify='left').pack(anchor='w', padx=10)

    def queue_direct_item(self, name, url, filename=None):
        browser = ThemedDirBrowser(self, title=f"Select Save Location for {name}")
        local_dir = browser.result
        if not local_dir: return
        if not os.access(local_dir, os.W_OK):
             CustomPopup(self, "Permission Error", f"Cannot write to:\n{local_dir}", ["OK"])
             return
        if filename: dest = os.path.join(local_dir, filename)
        else: dest = os.path.join(local_dir, f"{name}.zip")
        self.download_list.append({'url': url, 'path': dest, 'name': name, 'size_mb': 0})
        self.log(f"QUEUED: {name}")
        self.show_queue()
        self.render_queue_list()
        if not self.is_downloading: threading.Thread(target=self.process_queue, daemon=True).start()

    def render_home_grid(self):
        for widget in self.home_widgets:
            widget.grid_forget()
            widget.destroy()
        self.home_widgets = []
        self.update_idletasks()
        MAX_COLS = 3
        self.grid_consoles.grid_columnconfigure((0, 1, 2), weight=1)
        GROUPS = [('SONY', ['PlayStation 1', 'PlayStation 2', 'PSP', 'PlayStation 3']), ('NINTENDO', ['SNES', 'GBA', 'GameCube', 'Nintendo DS', 'Wii', 'Nintendo 3DS']), ('SEGA', ['Dreamcast']), ('MICROSOFT', ['Xbox'])]
        current_row = 0
        for group_name, console_list in GROUPS:
            header = ctk.CTkLabel(self.grid_consoles, text=group_name, font=('Arial', 14, 'bold'), text_color=C['cyan'], anchor='w')
            header.grid(row=current_row, column=0, columnspan=MAX_COLS, sticky='w', padx=20, pady=5)
            self.bind_scroll(header, self.grid_consoles)
            self.home_widgets.append(header)
            current_row += 1
            col = 0
            for name in console_list:
                if name not in CONSOLES: continue
                path = CONSOLES[name]
                btn = ctk.CTkButton(self.grid_consoles, text=f"\n{name}", image=self.console_icons.get(name), compound='top', width=150, height=150, fg_color=C['card'], font=('Arial', 14, 'bold'), hover_color=C['pink'], command=lambda p=path: self.jump_to(p))
                btn.grid(row=current_row, column=col, padx=10, pady=10, sticky='nsew')
                self.bind_scroll(btn, self.grid_consoles)
                self.home_widgets.append(btn)
                col += 1
                if col >= MAX_COLS:
                    col = 0
                    current_row += 1
            if col > 0: current_row += 1

    def jump_to(self, p):
        self.refresh_dir(p)
        self.show_browser()

    def show_loader(self):
        self.list_frame.pack_forget()
        self.page_controls.pack_forget()
        self.btn_dl.pack_forget()
        self.btn_dl_all.pack_forget()
        self.loading_frame.pack(fill='both', expand=True, pady=10)
        self.loading_bar.start()

    def hide_loader(self):
        self.loading_bar.stop()
        self.loading_frame.pack_forget()
        self.list_frame.pack(fill='both', expand=True, pady=10)
        self.page_controls.pack(fill='x', pady=5)
        self.btn_dl.pack(side='left', fill='x', expand=True, padx=(0,5))
        self.btn_dl_all.pack(side='right', fill='x', expand=True, padx=(5,0))

    def hide_all(self):
        self.frame_home.grid_forget()
        self.frame_browser.grid_forget()
        self.frame_queue.grid_forget()
        self.frame_settings.grid_forget()
        self.frame_bios.grid_forget()
        self.frame_library.grid_forget()
        self.frame_details.grid_forget()
        self.frame_achievements.grid_forget()
        self.search_container.grid_forget()
        self.btn_home.configure(fg_color='transparent', text_color='white')
        self.btn_library.configure(fg_color='transparent', text_color='white')
        self.btn_browser.configure(fg_color='transparent', text_color='white')
        self.btn_queue.configure(fg_color='transparent', text_color='white')
        self.btn_settings.configure(fg_color='transparent', text_color='white')
        self.btn_bios.configure(fg_color='transparent', text_color='white')
        self.btn_ra.configure(fg_color='transparent', text_color='white')

    def show_home(self):
        self.hide_all()
        self.frame_home.grid(row=1, column=0, sticky='nsew')
        self.btn_home.configure(fg_color=C['cyan'], text_color='black')

    def show_browser(self):
        self.hide_all()
        self.search_container.grid(row=0, column=0, sticky='ew', pady=(0, 20))
        self.frame_browser.grid(row=1, column=0, sticky='nsew')
        self.btn_browser.configure(fg_color=C['cyan'], text_color='black')
        self.update_storage_stats()

    def show_queue(self):
        self.hide_all()
        self.frame_queue.grid(row=1, column=0, sticky='nsew')
        self.btn_queue.configure(fg_color=C['cyan'], text_color='black')
        self.render_queue_list()

    def show_settings(self):
        self.hide_all()
        self.frame_settings.grid(row=1, column=0, sticky='nsew')
        self.btn_settings.configure(fg_color=C['cyan'], text_color='black')
        self.render_settings()

    def show_bios(self):
        self.hide_all()
        self.frame_bios.grid(row=1, column=0, sticky='nsew')
        self.btn_bios.configure(fg_color=C['cyan'], text_color='black')
    
    def show_library(self):
        self.hide_all()
        self.frame_library.grid(row=1, column=0, sticky='nsew')
        self.btn_library.configure(fg_color=C['cyan'], text_color='black')
        self.render_library_grid()

    def show_achievements(self):
        self.hide_all()
        self.frame_achievements.grid(row=1, column=0, sticky='nsew')
        self.btn_ra.configure(fg_color=C['cyan'], text_color='black')
        self.render_achievements()

    def render_achievements(self):
        for w in self.frame_achievements.winfo_children(): w.destroy()
        
        # Header row with Title and Browse Button
        header_row = ctk.CTkFrame(self.frame_achievements, fg_color='transparent')
        header_row.pack(fill='x', pady=(10, 20))
        
        ctk.CTkLabel(header_row, text="RETROACHIEVEMENTS", 
                     font=('Arial', 20, 'bold'), text_color=C['cyan']).pack(side='left', padx=5)
        
        # Browse Button to Myrient's RetroAchievements folder
        ctk.CTkButton(header_row, text="Browse RA-Supported ROMs ↗", 
                      fg_color=C['card'], hover_color=C['pink'],
                      command=lambda: self.jump_to("RetroAchievements/")).pack(side='right', padx=5)
        
        if not self.ra.api_key:
            ctk.CTkLabel(self.frame_achievements, text="Please configure your RA API Key in Settings.", 
                         text_color=C['dim']).pack(pady=20)
            return

        loading = ctk.CTkLabel(self.frame_achievements, text="FETCHING PROFILE DATA...", font=('Arial', 14))
        loading.pack(pady=20)

        def _load():
            error_msg, data = self.ra.get_user_summary()
            self.after(0, lambda: loading.destroy())
            if data:
                self.after(0, lambda: self.draw_ra_profile(data))
            else:
                self.after(0, lambda e=error_msg: ctk.CTkLabel(self.frame_achievements, 
                           text=f"Error: {e}", text_color=C['pink']).pack())
        
        threading.Thread(target=_load, daemon=True).start()

    def draw_ra_profile(self, data):
        profile_card = ctk.CTkFrame(self.frame_achievements, fg_color=C['card'])
        profile_card.pack(fill='x', padx=10, pady=10)
        
        user_info = ctk.CTkFrame(profile_card, fg_color='transparent')
        user_info.pack(fill='x', padx=20, pady=20)
        
        ctk.CTkLabel(user_info, text=data.get('User', 'Unknown'), font=('Arial', 24, 'bold'), text_color=C['cyan']).pack(side='left')
        
        stats_frame = ctk.CTkFrame(profile_card, fg_color='transparent')
        stats_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        stats = [
            ("Points", data.get('TotalPoints', '0')),
            ("Ratio", data.get('RetroRatio', '0')),
            ("Rank", data.get('Rank', 'N/A')),
            ("Completed", data.get('TotalGamesCompleted', '0'))
        ]
        
        for label, val in stats:
            s_box = ctk.CTkFrame(stats_frame, fg_color=C['bg'], corner_radius=10)
            s_box.pack(side='left', padx=5, fill='x', expand=True)
            ctk.CTkLabel(s_box, text=label, font=('Arial', 10), text_color=C['dim']).pack(pady=(5, 0))
            ctk.CTkLabel(s_box, text=val, font=('Arial', 14, 'bold'), text_color='white').pack(pady=(0, 5))

    def show_game_details(self, game):
        self.hide_all()
        self.frame_details.grid(row=1, column=0, sticky='nsew')
        
        for w in self.frame_details.winfo_children(): w.destroy()
        
        header = ctk.CTkFrame(self.frame_details, fg_color='transparent')
        header.pack(fill='x', pady=10)
        ctk.CTkButton(header, text="⬅ Back to Library", width=120, command=self.show_library, fg_color=C['card']).pack(side='left')
        
        content = ctk.CTkFrame(self.frame_details, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=20)
        
        left_col = ctk.CTkFrame(content, fg_color='transparent')
        left_col.pack(side='left', fill='y', padx=(0, 20))
        
        if game['cover'] and os.path.exists(game['cover']):
            try:
                pil = Image.open(game['cover'])
                w, h = pil.size
                ratio = 350 / h
                new_w = int(w * ratio)
                img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(new_w, 350))
                lbl_img = ctk.CTkLabel(left_col, text="", image=img)
            except:
                lbl_img = ctk.CTkLabel(left_col, text="[No Image]", width=200, height=300, fg_color=C['card'])
        else:
             icon = self.console_icons.get(game['console'])
             lbl_img = ctk.CTkLabel(left_col, text="", image=icon) if icon else ctk.CTkLabel(left_col, text="No Art")
             
        lbl_img.pack(pady=10)
        
        btn_open = ctk.CTkButton(left_col, text="Open File Location", fg_color=C['cyan'], text_color='black', command=lambda: self.launch_game_folder(game['path']))
        btn_open.pack(fill='x', pady=5)
        
        btn_del = ctk.CTkButton(left_col, text="Delete Game", fg_color=C['pink'], hover_color='#990033', command=lambda: self.confirm_delete(game))
        btn_del.pack(fill='x', pady=5)
        
        right_col = ctk.CTkScrollableFrame(content, fg_color='transparent')
        right_col.pack(side='left', fill='both', expand=True)
        
        ctk.CTkLabel(right_col, text=game['name'], font=('Arial', 28, 'bold'), text_color='white', wraplength=600, justify='left').pack(anchor='w', pady=(10, 5))
        ctk.CTkLabel(right_col, text=f"Console: {game['console']}", font=('Arial', 14, 'bold'), text_color=C['cyan']).pack(anchor='w', pady=(0, 20))
        
        self.lbl_genre = ctk.CTkLabel(right_col, text="Genre: Loading...", font=('Arial', 14), text_color=C['dim'])
        self.lbl_genre.pack(anchor='w', pady=2)
        
        self.lbl_dev = ctk.CTkLabel(right_col, text="Developer: Loading...", font=('Arial', 14), text_color=C['dim'])
        self.lbl_dev.pack(anchor='w', pady=2)
        
        self.lbl_date = ctk.CTkLabel(right_col, text="Release Date: Loading...", font=('Arial', 14), text_color=C['dim'])
        self.lbl_date.pack(anchor='w', pady=2)
        
        ctk.CTkLabel(right_col, text="\nDescription:", font=('Arial', 16, 'bold'), text_color='white').pack(anchor='w', pady=(20, 5))
        self.lbl_desc = ctk.CTkLabel(right_col, text="Loading summary from IGDB...", font=('Arial', 14), text_color='white', wraplength=600, justify='left')
        self.lbl_desc.pack(anchor='w')
        
        threading.Thread(target=lambda: self.fetch_details_for_page(game['name']), daemon=True).start()

    def fetch_details_for_page(self, game_name):
        clean_name = game_name.split('(')[0].split('[')[0].strip()
        
        if clean_name in self.game_metadata_cache:
            data = self.game_metadata_cache[clean_name]
        else:
            data = self.twitch.search_game(clean_name)
            
        if data:
            genre = "Unknown"
            if 'genres' in data: genre = ", ".join([g['name'] for g in data['genres']])
            
            dev = "Unknown"
            if 'involved_companies' in data:
                 for c in data['involved_companies']:
                     if c.get('company'): 
                         dev = c['company']['name']
                         break
            
            date = "Unknown"
            if 'first_release_date' in data:
                date = datetime.fromtimestamp(data['first_release_date']).strftime('%Y-%m-%d')
                
            summary = data.get('summary', 'No description available.')
            self.after(0, lambda: self.update_details_ui(genre, dev, date, summary))
        else:
            self.after(0, lambda: self.update_details_ui("Unknown", "Unknown", "Unknown", "Could not find details on IGDB."))

    def update_details_ui(self, genre, dev, date, summary):
        try:
            self.lbl_genre.configure(text=f"Genre: {genre}")
            self.lbl_dev.configure(text=f"Developer: {dev}")
            self.lbl_date.configure(text=f"Release Date: {date}")
            self.lbl_desc.configure(text=summary)
        except: pass

    def confirm_delete(self, game):
        ask = CustomPopup(self, "Delete Game", f"Are you sure you want to delete:\n{game['name']}?\n\nThis cannot be undone.", ["Delete", "Cancel"])
        if ask.result == "Delete":
            try:
                folder_path = os.path.dirname(os.path.abspath(game['path']))
                
                # Delete main game file
                if os.path.exists(game['path']): 
                    os.remove(game['path'])
                
                # Delete cover art if it exists
                if game['cover'] and os.path.exists(game['cover']): 
                    os.remove(game['cover'])
                
                # Logic to delete folder if empty
                try:
                    if os.path.exists(folder_path):
                        # Check if directory is now empty
                        if not os.listdir(folder_path):
                            os.rmdir(folder_path)
                            self.log(f"Removed empty folder: {os.path.basename(folder_path)}")
                except Exception as fe:
                    self.log(f"Note: Could not remove folder: {fe}")

                self.show_library()
                CustomPopup(self, "Deleted", "Game files deleted successfully.", ["OK"])
            except Exception as e:
                CustomPopup(self, "Error", f"Could not delete: {e}", ["OK"])

    def scan_library(self):
        games = []
        valid_exts = ('.iso', '.cso', '.rvz', '.zip', '.7z', '.chd', '.wbfs', '.bin', '.nds', '.cia')
        found_consoles = set(['All Consoles'])
        for remote_path, local_path in self.folder_mappings.items():
            if not os.path.exists(local_path): continue
            console_name = "Unknown"
            for k, v in CONSOLES.items():
                if v == remote_path:
                    console_name = k
                    break
            if console_name != "Unknown": found_consoles.add(console_name)
            
            files_to_check = []
            try:
                with os.scandir(local_path) as it:
                    for entry in it:
                        if entry.is_file():
                            files_to_check.append((entry.name, entry.path))
                        elif entry.is_dir():
                            try:
                                for sub in os.scandir(entry.path):
                                    if sub.is_file():
                                        files_to_check.append((sub.name, sub.path))
                            except: pass
            except: pass

            for fname, fpath in files_to_check:
                if fname.lower().endswith(valid_exts):
                    base_name = os.path.splitext(fname)[0]
                    img_path = None
                    folder = os.path.dirname(fpath)
                    possible_cover = os.path.join(folder, base_name + ".jpg")
                    if os.path.exists(possible_cover): img_path = possible_cover
                    games.append({'name': base_name, 'path': fpath, 'console': console_name, 'cover': img_path})

        current_sort = self.lib_sort_var.get()
        sorted_consoles = sorted(list(found_consoles))
        self.lib_sort_menu.configure(values=sorted_consoles)
        if current_sort not in sorted_consoles: self.lib_sort_var.set("All Consoles")
        return games

    def render_library_grid(self, _=None):
        for w in self.library_widgets: w.destroy()
        self.library_widgets = []
        games = self.scan_library()
        filter_console = self.lib_sort_var.get()
        filtered = [g for g in games if filter_console == "All Consoles" or g['console'] == filter_console]
        if not filtered:
            lbl = ctk.CTkLabel(self.lib_scroll, text="No games found in your mapped folders.", font=('Arial', 14), text_color=C['dim'])
            lbl.pack(pady=40)
            self.library_widgets.append(lbl)
            return
        COLUMNS = 4
        self.lib_scroll.grid_columnconfigure(tuple(range(COLUMNS)), weight=1)
        for i, game in enumerate(filtered):
            row = i // COLUMNS
            col = i % COLUMNS
            card = ctk.CTkFrame(self.lib_scroll, fg_color=C['bg'])
            card.grid(row=row, column=col, padx=10, pady=10, sticky='nsew')
            self.library_widgets.append(card)
            if game['cover']:
                try:
                    pil = Image.open(game['cover'])
                    w, h = pil.size
                    ratio = 150 / h
                    new_w = int(w * ratio)
                    ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(new_w, 150))
                except: ctk_img = None
            else: ctk_img = self.console_icons.get(game['console'])
            btn = ctk.CTkButton(card, text=f"\n{game['name'][:20]}...", image=ctk_img, compound='top', fg_color='transparent', hover_color=C['card'], text_color='white', font=('Arial', 11), command=lambda g=game: self.show_game_details(g))
            btn.pack(fill='both', expand=True, padx=5, pady=5)
            clean_name = game['name'].split('(')[0].split('[')[0].strip()
            btn.bind("<Enter>", lambda e, n=clean_name: self.on_hover_enter(e, n))
            btn.bind("<Leave>", self.on_hover_leave)

    def on_hover_enter(self, event, game_name):
        if not self.twitch.client_id: return
        if self.tooltip_job: self.after_cancel(self.tooltip_job)
        self.tooltip_job = self.after(600, lambda: self.fetch_and_show_tooltip(game_name, event))

    def on_hover_leave(self, event):
        if self.tooltip_job: self.after_cancel(self.tooltip_job)
        self.tooltip_job = None
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

    def fetch_and_show_tooltip(self, game_name, event):
        if game_name in self.game_metadata_cache:
            self.show_tooltip_window(game_name, self.game_metadata_cache[game_name])
            return

        def _fetch():
            data = self.twitch.search_game(game_name)
            if not data:
                self.game_metadata_cache[game_name] = None
                return
            
            details = {}
            if 'first_release_date' in data:
                ts = data['first_release_date']
                details['Released'] = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
            
            if 'genres' in data:
                genres = [g['name'] for g in data['genres']]
                details['Genre'] = ", ".join(genres[:2])
            
            if 'involved_companies' in data:
                for comp in data['involved_companies']:
                    if comp.get('company'):
                        details['Developer'] = comp['company']['name']
                        break
            
            self.game_metadata_cache[game_name] = details
            self.after(0, lambda: self.show_tooltip_window(game_name, details))

        threading.Thread(target=_fetch, daemon=True).start()

    def show_tooltip_window(self, title, details):
        if not details: return
        x, y = self.winfo_pointerx(), self.winfo_pointery()
        if self.tooltip_window: self.tooltip_window.destroy()
        self.tooltip_window = GameTooltip(self, title, details, x, y)

    def toggle_pause(self):
        if self.is_downloading:
            if not self.is_paused:
                self.is_paused = True
                self.btn_pause.configure(text="Resume Download", fg_color=C['success'], text_color='black')
                self.log("⏸ DOWNLOAD PAUSED")
            else:
                self.is_paused = False
                self.btn_pause.configure(text="Pause Download", fg_color=C['card'], text_color='white')
                self.log("▶ RESUMING...")

    def cancel_current(self):
        if self.is_downloading:
            self.cancel_download = True
            self.pending_stage_queue = [] 
            self.download_list = []
            
            self.btn_stop.configure(state='disabled', text='Stopping...')
            self.log("🛑 STOPPING DOWNLOAD & WIPING ALL QUEUES...")
            self.update_batch_labels()
            self.after(0, self.render_queue_list)

    def open_twitch_site(self):
        webbrowser.open("https://dev.twitch.tv/console")

    def render_settings(self):
        for widget in self.settings_widgets: widget.destroy()
        self.settings_widgets = []
        
        theme_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        theme_row.pack(fill='x', pady=10)
        self.settings_widgets.append(theme_row)
        lbl = ctk.CTkLabel(theme_row, text="APP THEME", width=150, anchor='w', font=('Arial', 13, 'bold'), text_color=C['cyan'])
        lbl.pack(side='left', padx=10)
        current_theme_name = self.folder_mappings.get('app_theme', 'Cyber Dark')
        self.theme_var = ctk.StringVar(value=current_theme_name)
        theme_dropdown = ctk.CTkOptionMenu(theme_row, variable=self.theme_var, values=list(THEMES.keys()), command=self.change_theme, fg_color=C['bg'], button_color=C['cyan'], button_hover_color=C['pink'], text_color='white', corner_radius=20)
        theme_dropdown.pack(side='left', padx=10)
        hint = ctk.CTkLabel(theme_row, text="(Restart Required)", text_color=C['dim'], font=('Arial', 10))
        hint.pack(side='left', padx=5)

        region_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        region_row.pack(fill='x', pady=10)
        self.settings_widgets.append(region_row)
        lbl_reg = ctk.CTkLabel(region_row, text="DEFAULT REGION", width=150, anchor='w', font=('Arial', 13, 'bold'), text_color=C['cyan'])
        lbl_reg.pack(side='left', padx=10)
        current_region = self.folder_mappings.get('default_region', 'All Regions')
        self.default_region_var = ctk.StringVar(value=current_region)
        region_dropdown = ctk.CTkOptionMenu(region_row, variable=self.default_region_var, values=['All Regions', 'USA', 'Europe', 'Japan', 'World'], command=self.change_default_region, fg_color=C['bg'], button_color=C['cyan'], button_hover_color=C['pink'], text_color='white', corner_radius=20)
        region_dropdown.pack(side='left', padx=10)

        # New: Font Size row
        font_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        font_row.pack(fill='x', pady=10)
        self.settings_widgets.append(font_row)
        lbl_font = ctk.CTkLabel(font_row, text="BROWSER TEXT SIZE", width=150, anchor='w', font=('Arial', 13, 'bold'), text_color=C['cyan'])
        lbl_font.pack(side='left', padx=10)
        
        self.font_size_var = tk.IntVar(value=self.folder_mappings.get('font_size', 12))
        self.font_slider = ctk.CTkSlider(font_row, from_=10, to=24, number_of_steps=14, variable=self.font_size_var, command=self.update_font_size)
        self.font_slider.pack(side='left', padx=10, fill='x', expand=True)
        self.lbl_font_val = ctk.CTkLabel(font_row, text=str(self.font_size_var.get()), width=30)
        self.lbl_font_val.pack(side='left', padx=5)

        notif_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        notif_row.pack(fill='x', pady=10)
        self.settings_widgets.append(notif_row)
        lbl_notif = ctk.CTkLabel(notif_row, text="FINISH CHIME", width=150, anchor='w', font=('Arial', 13, 'bold'), text_color=C['cyan'])
        lbl_notif.pack(side='left', padx=10)
        notif_enabled = self.folder_mappings.get('notif_sound', True)
        self.notif_var = tk.BooleanVar(value=notif_enabled)
        notif_switch = ctk.CTkSwitch(notif_row, text="", variable=self.notif_var, command=self.toggle_notif_sound, progress_color=C['cyan'])
        notif_switch.pack(side='left', padx=10)

        demo_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        demo_row.pack(fill='x', pady=10)
        self.settings_widgets.append(demo_row)
        lbl_demo = ctk.CTkLabel(demo_row, text="FILTER DEMOS", width=150, anchor='w', font=('Arial', 13, 'bold'), text_color=C['cyan'])
        lbl_demo.pack(side='left', padx=10)
        demo_filtered = self.folder_mappings.get('filter_demos', False)
        self.demo_var = tk.BooleanVar(value=demo_filtered)
        demo_switch = ctk.CTkSwitch(demo_row, text="", variable=self.demo_var, command=self.toggle_demo_filter, progress_color=C['cyan'])
        demo_switch.pack(side='left', padx=10)

        rev_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        rev_row.pack(fill='x', pady=10)
        self.settings_widgets.append(rev_row)
        lbl_rev = ctk.CTkLabel(rev_row, text="FILTER REVISIONS", width=150, anchor='w', font=('Arial', 13, 'bold'), text_color=C['cyan'])
        lbl_rev.pack(side='left', padx=10)
        rev_filtered = self.folder_mappings.get('filter_revs', False)
        self.rev_var = tk.BooleanVar(value=rev_filtered)
        rev_switch = ctk.CTkSwitch(rev_row, text="", variable=self.rev_var, command=self.toggle_rev_filter, progress_color=C['cyan'])
        rev_switch.pack(side='left', padx=10)

        sep1 = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep1.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep1)

        for name, path in CONSOLES.items():
            row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
            row.pack(fill='x', pady=5)
            self.settings_widgets.append(row)
            l1 = ctk.CTkLabel(row, text=name, width=150, anchor='w', font=('Arial', 13, 'bold'))
            l1.pack(side='left', padx=10)
            current = self.folder_mappings.get(path)
            path_text = current if current else "Default (Ask)"
            path_color = 'white' if current else C['dim']
            l2 = ctk.CTkLabel(row, text=path_text, text_color=path_color, anchor='w')
            l2.pack(side='left', fill='x', expand=True)
            btn = ctk.CTkButton(row, text="Change", width=80, fg_color=C['bg'], border_width=1, border_color=C['cyan'], text_color=C['cyan'], command=lambda p=path: self.change_console_path(p))
            btn.pack(side='right', padx=10)

        clear_row = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        clear_row.pack(fill='x', pady=20)
        self.settings_widgets.append(clear_row)
        btn_clear = ctk.CTkButton(clear_row, text="Clear All Saved Directories", fg_color=C['pink'], hover_color='#990033', command=self.clear_saved_folders)
        btn_clear.pack()

        sep2 = ctk.CTkFrame(self.settings_scroll, fg_color=C['dim'], height=1)
        sep2.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(sep2)

        # TWITCH SECTION
        twitch_header = ctk.CTkLabel(self.settings_scroll, text="TWITCH / IGDB API (BOX ART & INFO)", font=('Arial', 14, 'bold'), text_color=C['cyan'])
        twitch_header.pack(fill='x', pady=(10, 5))
        self.settings_widgets.append(twitch_header)

        expl = ctk.CTkLabel(self.settings_scroll, text="Integrate with IGDB to automatically download box art and show game details.", text_color=C['dim'], font=('Arial', 12))
        expl.pack(pady=(0, 10))
        self.settings_widgets.append(expl)
        
        row_id = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        row_id.pack(fill='x', pady=2)
        self.settings_widgets.append(row_id)
        ctk.CTkLabel(row_id, text="Client ID:", width=100, anchor='w').pack(side='left', padx=10)
        self.entry_twitch_id = ctk.CTkEntry(row_id, fg_color=C['bg'], border_color=C['dim'])
        self.entry_twitch_id.insert(0, self.folder_mappings.get('twitch_id', ''))
        self.entry_twitch_id.pack(side='left', fill='x', expand=True, padx=10)
        
        row_secret = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        row_secret.pack(fill='x', pady=2)
        self.settings_widgets.append(row_secret)
        ctk.CTkLabel(row_secret, text="Client Secret:", width=100, anchor='w').pack(side='left', padx=10)
        self.entry_twitch_secret = ctk.CTkEntry(row_secret, fg_color=C['bg'], border_color=C['dim'], show="*")
        self.entry_twitch_secret.insert(0, self.folder_mappings.get('twitch_secret', ''))
        self.entry_twitch_secret.pack(side='left', fill='x', expand=True, padx=10)
        
        btn_save_twitch = ctk.CTkButton(self.settings_scroll, text="Save Keys & Test Connection", fg_color=C['cyan'], text_color='black', command=self.save_twitch_creds)
        btn_save_twitch.pack(pady=10)
        self.settings_widgets.append(btn_save_twitch)

        help_frame = ctk.CTkFrame(self.settings_scroll, fg_color=C['card'])
        help_frame.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(help_frame)
        ctk.CTkLabel(help_frame, text="How to get Twitch keys:", font=('Arial', 12, 'bold'), text_color=C['cyan']).pack(anchor='w', padx=10, pady=(10,5))
        t_steps = ["1. Visit dev.twitch.tv/console", "2. Register your application (OAuth: http://localhost)", "3. Category: Game Integration", "4. Copy Client ID and generate a Client Secret."]
        for s in t_steps: ctk.CTkLabel(help_frame, text=s, font=('Arial', 11), anchor='w').pack(anchor='w', padx=15)

        # RETROACHIEVEMENTS SECTION
        ra_header = ctk.CTkLabel(self.settings_scroll, text="RETROACHIEVEMENTS API", font=('Arial', 14, 'bold'), text_color=C['cyan'])
        ra_header.pack(fill='x', pady=(20, 5))
        self.settings_widgets.append(ra_header)

        row_ra_user = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        row_ra_user.pack(fill='x', pady=2)
        self.settings_widgets.append(row_ra_user)
        ctk.CTkLabel(row_ra_user, text="Username:", width=100, anchor='w').pack(side='left', padx=10)
        self.entry_ra_user = ctk.CTkEntry(row_ra_user, fg_color=C['bg'], border_color=C['dim'])
        self.entry_ra_user.insert(0, self.folder_mappings.get('ra_user', ''))
        self.entry_ra_user.pack(side='left', fill='x', expand=True, padx=10)

        row_ra_key = ctk.CTkFrame(self.settings_scroll, fg_color='transparent')
        row_ra_key.pack(fill='x', pady=2)
        self.settings_widgets.append(row_ra_key)
        ctk.CTkLabel(row_ra_key, text="API Key:", width=100, anchor='w').pack(side='left', padx=10)
        self.entry_ra_key = ctk.CTkEntry(row_ra_key, fg_color=C['bg'], border_color=C['dim'], show="*")
        self.entry_ra_key.insert(0, self.folder_mappings.get('ra_key', ''))
        self.entry_ra_key.pack(side='left', fill='x', expand=True, padx=10)

        btn_save_ra = ctk.CTkButton(self.settings_scroll, text="Save RetroAchievements Keys", fg_color=C['cyan'], text_color='black', command=self.save_ra_creds)
        btn_save_ra.pack(pady=10)
        self.settings_widgets.append(btn_save_ra)

        ra_help = ctk.CTkFrame(self.settings_scroll, fg_color=C['card'])
        ra_help.pack(fill='x', pady=10, padx=10)
        self.settings_widgets.append(ra_help)
        ctk.CTkLabel(ra_help, text="How to get RA key:", font=('Arial', 12, 'bold'), text_color=C['cyan']).pack(anchor='w', padx=10, pady=(10,5))
        ra_steps = ["1. Log in to RetroAchievements.org", "2. Go to My Pages > Settings", "3. Locate 'Web API Key' near the bottom of the page", "4. Copy and paste it here."]
        for s in ra_steps: ctk.CTkLabel(ra_help, text=s, font=('Arial', 11), anchor='w').pack(anchor='w', padx=15)

    def toggle_notif_sound(self):
        self.folder_mappings['notif_sound'] = self.notif_var.get()
        self.save_config()

    def toggle_demo_filter(self):
        self.folder_mappings['filter_demos'] = self.demo_var.get()
        self.save_config()
        self.filter_list()

    def toggle_rev_filter(self):
        self.folder_mappings['filter_revs'] = self.rev_var.get()
        self.save_config()
        self.filter_list()

    def update_font_size(self, value):
        val = int(value)
        self.lbl_font_val.configure(text=str(val))
        self.folder_mappings['font_size'] = val
        self.save_config()
        if self.frame_browser.winfo_viewable():
            self.render_page()

    def clear_saved_folders(self):
        confirm = CustomPopup(self, "Confirm Reset", "Are you sure you want to clear all saved download locations?", ["Yes", "No"])
        if confirm.result == "Yes":
            keys_to_remove = []
            for path in CONSOLES.values():
                if path in self.folder_mappings: keys_to_remove.append(path)
            for k in keys_to_remove: del self.folder_mappings[k]
            self.save_config()
            self.render_settings()
            CustomPopup(self, "Success", "All console folder mappings have been cleared.", ["OK"])

    def apply_folder_structure(self, base_path, remote_path):
        console_key = None
        for k, v in CONSOLES.items():
            if v == remote_path:
                console_key = k
                break
        if not console_key: return base_path
        short_name = SHORT_NAMES.get(console_key, console_key)
        final_path = os.path.join(base_path, short_name)
        if not os.path.exists(final_path):
            try: os.makedirs(final_path)
            except: return base_path
        return final_path

    def change_console_path(self, path):
        browser = ThemedDirBrowser(self, title=f"Select folder for {path}")
        d = browser.result
        if d:
            final_path = self.apply_folder_structure(d, path)
            self.folder_mappings[path] = final_path
            self.save_config()
            self.render_settings()

    def save_twitch_creds(self):
        new_id = self.entry_twitch_id.get().strip()
        new_secret = self.entry_twitch_secret.get().strip()
        self.folder_mappings['twitch_id'] = new_id
        self.folder_mappings['twitch_secret'] = new_secret
        self.save_config()
        self.twitch.client_id = new_id
        self.twitch.client_secret = new_secret
        if self.twitch.authenticate(): CustomPopup(self, "Success", "Twitch Authentication Successful!", ["OK"])
        else: CustomPopup(self, "Failed", "Could not authenticate.\nCheck your Client ID and Secret.", ["OK"])

    def save_ra_creds(self):
        self.folder_mappings['ra_user'] = self.entry_ra_user.get().strip()
        self.folder_mappings['ra_key'] = self.entry_ra_key.get().strip()
        self.save_config()
        self.ra.username = self.entry_ra_user.get().strip()
        self.ra.api_key = self.entry_ra_key.get().strip()
        CustomPopup(self, "Success", "RetroAchievements keys saved.", ["OK"])

    def bind_scroll(self, widget, target_frame):
        widget.bind("<Button-4>", lambda e, t=target_frame: self._on_mouse_scroll(e, t, -1))
        widget.bind("<Button-5>", lambda e, t=target_frame: self._on_mouse_scroll(e, t, 1))
        widget.bind("<MouseWheel>", lambda e, t=target_frame: self._on_mouse_scroll(e, t, 0))

    def _on_mouse_scroll(self, event, widget, direction):
        if direction == 0: widget._parent_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        else: widget._parent_canvas.yview_scroll(direction, "units")

    def refresh_dir(self, path=None):
        self.show_loader()
        target = path if path is not None else self.current_path
        def _work():
            try:
                req_headers = HEADERS.copy()
                if 'myrient.erista.me' not in target:
                    req_headers.pop('Referer', None)
                    req_headers.pop('Origin', None)
                self.net_log(f"Listing: {target[:20]}...")
                clean_path = unquote(target)
                url = BASE_URL + clean_path
                r = requests.get(url, headers=req_headers, timeout=15)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'html.parser')
                parsed = []
                for row in soup.find_all('tr'):
                    links = row.find_all('a')
                    if not links: continue
                    href = links[0].get('href')
                    name = links[0].text.strip()
                    if href in ('../', '/') or name == 'Parent Directory' or '?' in href: continue
                    is_dir = href.endswith('/')
                    size_text = ""
                    cols = row.find_all('td')
                    if len(cols) >= 2 and not is_dir:
                        for c in cols:
                            txt = c.text.strip()
                            if any(x in txt for x in ('M', 'G', 'K', 'B')):
                                if len(txt) < 10 and txt != name:
                                    size_text = txt
                                    break
                    parsed.append({'name': unquote(name).strip('/'), 'href': href, 'type': 'dir' if is_dir else 'file', 'size': size_text})
                self.current_path = target
                self.file_cache = parsed
                self.after(0, self.filter_list)
                self.after(0, self.update_map_btn)
                self.after(0, self.update_storage_stats)
                self.net_log("Idle")
            except Exception as e:
                self.after(0, self.hide_loader)
                self.after(0, lambda: CustomPopup(self, "Error", f"Failed to load: {e}", ["OK"]))
                self.net_log("Network Error")
        threading.Thread(target=_work, daemon=True).start()

    def filter_list(self, event=None):
        search = self.search_var.get().lower()
        region = self.region_var.get().lower()
        ownership = self.status_var.get().lower()
        filter_demos = self.folder_mappings.get('filter_demos', False)
        filter_revs = self.folder_mappings.get('filter_revs', False)
        local_path = self.folder_mappings.get(self.current_path)
        
        filtered = []
        for i in self.file_cache:
            name_lower = i['name'].lower()
            if search and search not in name_lower: continue
            if i['type'] != 'dir':
                if region != 'all regions' and region not in name_lower: continue
                if filter_demos and ("(demo)" in name_lower or " demo" in name_lower): continue
                if filter_revs and ("(rev " in name_lower or " rev " in name_lower): continue
                
                if ownership != 'all status':
                    is_owned = False
                    if local_path and os.path.exists(os.path.join(local_path, i['name'])): is_owned = True
                    if ownership == 'missing only' and is_owned: continue
                    if ownership == 'owned only' and not is_owned: continue
            filtered.append(i)
        
        self.filtered_cache = filtered
        self.current_page = 0
        self.render_page()
        item_count = len([x for x in self.filtered_cache if x['type'] != 'dir'])
        self.btn_dl_all.configure(text=f"⬇ Download All Listed [{item_count}]")

    def render_page(self):
        self.hide_loader()
        for widget in self.browser_widgets:
            widget.pack_forget()
            widget.destroy()
        self.browser_widgets = []
        self.update_idletasks()
        self.lbl_path.configure(text="/" + self.current_path)
        self.checkboxes = []
        local_path = self.folder_mappings.get(self.current_path)
        sorted_items = sorted(self.filtered_cache, key=lambda x: (x['type'] != 'dir', x['name']))
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_items = sorted_items[start:end]
        total_pages = (len(sorted_items) + self.items_per_page - 1) // self.items_per_page
        if total_pages == 0: total_pages = 1
        self.lbl_page.configure(text=f"Page {self.current_page + 1} / {total_pages}")
        self.btn_prev.configure(state='normal' if self.current_page > 0 else 'disabled')
        self.btn_next.configure(state='normal' if end < len(sorted_items) else 'disabled')
        
        current_font_size = self.folder_mappings.get('font_size', 12)
        
        for item in page_items:
            row = ctk.CTkFrame(self.list_frame, fg_color='transparent')
            row.pack(fill='x', pady=2)
            self.browser_widgets.append(row)
            self.bind_scroll(row, self.list_frame)
            if item['type'] == 'dir':
                btn = ctk.CTkButton(row, text=f"📁 {item['name']}", font=('Arial', current_font_size), fg_color='transparent', anchor='w', hover_color=C['pink'], command=lambda href=item['href']: self.refresh_dir(self.current_path + href))
                btn.pack(fill='x')
                self.bind_scroll(btn, self.list_frame)
            else:
                is_owned = False
                if local_path and os.path.exists(os.path.join(local_path, item['name'])): is_owned = True
                var = ctk.IntVar()
                text_col = C['success'] if is_owned else 'white'
                display_text = f"✔ {item['name']}" if is_owned else item['name']
                chk = ctk.CTkCheckBox(row, text=display_text, variable=var, font=('Arial', current_font_size), text_color=text_col, fg_color=C['cyan'], hover_color=C['pink'], command=self.update_selection_counter)
                chk.pack(side='left')
                self.bind_scroll(chk, self.list_frame)
                self.checkboxes.append((var, item['name'], item['href']))
                lbl = ctk.CTkLabel(row, text=item['size'], font=('Arial', current_font_size), text_color=C['dim'])
                lbl.pack(side='right', padx=10)
                self.bind_scroll(lbl, self.list_frame)
                
                clean_name = item['name'].split('(')[0].split('[')[0].strip()
                for w in [row, chk, lbl]:
                    w.bind("<Enter>", lambda e, n=clean_name: self.on_hover_enter(e, n))
                    w.bind("<Leave>", self.on_hover_leave)

    def update_selection_counter(self):
        count = sum(1 for v, n, h in self.checkboxes if v.get() == 1)
        self.btn_dl.configure(text=f"DOWNLOAD SELECTED [{count}]")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        if (self.current_page + 1) * self.items_per_page < len(self.filtered_cache):
            self.current_page += 1
            self.render_page()

    def go_up(self):
        if self.current_path:
            parts = self.current_path.rstrip('/').split('/')
            if len(parts) <= 1: self.refresh_dir('')
            else: self.refresh_dir('/'.join(parts[:-1]) + '/')

    def get_local_folder(self):
        return self.folder_mappings.get(self.current_path)

    def update_map_btn(self):
        path = self.get_local_folder()
        if path: self.btn_map.configure(text=f"📂 {os.path.basename(path)}", fg_color=C['cyan'], text_color='black')
        else: self.btn_map.configure(text="📂 Set Save Folder", fg_color='transparent', text_color=C['cyan'])

    def set_mapping(self):
        browser = ThemedDirBrowser(self, title="Select Download Folder")
        d = browser.result
        if d:
            final_path = self.apply_folder_structure(d, self.current_path)
            self.folder_mappings[self.current_path] = final_path
            self.save_config()
            self.update_map_btn()
            self.update_storage_stats()

    def open_current_folder(self):
        path = self.get_local_folder()
        if not path or not os.path.exists(path):
            CustomPopup(self, "Error", "No valid local folder set for this console.", ["OK"])
            return
        if platform.system() == "Windows": os.startfile(path)
        elif platform.system() == "Darwin": subprocess.Popen(["open", path])
        else: subprocess.Popen(["xdg-open", path])

    def launch_game_folder(self, game_path):
        if not game_path or not os.path.exists(game_path):
            CustomPopup(self, "Error", "File no longer exists at this location.", ["OK"])
            return
        folder_path = os.path.dirname(os.path.abspath(game_path))
        try:
            if platform.system() == "Windows":
                subprocess.run(['explorer', '/select,', os.path.normpath(game_path)])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", game_path])
            else:
                subprocess.Popen(["xdg-open", folder_path])
        except Exception as e:
            CustomPopup(self, "Error", f"Could not open folder: {e}", ["OK"])

    def update_storage_stats(self):
        path = self.get_local_folder()
        if not path or not os.path.exists(path):
            self.storage_label.configure(text="Storage: No Folder Set")
            self.storage_bar.set(0)
            return
        try:
            total, used, free = shutil.disk_usage(path)
            total_gb = total / (2**30)
            free_gb = free / (2**30)
            used_pct = used / total
            self.storage_label.configure(text=f"Storage: {free_gb:.1f} GB Free")
            self.storage_bar.set(used_pct)
            if free_gb < 10: self.storage_bar.configure(progress_color='pink')
            elif free_gb < 50: self.storage_bar.configure(progress_color='orange')
            else: self.storage_bar.configure(progress_color=C['success'])
        except:
            self.storage_label.configure(text="Storage: Unknown")
            self.storage_bar.set(0)

    def add_to_queue(self):
        targets = []
        for v, n, h in self.checkboxes:
            if v.get() == 1: targets.append((n, h))
        if targets: self._queue_items(targets)

    def add_all_to_queue(self):
        if not self.filtered_cache:
            return
        targets = []
        for item in self.filtered_cache:
            if item['type'] != 'dir': targets.append((item['name'], item['href']))
        if targets:
            confirm = CustomPopup(self, "Confirm Bulk Download", f"Are you sure you want to queue {len(targets)} files?", ["Yes", "No"])
            if confirm.result != "Yes": return
            self._queue_items(targets)

    def _queue_items(self, targets):
        local_dir = self.get_local_folder()
        if not local_dir:
            browser = ThemedDirBrowser(self, title="Select Download Folder")
            local_dir = browser.result
            if not local_dir: return
            final_path = self.apply_folder_structure(local_dir, self.current_path)
            local_dir = final_path
            if self.current_path:
                ask_save = CustomPopup(self, "Save Location?", 
                                     f"Do you want to save this folder as the default for this console?\n\n{final_path}", 
                                     ["Yes", "No"])
                if ask_save.result == "Yes":
                    self.folder_mappings[self.current_path] = final_path
                    self.save_config()
                    self.update_map_btn()
                    self.update_storage_stats()

        if not os.path.exists(local_dir):
            try: os.makedirs(local_dir)
            except Exception as e:
                CustomPopup(self, "Error", f"Could not create folder:\n{e}", ["OK"])
                return

        if not os.access(local_dir, os.W_OK):
            CustomPopup(self, "Permission Error", f"Cannot write to:\n{local_dir}", ["OK"])
            return

        cache_map = {item['name']: item for item in self.file_cache}
        
        for name, href in targets:
            url = BASE_URL + self.current_path + href
            game_clean_name = os.path.splitext(name)[0]
            game_folder_path = os.path.join(local_dir, game_clean_name)
            
            size_mb = 0
            if name in cache_map:
                try:
                    raw_size = cache_map[name]['size']
                    clean_str = ''.join(c for c in raw_size if c.isdigit() or c == '.')
                    if clean_str:
                        val = float(clean_str)
                        if 'G' in raw_size: size_mb = val * 1024
                        elif 'M' in raw_size: size_mb = val
                        elif 'K' in raw_size: size_mb = val / 1024
                except: size_mb = 0
                
            self.pending_stage_queue.append({'url': url, 'path': os.path.join(game_folder_path, name), 'name': name, 'size_mb': size_mb, 'folder': game_folder_path})
            
        self.show_queue()
        self.update_batch_labels()
        
        if not self.is_downloading: threading.Thread(target=self.process_queue, daemon=True).start()

    def update_batch_labels(self):
        total_remaining = len(self.pending_stage_queue) + len(self.download_list)
        batches_remaining = (len(self.pending_stage_queue) + 99) // 100
        self.after(0, lambda: self.lbl_total_left.configure(text=f"Total Left: {total_remaining}"))
        self.after(0, lambda: self.lbl_batches_left.configure(text=f"Batches Left: {batches_remaining}"))

    def remove_from_queue(self, index):
        if 0 <= index < len(self.download_list):
            item = self.download_list.pop(index)
            self.log(f"REMOVED: {item['name']}")
            self.render_queue_list()
            self.update_batch_labels()

    def render_queue_list(self):
        for widget in self.queue_widgets: widget.destroy()
        self.queue_widgets = []
        if not self.download_list and not self.pending_stage_queue:
            lbl = ctk.CTkLabel(self.queue_list_frame, text="Queue is empty", text_color=C['dim'])
            lbl.pack(pady=10)
            self.queue_widgets.append(lbl)
            return
            
        for i, item in enumerate(self.download_list):
            row = ctk.CTkFrame(self.queue_list_frame, fg_color='transparent')
            row.pack(fill='x', pady=2)
            self.queue_widgets.append(row)
            self.bind_scroll(row, self.queue_list_frame)
            name_lbl = ctk.CTkLabel(row, text=f"{i+1}. {item['name']}", anchor='w', text_color='white')
            name_lbl.pack(side='left', padx=5, fill='x', expand=True)
            self.bind_scroll(name_lbl, self.queue_list_frame)
            del_btn = ctk.CTkButton(row, text="❌", width=30, fg_color=C['bg'], hover_color=C['pink'], command=lambda idx=i: self.remove_from_queue(idx))
            del_btn.pack(side='right', padx=5)
            self.bind_scroll(del_btn, self.queue_list_frame)

    def log(self, msg):
        self.log_box.insert('end', msg + "\n")
        self.log_box.see('end')

    def play_notification(self):
        if not self.folder_mappings.get('notif_sound', True): return
        if os.name == 'nt' and winsound: winsound.MessageBeep()
        else: print('\a')

    def dl_part(self, url, start, end, fname, headers):
        h = headers.copy()
        h['Range'] = f"bytes={start}-{end}"
        try:
            with requests.get(url, headers=h, stream=True, timeout=30) as r:
                if r.status_code == 403: raise Exception("Blocked/HTML Response")
                r.raise_for_status()
                with open(fname, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        while self.is_paused and not self.cancel_download:
                            time.sleep(0.5)
                        if self.cancel_download: break
                        f.write(chunk)
        except Exception as e: pass
    
    def download_cover(self, game_name, save_folder):
        clean_name = game_name.split('(')[0].split('[')[0].strip()
        self.log(f"🎨 Searching art for: {clean_name}...")
        game_data = self.twitch.search_game(clean_name)
        if game_data and 'cover' in game_data and 'url' in game_data['cover']:
            raw_url = game_data['cover']['url']
            if raw_url.startswith("//"): raw_url = "https:" + raw_url
            hq_url = raw_url.replace("t_thumb", "t_cover_big") 
            try:
                r = requests.get(hq_url, timeout=10)
                if r.status_code == 200:
                    fname = os.path.splitext(game_name)[0] + ".jpg"
                    save_path = os.path.join(save_folder, fname)
                    with open(save_path, 'wb') as f: f.write(r.content)
                    self.log("✔ Art Downloaded")
                else: self.log("⚠ Art found but failed to download")
            except Exception as e: self.log(f"⚠ Art Error: {e}")
        else: self.log("⚠ No art found on IGDB")

    def process_queue(self):
        self.is_downloading = True
        self.cancel_download = False
        self.is_paused = False
        
        self.btn_pause.configure(state='normal', text="Pause Download", fg_color=C['card'], text_color='white')
        self.btn_stop.configure(state='normal', text="Stop Download")
        
        while (self.download_list or self.pending_stage_queue) and not self.cancel_download:
            
            if not self.download_list and self.pending_stage_queue:
                self.log("📦 LOADING NEXT BATCH (100 items)...")
                BATCH_SIZE = 100
                batch = [self.pending_stage_queue.pop(0) for _ in range(min(BATCH_SIZE, len(self.pending_stage_queue)))]
                self.download_list.extend(batch)
                self.after(0, self.render_queue_list)
                self.update_batch_labels()

            if not self.download_list: break 

            try:
                task = self.download_list.pop(0)
                self.update_batch_labels()
                self.after(0, self.render_queue_list)
                
                self.log(f"HYDRA ACTIVE: {task['name']}")
                self.net_log(f"DL: {task['name'][:15]}...")
                
                req_headers = HEADERS.copy()
                if 'myrient.erista.me' not in task['url']:
                    req_headers.pop('Referer', None)
                    req_headers.pop('Origin', None)
                
                try:
                    head = requests.head(task['url'], headers=req_headers, timeout=15, allow_redirects=True)
                    total_length = int(head.headers.get('content-length', 0))
                except: total_length = 0

                if total_length == 0 and task['size_mb'] > 0:
                    total_length = int(task['size_mb'] * 1024 * 1024)

                save_folder = task['folder']
                if not os.path.exists(save_folder):
                    try: os.makedirs(save_folder)
                    except: pass
                
                final_path = task['path']
                if os.name == 'nt' and len(os.path.abspath(final_path)) > 255:
                    final_path = "\\\\?\\" + os.path.abspath(final_path)

                try:
                    total, used, free = shutil.disk_usage(save_folder)
                    if total_length > 0 and free < total_length:
                        self.log("❌ ERROR: Disk Full")
                        continue
                except: pass

                self.download_stats = {'bytes': 0}
                start_t = time.time()
                parts, threads = [], []

                if total_length == 0:
                     self.log("⚠ Unknown Size: Switching to Single-Thread Stream")
                     safe_url = quote(task['url'], safe=':/?=&')
                     with requests.get(safe_url, headers=req_headers, stream=True, timeout=60) as r:
                         r.raise_for_status()
                         with open(final_path, 'wb') as f:
                             for chunk in r.iter_content(chunk_size=8192):
                                 while self.is_paused and not self.cancel_download:
                                     time.sleep(0.5)
                                 if self.cancel_download: break
                                 f.write(chunk)
                                 self.download_stats['bytes'] += len(chunk)
                                 if time.time() - start_t > 0.1:
                                     dl_mb = self.download_stats['bytes']/1024/1024
                                     self.after(0, lambda: self.lbl_speed.configure(text=f"DL: {dl_mb:.1f} MB"))
                                     self.after(0, lambda: self.progress_bar.set(0.5)) 
                else:
                    part_size = total_length // NUM_THREADS
                    for i in range(NUM_THREADS):
                        s = i * part_size
                        e = s + part_size - 1 if i < NUM_THREADS - 1 else total_length - 1
                        fname = f"{final_path}.part{i}"
                        parts.append(fname)
                        t = threading.Thread(target=self.dl_part, args=(task['url'], s, e, fname, req_headers))
                        threads.append(t)
                        t.start()

                    while any(t.is_alive() for t in threads) and not self.cancel_download:
                         if self.is_paused:
                             time.sleep(1)
                             continue
                         time.sleep(0.5)
                         now = time.time()
                         current_size = 0
                         for p in parts:
                             if os.path.exists(p): current_size += os.path.getsize(p)
                         if now - start_t > 0:
                             speed = current_size / (now - start_t) / 1024 / 1024
                             pct = current_size / total_length if total_length > 0 else 0
                             self.after(0, lambda: self.lbl_speed.configure(text=f"DL: {speed:.2f} MB/s"))
                             self.after(0, lambda: self.progress_bar.set(pct))

                if self.cancel_download:
                    self.log("🛑 CANCELLED BY USER")
                    for p in parts:
                        if os.path.exists(p): os.remove(p)
                    if os.path.exists(final_path): os.remove(final_path)
                    break 

                self.log("Stitching...")
                if all(os.path.exists(p) for p in parts) and len(parts) > 0:
                    with open(final_path, 'wb') as f_out:
                        for p in parts:
                            with open(p, 'rb') as f_in:
                                while chunk := f_in.read(1024*1024): f_out.write(chunk)
                            os.remove(p)
                
                if os.path.exists(final_path):
                    if os.path.getsize(final_path) < 2048: self.log("❌ FAILED: File too small (likely HTML error)")
                    else:
                         self.log("✔ COMPLETED")
                         if self.twitch.client_id:
                             save_dir = os.path.dirname(final_path)
                             self.download_cover(task['name'], save_dir)
                         self.play_notification()
                else: self.log("❌ FAILED: File missing after download")
            
            except Exception as e:
                self.log(f"CRITICAL ERROR: {e}")
                traceback.print_exc()

        self.is_downloading = False
        self.cancel_download = False
        self.is_paused = False
        self.btn_pause.configure(state='disabled', text="Pause Download", fg_color=C['card'], text_color='white')
        self.btn_stop.configure(state='disabled', text="Stop Download")
        self.progress_bar.set(0)
        self.update_batch_labels()
        self.after(0, lambda: self.lbl_speed.configure(text="IDLE"))
        self.net_log("Idle")

if __name__ == '__main__':
    try:
        app = UltimateApp()
        app.mainloop()
    except Exception as e:
        error_msg = traceback.format_exc()
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Critical Error", f"MyriFetch Crashed:\n\n{error_msg}")