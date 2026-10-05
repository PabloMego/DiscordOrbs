"""
Discord Game Quest Simulator
============================
Aplicación con interfaz gráfica para simular que estás jugando a cualquier juego en Discord
y completar misiones (Discord Quests) de forma automática.

Características destacadas:
- Búsqueda universal inteligente conectada a la base de datos oficial de Discord (+10.400 juegos reconocidos).
- Reconoce automáticamente el ejecutable oficial (.exe) de cualquier juego que busques por su nombre.
- Presets inmediatos para los juegos más habituales en Discord Quests (War Thunder, Genshin, Fortnite, etc.).
- Soporte para añadir cualquier juego personalizado manualmente.
- Ejecución real bajo el proceso oficial del juego (.exe) para que Discord lo detecte como juego verificado.
- Ventana HUD animada (25-30 FPS) que garantiza que las misiones de streaming de Discord no se pausen por inactividad.
- Cronómetro y barra de progreso de 15 minutos con sonido y notificación al finalizar.
- Autolimpieza de archivos temporales al cerrar.dwwwwwwwwwwwwwdwdwd
"""

import sys
import os
import shutil
import subprocess
import time
import math
import json
import threading
import urllib.request
import winsound
import tkinter as tk
from tkinter import ttk, messagebox

# Presets populares iniciales (siempre disponibles offline al instante)
POPULAR_PRESETS = [
    {"name": "War Thunder", "exe": "aces.exe", "category": "Militar / Acción (Discord Quest)"},
    {"name": "Genshin Impact", "exe": "GenshinImpact.exe", "category": "RPG / Gacha (Discord Quest)"},
    {"name": "Honkai: Star Rail", "exe": "StarRail.exe", "category": "RPG / Estrategia (Discord Quest)"},
    {"name": "Zenless Zone Zero", "exe": "ZenlessZoneZero.exe", "category": "Acción / Gacha (Discord Quest)"},
    {"name": "Wuthering Waves", "exe": "Client-Win64-Shipping.exe", "category": "RPG / Mundo Abierto (Discord Quest)"},
    {"name": "Fortnite", "exe": "FortniteClient-Win64-Shipping.exe", "category": "Battle Royale"},
    {"name": "VALORANT", "exe": "VALORANT-Win64-Shipping.exe", "category": "Shooter Táctico"},
    {"name": "League of Legends", "exe": "League of Legends.exe", "category": "MOBA"},
    {"name": "Counter-Strike 2", "exe": "cs2.exe", "category": "Shooter Táctico"},
    {"name": "Apex Legends", "exe": "r5apex.exe", "category": "Battle Royale"},
    {"name": "Marvel Rivals", "exe": "marvel-win64-shipping.exe", "category": "Hero Shooter"},
    {"name": "Overwatch 2", "exe": "Overwatch.exe", "category": "Hero Shooter"},
    {"name": "Call of Duty", "exe": "cod.exe", "category": "Shooter"},
    {"name": "World of Warcraft", "exe": "Wow.exe", "category": "MMORPG"},
    {"name": "Minecraft", "exe": "javaw.exe", "category": "Sandbox"},
    {"name": "Roblox", "exe": "RobloxPlayerBeta.exe", "category": "Sandbox / Plataforma"},
    {"name": "Rocket League", "exe": "RocketLeague.exe", "category": "Deportes / Acción"},
    {"name": "The Finals", "exe": "Discovery.exe", "category": "Shooter / Acción"},
    {"name": "Dead by Daylight", "exe": "DeadByDaylight-Win64-Shipping.exe", "category": "Supervivencia"},
    {"name": "Palworld", "exe": "Palworld-Win64-Shipping.exe", "category": "Supervivencia / RPG"},
    {"name": "Rainbow Six Siege", "exe": "RainbowSix.exe", "category": "Shooter Táctico"},
    {"name": "Destiny 2", "exe": "destiny2.exe", "category": "Shooter / RPG"},
    {"name": "Cyberpunk 2077", "exe": "Cyberpunk2077.exe", "category": "RPG / Acción"},
    {"name": "Helldivers 2", "exe": "helldivers2.exe", "category": "Shooter Cooperativo"},
    {"name": "Grand Theft Auto V", "exe": "GTA5.exe", "category": "Mundo Abierto"},
    {"name": "ELDEN RING", "exe": "eldenring.exe", "category": "Action RPG"},
    {"name": "Monster Hunter: World", "exe": "MonsterHunterWorld.exe", "category": "Action RPG"},
    {"name": "EA Sports FC 27", "exe": "FC27.exe", "category": "Deportes / Fútbol"},
    {"name": "EA Sports FC 26", "exe": "FC26.exe", "category": "Deportes / Fútbol"},
    {"name": "EA Sports FC 25", "exe": "FC25.exe", "category": "Deportes / Fútbol"},
    {"name": "EA Sports FC 24", "exe": "FC24.exe", "category": "Deportes / Fútbol"}
]

DISCORD_API_URL = "https://discord.com/api/v9/applications/detectable"
CACHE_FILENAME = "discord_games_cache.json"
QUEST_DURATION_SECONDS = 15 * 60  # 15 minutos estándar


# ==============================================================================
# MODO SIMULADOR DE JUEGO (Ventana activa con HUD animado para Discord)
# ==============================================================================
class GameSimulationWindow:
    def __init__(self, root, game_name, exe_name):
        self.root = root
        self.game_name = game_name
        self.exe_name = exe_name

        self.root.title(game_name)
        self.root.geometry("560x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1f22")

        self.start_time = time.time()
        self.completed_alert_sent = False
        self.angle = 0

        self._build_ui()
        self._update_loop()

    def _build_ui(self):
        # Header superior
        header = tk.Frame(self.root, bg="#2b2d31", pady=12, padx=18)
        header.pack(fill="x")

        title_lbl = tk.Label(
            header,
            text=self.game_name.upper(),
            font=("Segoe UI", 16, "bold"),
            fg="#5865F2",
            bg="#2b2d31"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header,
            text=f"Simulación activa ({self.exe_name}) para Discord Quests",
            font=("Segoe UI", 9),
            fg="#949ba4",
            bg="#2b2d31"
        )
        sub_lbl.pack(anchor="w")

        # Badge de estado de detección
        badge_frame = tk.Frame(self.root, bg="#1e1f22", pady=8, padx=20)
        badge_frame.pack(fill="x")

        tk.Label(badge_frame, text="●", font=("Segoe UI", 12), fg="#23a55a", bg="#1e1f22").pack(side="left")
        tk.Label(
            badge_frame,
            text=f" Proceso activo: {self.exe_name} | Detectado por Discord",
            font=("Segoe UI", 9, "bold"),
            fg="#dbdee1",
            bg="#1e1f22"
        ).pack(side="left", padx=4)

        # Canvas con HUD Animado (~25 FPS para streaming)
        self.canvas = tk.Canvas(
            self.root,
            width=220,
            height=160,
            bg="#111214",
            highlightthickness=1,
            highlightbackground="#35373c"
        )
        self.canvas.pack(pady=8)

        # Cronómetro
        timer_box = tk.Frame(self.root, bg="#1e1f22")
        timer_box.pack(pady=6)

        tk.Label(
            timer_box,
            text="TIEMPO DE JUEGO / STREAMING",
            font=("Segoe UI", 9, "bold"),
            fg="#949ba4",
            bg="#1e1f22"
        ).pack()

        self.timer_lbl = tk.Label(
            timer_box,
            text="00:00:00",
            font=("Consolas", 30, "bold"),
            fg="#ffffff",
            bg="#1e1f22"
        )
        self.timer_lbl.pack()

        # Barra de progreso
        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            self.root,
            variable=self.progress_var,
            maximum=100,
            length=480
        )
        self.progress_bar.pack(pady=4)

        self.progress_lbl = tk.Label(
            self.root,
            text="Progreso hacia los 15 min: 0.0%",
            font=("Segoe UI", 9),
            fg="#949ba4",
            bg="#1e1f22"
        )
        self.progress_lbl.pack()

        # Cuadro de instrucciones
        guide_box = tk.LabelFrame(
            self.root,
            text=" Instrucciones de la Misión de Discord ",
            font=("Segoe UI", 9, "bold"),
            fg="#5865F2",
            bg="#2b2d31",
            padx=14,
            pady=8
        )
        guide_box.pack(fill="x", padx=20, pady=10)

        guide_text = (
            "• Discord Quests detecta el juego automáticamente por el nombre del proceso.\n"
            "• Si la misión pide STREAMING: Entra a un canal de voz con un amigo (o cuenta secundaria)"
            " y haz clic en 'Transmitir " + self.game_name + "' en Discord.\n"
            "• La animación del radar genera frames continuos para que Discord no pause el contador.\n"
            "• Al llegar a 15:00 min sonará un aviso y podrás reclamar la recompensa en Discord."
        )
        tk.Label(
            guide_box,
            text=guide_text,
            font=("Segoe UI", 8),
            fg="#dbdee1",
            bg="#2b2d31",
            justify="left",
            wraplength=480
        ).pack(anchor="w")

        # Botón de cerrar
        btn_box = tk.Frame(self.root, bg="#1e1f22")
        btn_box.pack(fill="x", padx=20, pady=8)

        self.close_btn = tk.Button(
            btn_box,
            text="Detener Simulación y Salir",
            command=self.root.destroy,
            bg="#f23f43",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=16,
            pady=7,
            cursor="hand2"
        )
        self.close_btn.pack(side="right")

    def _draw_hud(self):
        self.canvas.delete("all")
        w, h = 220, 160
        cx, cy = w // 2, h // 2

        # Círculos de radar
        self.canvas.create_oval(cx - 60, cy - 60, cx + 60, cy + 60, outline="#2b2d31", width=1)
        self.canvas.create_oval(cx - 35, cy - 35, cx + 35, cy + 35, outline="#2b2d31", width=1)
        self.canvas.create_line(cx - 70, cy, cx + 70, cy, fill="#2b2d31", width=1)
        self.canvas.create_line(cx, cy - 70, cx, cy + 70, fill="#2b2d31", width=1)

        # Línea de escáner rotativo
        rad = math.radians(self.angle)
        x2 = cx + 60 * math.cos(rad)
        y2 = cy + 60 * math.sin(rad)
        self.canvas.create_line(cx, cy, x2, y2, fill="#5865F2", width=2)

        # Puntos de actividad simulados
        self.canvas.create_oval(cx + 25, cy - 18, cx + 30, cy - 13, fill="#23a55a", outline="")
        self.canvas.create_oval(cx - 35, cy + 22, cx - 30, cy + 27, fill="#5865F2", outline="")

        # Indicador de FPS simulados para Discord
        self.canvas.create_text(
            20, 15,
            text="FPS: 30",
            anchor="w",
            fill="#23a55a",
            font=("Consolas", 8, "bold")
        )
        self.canvas.create_text(
            w - 20, 15,
            text="STATUS: ONLINE",
            anchor="e",
            fill="#949ba4",
            font=("Consolas", 8)
        )

        self.angle = (self.angle + 7) % 360

    def _update_loop(self):
        elapsed = int(time.time() - self.start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        self.timer_lbl.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")

        progress = min(100.0, (elapsed / QUEST_DURATION_SECONDS) * 100.0)
        self.progress_var.set(progress)

        if elapsed >= QUEST_DURATION_SECONDS:
            self.progress_lbl.config(
                text=f"¡Misión Completada! ({mins} min) - Reclama tu recompensa en Discord",
                fg="#23a55a"
            )
            self.timer_lbl.config(fg="#23a55a")
            if not self.completed_alert_sent:
                self.completed_alert_sent = True
                try:
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except Exception:
                    pass
                try:
                    messagebox.showinfo(
                        "¡Misión Completada!",
                        f"¡Han pasado los 15 minutos en {self.game_name}!\nYa puedes reclamar tu recompensa en la pestaña de Misiones de Discord."
                    )
                except Exception:
                    pass
        else:
            remaining = QUEST_DURATION_SECONDS - elapsed
            rem_mins = remaining // 60
            rem_secs = remaining % 60
            self.progress_lbl.config(
                text=f"Progreso hacia los 15 min: {progress:.1f}% (Faltan {rem_mins:02d}:{rem_secs:02d})"
            )

        self._draw_hud()
        self.root.after(40, self._update_loop)


# ==============================================================================
# MODO PANEL DE CONTROL (Launcher con Búsqueda Universal en Discord)
# ==============================================================================
class LauncherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Game Simulator - Selector Universal de Juegos")
        self.root.geometry("680x720")
        self.root.minsize(620, 600)
        self.root.configure(bg="#1e1f22")

        self.active_process = None
        self.active_exe_path = None

        # Lista de juegos combinada (Presets + Base de datos Discord)
        self.games = list(POPULAR_PRESETS)
        self.all_discord_games = []
        self.db_ready = False

        self._apply_styles()
        self._build_ui()
        self._populate_list(self.games)

        # Iniciar carga en segundo plano de la base de datos de 10.400+ juegos de Discord
        threading.Thread(target=self._load_discord_database_async, daemon=True).start()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Treeview / Listado
        style.configure(
            "Treeview",
            background="#2b2d31",
            foreground="#dbdee1",
            fieldbackground="#2b2d31",
            borderwidth=0,
            rowheight=28,
            font=("Segoe UI", 9)
        )
        style.map(
            "Treeview",
            background=[("selected", "#5865F2")],
            foreground=[("selected", "#ffffff")]
        )
        style.configure(
            "Treeview.Heading",
            background="#1e1f22",
            foreground="#949ba4",
            font=("Segoe UI", 9, "bold"),
            relief="flat"
        )
        style.map("Treeview.Heading", background=[("active", "#2b2d31")])

        # Progress bar
        style.configure(
            "TProgressbar",
            troughcolor="#1e1f22",
            background="#5865F2",
            bordercolor="#1e1f22",
            lightcolor="#5865F2",
            darkcolor="#5865F2"
        )

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#2b2d31", pady=14, padx=20)
        header.pack(fill="x")

        tk.Label(
            header,
            text="DISCORD GAME SIMULATOR",
            font=("Segoe UI", 16, "bold"),
            fg="#5865F2",
            bg="#2b2d31"
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Busca cualquier juego por su nombre: el programa lo reconocerá con su ejecutable oficial",
            font=("Segoe UI", 9),
            fg="#949ba4",
            bg="#2b2d31"
        ).pack(anchor="w")

        # Barra de búsqueda y estado de la base de datos
        search_card = tk.Frame(self.root, bg="#1e1f22", pady=10, padx=20)
        search_card.pack(fill="x")

        # Fila de búsqueda
        search_row = tk.Frame(search_card, bg="#1e1f22")
        search_row.pack(fill="x")

        tk.Label(
            search_row,
            text="🔍 Buscar juego:",
            font=("Segoe UI", 9, "bold"),
            fg="#dbdee1",
            bg="#1e1f22"
        ).pack(side="left", padx=(0, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        self.search_entry = tk.Entry(
            search_row,
            textvariable=self.search_var,
            font=("Segoe UI", 10),
            bg="#2b2d31",
            fg="#ffffff",
            insertbackground="#ffffff",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#35373c",
            highlightcolor="#5865F2"
        )
        self.search_entry.pack(side="left", fill="x", expand=True)

        # Botón para limpiar búsqueda
        clear_btn = tk.Button(
            search_row,
            text="✕",
            command=lambda: self.search_var.set(""),
            bg="#2b2d31",
            fg="#949ba4",
            relief="flat",
            padx=8,
            cursor="hand2"
        )
        clear_btn.pack(side="left", padx=(4, 0))

        # Indicador de estado de la base de datos oficial
        status_row = tk.Frame(search_card, bg="#1e1f22")
        status_row.pack(fill="x", pady=(4, 0))

        self.db_status_lbl = tk.Label(
            status_row,
            text="⏳ Conectando con base de datos oficial de Discord (+10.400 juegos)...",
            font=("Segoe UI", 8),
            fg="#e5b342",
            bg="#1e1f22"
        )
        self.db_status_lbl.pack(side="left")

        # Contenedor de la lista de juegos
        list_container = tk.Frame(self.root, bg="#1e1f22", padx=20)
        list_container.pack(fill="both", expand=True)

        columns = ("name", "exe", "category")
        self.tree = ttk.Treeview(list_container, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="Juego", anchor="w")
        self.tree.heading("exe", text="Ejecutable Oficial Reconocido (.exe)", anchor="w")
        self.tree.heading("category", text="Origen / Categoría", anchor="w")

        self.tree.column("name", width=220, anchor="w")
        self.tree.column("exe", width=220, anchor="w")
        self.tree.column("category", width=160, anchor="w")

        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self.start_simulation())

        # Cuadro de ayuda / juego manual
        custom_box = tk.LabelFrame(
            self.root,
            text=" ¿No lo encuentras? Añadir manualmente ",
            font=("Segoe UI", 9, "bold"),
            fg="#dbdee1",
            bg="#2b2d31",
            padx=14,
            pady=8
        )
        custom_box.pack(fill="x", padx=20, pady=8)

        f_row = tk.Frame(custom_box, bg="#2b2d31")
        f_row.pack(fill="x")

        tk.Label(f_row, text="Nombre:", font=("Segoe UI", 8, "bold"), fg="#949ba4", bg="#2b2d31").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.custom_name_entry = tk.Entry(f_row, font=("Segoe UI", 9), bg="#1e1f22", fg="#ffffff", insertbackground="#ffffff", relief="flat", highlightthickness=1, highlightbackground="#35373c", width=20)
        self.custom_name_entry.grid(row=0, column=1, padx=4, pady=2)

        tk.Label(f_row, text="Ejecutable (.exe):", font=("Segoe UI", 8, "bold"), fg="#949ba4", bg="#2b2d31").grid(row=0, column=2, sticky="w", padx=(10, 4), pady=2)
        self.custom_exe_entry = tk.Entry(f_row, font=("Segoe UI", 9), bg="#1e1f22", fg="#ffffff", insertbackground="#ffffff", relief="flat", highlightthickness=1, highlightbackground="#35373c", width=20)
        self.custom_exe_entry.grid(row=0, column=3, padx=4, pady=2)

        add_btn = tk.Button(
            f_row,
            text="+ Añadir",
            command=self._add_custom_game,
            bg="#4752c4",
            fg="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=10,
            pady=3,
            cursor="hand2"
        )
        add_btn.grid(row=0, column=4, padx=(8, 0), pady=2)

        # Barra de estado y botones de control inferiores
        action_bar = tk.Frame(self.root, bg="#1e1f22", pady=10, padx=20)
        action_bar.pack(fill="x")

        info_frame = tk.Frame(action_bar, bg="#1e1f22")
        info_frame.pack(side="left", fill="x", expand=True)

        self.selected_info_lbl = tk.Label(
            info_frame,
            text="Escribe en el buscador o selecciona un juego para simular",
            font=("Segoe UI", 9),
            fg="#949ba4",
            bg="#1e1f22"
        )
        self.selected_info_lbl.pack(anchor="w")

        self.status_lbl = tk.Label(
            info_frame,
            text="● Ningún juego en simulación",
            font=("Segoe UI", 9, "bold"),
            fg="#949ba4",
            bg="#1e1f22"
        )
        self.status_lbl.pack(anchor="w")

        # Botones
        btn_box = tk.Frame(action_bar, bg="#1e1f22")
        btn_box.pack(side="right")

        self.stop_btn = tk.Button(
            btn_box,
            text="Detener",
            command=self.stop_simulation,
            bg="#f23f43",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=14,
            pady=7,
            cursor="hand2",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.start_btn = tk.Button(
            btn_box,
            text="▶ Iniciar Simulación",
            command=self.start_simulation,
            bg="#5865F2",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=16,
            pady=7,
            cursor="hand2"
        )
        self.start_btn.pack(side="left")

    def _load_discord_database_async(self):
        """Descarga o carga en caché la base de datos oficial de juegos detectables de Discord"""
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), CACHE_FILENAME)
        loaded_games = []

        # 1. Intentar cargar desde caché local
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    loaded_games = json.load(f)
            except Exception:
                loaded_games = []

        # 2. Si no hay caché, descargar desde la API oficial de Discord
        if not loaded_games:
            try:
                req = urllib.request.Request(DISCORD_API_URL, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=12) as response:
                    raw_data = json.loads(response.read().decode("utf-8"))

                seen_names = set()
                for item in raw_data:
                    name = item.get("name")
                    if not name or name in seen_names:
                        continue

                    # Buscar ejecutable para Windows (win32)
                    for exe_info in item.get("executables", []):
                        if exe_info.get("os") == "win32" or not exe_info.get("os"):
                            raw_exe = exe_info.get("name", "")
                            clean_exe = os.path.basename(raw_exe.replace("\\", "/"))
                            if clean_exe and clean_exe.lower().endswith(".exe"):
                                loaded_games.append({
                                    "name": name,
                                    "exe": clean_exe,
                                    "category": "Discord Oficial"
                                })
                                seen_names.add(name)
                                break

                # Guardar caché para arranques futuros ultra rápidos
                if loaded_games:
                    try:
                        with open(cache_path, "w", encoding="utf-8") as f:
                            json.dump(loaded_games, f)
                    except Exception:
                        pass
            except Exception as e:
                pass

        if loaded_games:
            preset_names = {p["name"].lower() for p in POPULAR_PRESETS}
            filtered_loaded = [g for g in loaded_games if g["name"].lower() not in preset_names]
            self.all_discord_games = POPULAR_PRESETS + filtered_loaded
            self.db_ready = True

            def update_ui():
                count = len(self.all_discord_games)
                self.db_status_lbl.config(
                    text=f"🟢 Base de datos oficial conectada: {count:,} juegos listos para buscar",
                    fg="#23a55a"
                )
                if self.search_var.get().strip():
                    self._on_search()

            self.root.after(0, update_ui)
        else:
            def update_err():
                self.db_status_lbl.config(
                    text=f"ℹ Modo Offline: {len(POPULAR_PRESETS)} presets populares listos",
                    fg="#949ba4"
                )
            self.root.after(0, update_err)

    def _populate_list(self, games_list, limit=150):
        for item in self.tree.get_children():
            self.tree.delete(item)

        displayed = games_list[:limit]
        for game in displayed:
            self.tree.insert("", "end", values=(game["name"], game["exe"], game.get("category", "General")))

        children = self.tree.get_children()
        if children:
            self.tree.selection_set(children[0])
            self._on_select()

    def _on_search(self, *args):
        query = self.search_var.get().lower().strip()
        source_pool = self.all_discord_games if self.all_discord_games else self.games

        if not query:
            self._populate_list(POPULAR_PRESETS)
            return

        exact_matches = []
        starts_matches = []
        contains_matches = []

        for g in source_pool:
            g_name = g["name"].lower()
            g_exe = g["exe"].lower()

            if g_name == query or g_exe == query:
                exact_matches.append(g)
            elif g_name.startswith(query):
                starts_matches.append(g)
            elif query in g_name or query in g_exe:
                contains_matches.append(g)

        filtered = exact_matches + starts_matches + contains_matches
        self._populate_list(filtered)

    def _on_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        vals = self.tree.item(selected[0], "values")
        if vals:
            self.selected_info_lbl.config(
                text=f"Juego: {vals[0]}  |  Ejecutable oficial: {vals[1]}",
                fg="#dbdee1"
            )

    def _add_custom_game(self):
        name = self.custom_name_entry.get().strip()
        exe = self.custom_exe_entry.get().strip()

        if not name or not exe:
            messagebox.showwarning("Campos vacíos", "Por favor introduce el nombre del juego y su ejecutable .exe")
            return

        if not exe.lower().endswith(".exe"):
            exe += ".exe"

        new_game = {"name": name, "exe": exe, "category": "Personalizado"}
        self.games.insert(0, new_game)
        if self.all_discord_games:
            self.all_discord_games.insert(0, new_game)

        self.custom_name_entry.delete(0, "end")
        self.custom_exe_entry.delete(0, "end")
        self._populate_list([new_game] + self.games)
        messagebox.showinfo("Juego añadido", f"Se ha añadido '{name}' ({exe}) listo para simular.")

    def start_simulation(self):
        if self.active_process and self.active_process.poll() is None:
            messagebox.showwarning("Simulación activa", "Ya hay un juego ejecutándose. Detenlo antes de iniciar otro.")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selección", "Por favor selecciona un juego de la lista.")
            return

        vals = self.tree.item(selected[0], "values")
        game_name = vals[0]
        exe_name = vals[1]

        # Validar y preparar el ejecutable
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        target_exe_path = os.path.join(script_dir, exe_name)

        try:
            if not os.path.exists(target_exe_path):
                shutil.copyfile(sys.executable, target_exe_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear {exe_name}:\n{e}")
            return

        # Lanzar el proceso simulador
        cmd = [target_exe_path, script_path, "--simulate", game_name, exe_name]
        try:
            self.active_process = subprocess.Popen(cmd)
            self.active_exe_path = target_exe_path
        except Exception as e:
            messagebox.showerror("Error al iniciar", f"Error al ejecutar el simulador:\n{e}")
            return

        self.status_lbl.config(
            text=f"● Simulando: {game_name} ({exe_name}) [Detectado por Discord]",
            fg="#23a55a"
        )
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        # Monitorear el proceso en segundo plano
        self._check_process()

    def _check_process(self):
        if self.active_process:
            poll = self.active_process.poll()
            if poll is not None:
                self._cleanup_process()
                return
            self.root.after(1000, self._check_process)

    def stop_simulation(self):
        if self.active_process and self.active_process.poll() is None:
            try:
                self.active_process.terminate()
            except Exception:
                pass
        self._cleanup_process()

    def _cleanup_process(self):
        self.active_process = None
        if self.active_exe_path and os.path.exists(self.active_exe_path):
            if os.path.abspath(self.active_exe_path) != os.path.abspath(sys.executable):
                for _ in range(5):
                    try:
                        time.sleep(0.3)
                        os.remove(self.active_exe_path)
                        break
                    except Exception:
                        pass
        self.active_exe_path = None
        self.status_lbl.config(text="● Ningún juego en simulación", fg="#949ba4")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _on_close(self):
        self.stop_simulation()
        self.root.destroy()


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================
def main():
    # Modo simulación de juego individual
    if len(sys.argv) >= 4 and sys.argv[1] == "--simulate":
        game_name = sys.argv[2]
        exe_name = sys.argv[3]
        root = tk.Tk()
        app = GameSimulationWindow(root, game_name, exe_name)
        root.mainloop()
        sys.exit(0)

    # Modo panel de control / Launcher
    root = tk.Tk()
    launcher = LauncherApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
