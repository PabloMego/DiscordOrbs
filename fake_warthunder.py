"""
War Thunder Discord Quest Helper
================================
Script de un solo archivo para simular War Thunder en Discord y completar
misiones de Discord Quests (15 minutos de juego o streaming).

Discord detecta el juego por el ejecutable oficial 'aces.exe' y el título de ventana 'War Thunder'.
Este script:
1. Se auto-ejecuta como 'aces.exe' para que Discord lo reconozca de inmediato.
2. Abre una ventana titulada 'War Thunder' con un radar animado (genera frames reales
   para que la detección de streaming de Discord nunca se pause por inactividad).
3. Lleva el cronómetro de 15 minutos exactos y te avisa cuando la misión esté lista.
4. Limpia el ejecutable temporal automáticamente al salir.
"""

import sys
import os
import shutil
import subprocess
import time
import math
import tkinter as tk
from tkinter import ttk, messagebox

TARGET_EXE = "aces.exe"
TARGET_TITLE = "War Thunder"
MISSION_DURATION_SECONDS = 15 * 60  # 15 minutos estándar de misiones Discord

def ensure_running_as_aces():
    current_exe = os.path.basename(sys.executable).lower()
    script_path = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_path)
    aces_path = os.path.join(script_dir, TARGET_EXE)

    if current_exe != TARGET_EXE.lower():
        try:
            if not os.path.exists(aces_path):
                shutil.copyfile(sys.executable, aces_path)
        except Exception as e:
            print(f"[!] Aviso al crear {TARGET_EXE}: {e}")
            aces_path = sys.executable

        cmd = [aces_path, script_path, "--child"]
        try:
            proc = subprocess.Popen(cmd)
            proc.wait()
        finally:
            if os.path.exists(aces_path) and os.path.abspath(aces_path) != os.path.abspath(sys.executable):
                for _ in range(5):
                    try:
                        time.sleep(0.3)
                        os.remove(aces_path)
                        break
                    except Exception:
                        pass
        sys.exit(0)

class WarThunderQuestApp:
    def __init__(self, root):
        self.root = root
        self.root.title(TARGET_TITLE)
        self.root.geometry("540x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#12161a")

        self.start_time = time.time()
        self.radar_angle = 0
        self.completed_alert_sent = False

        self._build_ui()
        self._update_loop()

    def _build_ui(self):
        header = tk.Frame(self.root, bg="#1a2026", pady=12, padx=16)
        header.pack(fill="x")

        title_lbl = tk.Label(
            header,
            text="WAR THUNDER",
            font=("Segoe UI", 18, "bold"),
            fg="#e5b342",
            bg="#1a2026"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header,
            text="Simulador de Presencia para Misiones de Discord (Quests)",
            font=("Segoe UI", 10),
            fg="#8c9aa6",
            bg="#1a2026"
        )
        sub_lbl.pack(anchor="w")

        badge_frame = tk.Frame(self.root, bg="#12161a", pady=10)
        badge_frame.pack(fill="x", padx=20)

        self.status_dot = tk.Label(badge_frame, text="●", font=("Segoe UI", 12), fg="#3ba55d", bg="#12161a")
        self.status_dot.pack(side="left")

        status_text = tk.Label(
            badge_frame,
            text=" Proceso activo: aces.exe (Reconocido por Discord)",
            font=("Segoe UI", 10, "bold"),
            fg="#dcddde",
            bg="#12161a"
        )
        status_text.pack(side="left")

        self.canvas = tk.Canvas(self.root, width=180, height=180, bg="#0d1114", highlightthickness=1, highlightbackground="#2a323b")
        self.canvas.pack(pady=5)

        timer_frame = tk.Frame(self.root, bg="#12161a")
        timer_frame.pack(pady=10)

        tk.Label(timer_frame, text="TIEMPO TRANSCURRIDO", font=("Segoe UI", 9, "bold"), fg="#8c9aa6", bg="#12161a").pack()
        
        self.timer_lbl = tk.Label(
            timer_frame,
            text="00:00:00",
            font=("Consolas", 28, "bold"),
            fg="#ffffff",
            bg="#12161a"
        )
        self.timer_lbl.pack()

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100, length=440)
        self.progress_bar.pack(pady=5)

        self.progress_lbl = tk.Label(
            self.root,
            text="Progreso hacia los 15 minutos: 0.0%",
            font=("Segoe UI", 9),
            fg="#8c9aa6",
            bg="#12161a"
        )
        self.progress_lbl.pack()

        info_box = tk.LabelFrame(
            self.root,
            text=" Instrucciones para completar la Misión de Discord ",
            font=("Segoe UI", 9, "bold"),
            fg="#e5b342",
            bg="#1a2026",
            padx=12,
            pady=8
        )
        info_box.pack(fill="x", padx=20, pady=12)

        steps = (
            "1. En Discord, ve a Ajustes > Privacidad de la actividad y activa 'Compartir tu estado de actividad'.\n"
            "2. En la pestaña de Misiones (Descubrir > Misiones), dale a 'Aceptar misión' de War Thunder.\n"
            "3. Si pide streaming: entra a un canal de voz con un amigo o cuenta secundaria y pulsa el botón 'Transmitir War Thunder' que Discord te mostrará abajo a la izquierda.\n"
            "4. Espera a que este contador llegue a 15:00 minutos y reclama tu recompensa en Discord."
        )
        tk.Label(
            info_box,
            text=steps,
            font=("Segoe UI", 8),
            fg="#c5c8ca",
            bg="#1a2026",
            justify="left",
            wraplength=480
        ).pack(anchor="w")

        btn_frame = tk.Frame(self.root, bg="#12161a")
        btn_frame.pack(fill="x", padx=20, pady=5)

        self.close_btn = tk.Button(
            btn_frame,
            text="Cerrar y Salir",
            command=self.root.destroy,
            bg="#d83a52",
            fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2"
        )
        self.close_btn.pack(side="right")

    def _draw_radar(self):
        self.canvas.delete("all")
        cx, cy, r = 90, 90, 80

        for radius in (25, 50, 75):
            self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#1f2d24", width=1)

        self.canvas.create_line(cx - r, cy, cx + r, cy, fill="#1f2d24", width=1)
        self.canvas.create_line(cx, cy - r, cx, cy + r, fill="#1f2d24", width=1)

        rad = math.radians(self.radar_angle)
        x2 = cx + r * math.cos(rad)
        y2 = cy + r * math.sin(rad)
        self.canvas.create_line(cx, cy, x2, y2, fill="#3ba55d", width=2)

        self.canvas.create_oval(cx + 35, cy - 20, cx + 41, cy - 14, fill="#e5b342", outline="")
        self.canvas.create_text(cx + 45, cy - 25, text="T-34", fill="#8c9aa6", font=("Segoe UI", 7))

        self.radar_angle = (self.radar_angle + 6) % 360

    def _update_loop(self):
        elapsed = int(time.time() - self.start_time)
        hrs = elapsed // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        self.timer_lbl.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")

        progress = min(100.0, (elapsed / MISSION_DURATION_SECONDS) * 100.0)
        self.progress_var.set(progress)

        if elapsed >= MISSION_DURATION_SECONDS:
            self.progress_lbl.config(
                text=f"¡Misión Completada! ({mins} min transcurridos) - Reclama en Discord",
                fg="#3ba55d"
            )
            self.timer_lbl.config(fg="#3ba55d")
            if not self.completed_alert_sent:
                self.completed_alert_sent = True
                try:
                    messagebox.showinfo("¡Misión Lista!", "¡Han pasado los 15 minutos!\nYa puedes reclamar la recompensa en Discord.")
                except Exception:
                    pass
        else:
            remaining = MISSION_DURATION_SECONDS - elapsed
            rem_mins = remaining // 60
            rem_secs = remaining % 60
            self.progress_lbl.config(
                text=f"Progreso hacia los 15 min: {progress:.1f}% (Faltan {rem_mins:02d}:{rem_secs:02d})"
            )

        self._draw_radar()
        self.root.after(40, self._update_loop)

def main():
    ensure_running_as_aces()

    root = tk.Tk()
    app = WarThunderQuestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
