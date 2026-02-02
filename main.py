import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
import webbrowser
from threading import Thread
from PIL import Image, ImageTk
import io
import re
from concurrent.futures import ThreadPoolExecutor
import os
import subprocess
from tkinter import messagebox

# --- CONFIGURATION ---
THEME_COLOR = "#0a0b0e" 
ACCENT_COLOR = "#3b82f6" 
CARD_COLOR = "#1c1f2b"
STATUS_BAR_COLOR = "#0f111a"

class JDManager:
    def __init__(self):
        self.possible_paths = [
            os.path.join(os.environ['LOCALAPPDATA'], 'JDownloader 2.0', 'JDownloader2.exe'),
            r"C:\Program Files\JDownloader 2.0\JDownloader2.exe",
            r"C:\Program Files (x86)\JDownloader 2.0\JDownloader2.exe",
            r"C:\JDownloader 2.0\JDownloader2.exe"
        ]
        self.exe_path = self.find_jd()

    def find_jd(self):
        for path in self.possible_paths:
            if os.path.exists(path):
                return path
        return None

    def install_jd(self):
        url = "https://installer.jdownloader.org/JDownloader2Setup.exe"
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
        dest = os.path.join(desktop, "JDownloader_Install.exe")
        
        try:
            if os.path.exists(dest):
                try: os.remove(dest)
                except: pass

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            r = requests.get(url, headers=headers, stream=True, timeout=20)
            r.raise_for_status()
            
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            subprocess.Popen([dest])
            return True

        except Exception as e:
            print(f"Erreur téléchargement: {e}")
            webbrowser.open("https://jdownloader.org/jdownloader2")
            return False

    def send_link(self, link):
        if self.exe_path and os.path.exists(self.exe_path):
            try:
                subprocess.Popen([self.exe_path, link])
                return True
            except: return False
        return False

class NexusLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("NEXUS LAUNCHER")
        self.geometry("1400x950")
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=THEME_COLOR)
        
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.jd_manager = JDManager()
        
        self.current_slug = ""
        self.current_page = 1
        self.is_search_mode = False
        self.load_more_btn = None
        self.global_index = 0

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # SIDEBAR
        self.sidebar = ctk.CTkFrame(self, width=260, fg_color="#12141c", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(self.sidebar, text="NEXUS //", font=("Segoe UI Display", 28, "bold"), text_color=ACCENT_COLOR).pack(pady=(40, 5), padx=25, anchor="w")
        
        status_text = "JD2 CONNECTÉ ✅" if self.jd_manager.exe_path else "JD2 MANQUANT ❌"
        status_col = "#2ecc71" if self.jd_manager.exe_path else "#e74c3c"
        self.lbl_jd_status = ctk.CTkLabel(self.sidebar, text=status_text, font=("Segoe UI", 10, "bold"), text_color=status_col)
        self.lbl_jd_status.pack(pady=(0, 20), padx=25, anchor="w")

        self.nav_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.nav_scroll.pack(fill="both", expand=True, padx=5, pady=5)

        tags = [
            ("🔥 Accueil (Tout)", ""),
            ("🚜 Simulation", "simulation"),
            ("🔫 Action", "action"),
            ("🗺️ Aventure", "adventure"),
            ("🏰 Stratégie", "strategy"),
            ("🧟 Horreur", "horror"),
            ("🏎️ Racing", "racing"),
            ("⚽ Sport", "sports"),
            ("🚀 Sci-Fi", "sci-fi"),
            ("💀 Survival", "survival"),
            ("🌍 Open World", "open-world"),
            ("👾 RPG", "rpg"),
            ("⚔️ Hack & Slash", "hack-and-slash")
        ]

        for name, slug in tags:
            btn = ctk.CTkButton(self.nav_scroll, text=name, anchor="w", fg_color="transparent", 
                                hover_color="#202430", height=35, font=("Segoe UI", 12, "bold"), 
                                command=lambda s=slug, t=name: self.reset_and_scan(s, t))
            btn.pack(fill="x", pady=2)

        self.btn_install_jd = ctk.CTkButton(self.sidebar, text="📥 INSTALLER JD2", 
                                            fg_color="#222533", hover_color="#27ae60", 
                                            font=("Segoe UI", 11, "bold"), command=self.ask_install_jd)
        self.btn_install_jd.pack(side="bottom", fill="x", padx=20, pady=20)

        # MAIN
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=20, pady=(20, 0))
        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self.main, height=60, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        title_cont = ctk.CTkFrame(self.header, fg_color="transparent")
        title_cont.pack(side="left")
        self.lbl_title = ctk.CTkLabel(title_cont, text="BIBLIOTHÈQUE", font=("Segoe UI", 28, "bold"), text_color="white")
        self.lbl_title.pack(side="left")
        self.lbl_counter = ctk.CTkLabel(title_cont, text="(0 JEUX)", font=("Segoe UI", 14, "bold"), text_color=ACCENT_COLOR)
        self.lbl_counter.pack(side="left", padx=(10, 0), pady=(5,0))

        self.entry_search = ctk.CTkEntry(self.header, placeholder_text="Rechercher...", width=300, fg_color="#222533", border_width=0, height=45)
        self.entry_search.pack(side="right", padx=10)
        ctk.CTkButton(self.header, text="GO", width=60, height=45, fg_color=ACCENT_COLOR, command=self.trigger_search).pack(side="right")

        self.scroll = ctk.CTkScrollableFrame(self.main, fg_color="transparent")
        self.scroll.grid(row=1, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure((0,1,2,3), weight=1)

        # STATUT
        self.status_bar = ctk.CTkFrame(self, height=30, fg_color=STATUS_BAR_COLOR, corner_radius=0)
        self.status_bar.grid(row=1, column=1, sticky="ew")
        self.status_lbl = ctk.CTkLabel(self.status_bar, text="Prêt.", font=("Segoe UI", 11), text_color="gray")
        self.status_lbl.pack(side="left", padx=20)
        self.status_indicator = ctk.CTkLabel(self.status_bar, text="●", font=("Arial", 14), text_color="green")
        self.status_indicator.pack(side="right", padx=(0, 20))

    def set_status(self, text, busy=False):
        try:
            self.status_lbl.configure(text=text)
            self.status_indicator.configure(text_color="orange" if busy else "green")
        except: pass

    def ask_install_jd(self):
        self.jd_manager.exe_path = self.jd_manager.find_jd()
        if self.jd_manager.exe_path:
            self.lbl_jd_status.configure(text="JD2 CONNECTÉ ✅", text_color="#2ecc71")
            messagebox.showinfo("Succès", "JDownloader 2 est maintenant détecté !")
            return
        
        ans = messagebox.askyesno("Installation", "Télécharger JDownloader 2 sur le Bureau ?")
        if ans:
            self.set_status("Téléchargement de l'installateur...", busy=True)
            Thread(target=self.run_install_process).start()

    def run_install_process(self):
        success = self.jd_manager.install_jd()
        if success:
            self.after(0, lambda: self.set_status("Installateur sur le Bureau. Lancez-le !", busy=False))
        else:
            self.after(0, lambda: self.set_status("Echec auto. Site ouvert.", busy=False))

    def handle_download(self, link):
        if not self.jd_manager.exe_path:
            self.jd_manager.exe_path = self.jd_manager.find_jd()
        
        if self.jd_manager.exe_path:
            self.set_status("Envoi vers JDownloader...", busy=True)
            self.jd_manager.send_link(link)
            self.after(2000, lambda: self.set_status("Lien envoyé à JD2.", busy=False))
        else:
            ans = messagebox.askyesno("JD2 Manquant", "JDownloader n'est pas installé.\nOuvrir le lien dans le navigateur ?")
            if ans: webbrowser.open(link)
            else: self.ask_install_jd()

    def trigger_search(self):
        q = self.entry_search.get()
        if q: self.reset_and_scan(q, f"Recherche : {q}", is_search=True)

    def reset_and_scan(self, slug, title, is_search=False):
        # On vide tout
        for w in self.scroll.winfo_children(): w.destroy()
        
        self.lbl_title.configure(text=title)
        self.lbl_counter.configure(text="(0 JEUX)")
        self.current_slug = slug
        self.is_search_mode = is_search
        self.current_page = 1
        self.global_index = 0
        Thread(target=self.fetch_page, daemon=True).start()

    def fetch_page(self):
        self.after(0, lambda: self.set_status(f"Chargement page {self.current_page}...", busy=True))
        page = self.current_page
        slug = self.current_slug
        
        if self.is_search_mode:
            if page == 1: url = f"https://fitgirl-repacks.site/?s={slug}"
            else: url = f"https://fitgirl-repacks.site/page/{page}/?s={slug}"
        elif slug == "":
            if page == 1: url = "https://fitgirl-repacks.site/"
            else: url = f"https://fitgirl-repacks.site/page/{page}/"
        else:
            if page == 1: url = f"https://fitgirl-repacks.site/tag/{slug}/"
            else: url = f"https://fitgirl-repacks.site/tag/{slug}/page/{page}/"

        try:
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            if res.status_code != 200: 
                self.after(0, lambda: self.set_status("Fin.", busy=False))
                return

            soup = BeautifulSoup(res.text, 'html.parser')
            articles = soup.find_all('article')
            if not articles: return

            if self.load_more_btn: self.load_more_btn.destroy()

            for art in articles:
                title_tag = art.find(class_='entry-title')
                if not title_tag:
                     header = art.find('header')
                     if header: title_tag = header.find('h1')

                if not title_tag: continue
                raw_title = title_tag.get_text(strip=True)
                if any(bad in raw_title.lower() for bad in ["upcoming", "digest", "discussion", "update", "patch"]): continue

                title = raw_title.split("(")[0].split("v1.")[0].strip()
                a_tag = title_tag.find('a')
                if not a_tag: continue
                link = a_tag['href']
                img_url = None
                img_tag = art.find('img')
                if img_tag: img_url = img_tag['src']

                self.after(0, self.spawn_card, title, link, img_url, self.global_index)
                self.global_index += 1

            self.after(0, lambda: self.lbl_counter.configure(text=f"({self.global_index} JEUX)"))
            self.after(0, self.add_load_more_button)
            self.after(0, lambda: self.set_status("Chargé.", busy=False))

        except Exception as e:
            self.after(0, lambda: self.set_status("Erreur réseau.", busy=False))

    def add_load_more_button(self):
        try:
            row = (self.global_index // 4) + 1
            self.load_more_btn = ctk.CTkButton(self.scroll, text="CHARGER LA SUITE (+)", 
                                               height=50, fg_color="#222533", hover_color=ACCENT_COLOR,
                                               font=("Segoe UI", 14, "bold"),
                                               command=self.load_next_page)
            self.load_more_btn.grid(row=row, column=0, columnspan=4, pady=30, padx=20, sticky="ew")
        except: pass

    def load_next_page(self):
        try:
            self.load_more_btn.configure(text="...", state="disabled")
            self.current_page += 1
            Thread(target=self.fetch_page, daemon=True).start()
        except: pass

    def spawn_card(self, title, link, img_url, index):
        # Vérification 1 : Si la fenêtre n'existe plus (fermeture de l'app), on arrête
        try:
            if not self.winfo_exists(): return
        except: return

        row = index // 4
        col = index % 4
        card = ctk.CTkFrame(self.scroll, fg_color=CARD_COLOR, corner_radius=16)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        img_lbl = ctk.CTkLabel(card, text="", corner_radius=12)
        img_lbl.pack(pady=10, padx=10)
        self.executor.submit(self.load_image, title, img_url, img_lbl)

        short_title = title[:22] + ".." if len(title) > 22 else title
        ctk.CTkLabel(card, text=short_title, font=("Segoe UI", 12, "bold"), text_color="white").pack()

        ctk.CTkButton(card, text="TÉLÉCHARGER (JD2)", height=32, width=140, fg_color=ACCENT_COLOR, corner_radius=20,
                      command=lambda: self.handle_download(link)).pack(pady=12)

    def load_image(self, title, url, label):
        final_img = None
        if url:
            try:
                r = requests.get(url, stream=True, timeout=3)
                final_img = Image.open(io.BytesIO(r.content))
            except: pass
        if not final_img:
            try:
                q = f"https://www.google.com/search?q={title}+pc+game+cover+art&tbm=isch"
                r = requests.get(q, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
                link = re.search(r'src="(https://[^"]+?)"', r.text).group(1)
                final_img = Image.open(io.BytesIO(requests.get(link).content))
            except: pass
        if not final_img:
            final_img = Image.new('RGB', (200, 260), color='#2b2b2b')
        
        self.after(0, lambda: self.update_img_ui(label, final_img))

    def update_img_ui(self, label, img):
        try:
            # FIX CRITIQUE : On vérifie si le label existe encore avant de le mettre à jour
            # Si l'utilisateur a changé de page entre temps, label.winfo_exists() sera False
            if label.winfo_exists():
                ctk_img = ctk.CTkImage(img, size=(190, 250))
                label.configure(image=ctk_img)
        except Exception:
            pass # Si ça rate, on ignore silencieusement

if __name__ == "__main__":
    app = NexusLauncher()
    app.mainloop()
