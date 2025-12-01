"""
Interface graphique CustomTkinter pour l'accordeur.

Fonctions :
- Sélection et analyse de fichiers WAV (data/raw et data/enregistrements)
- Enregistrement rapide (4 s) puis analyse
- Affichage note + écart en cents + statut couleur
- Graphe intégré (time + FFT)

Palette (Dark Flat) :
  - Fond principal : #1E1E2E
  - Secondaire     : #2B2B3B
  - Texte principal: #ECF0F1
  - Texte secondaire: #95A5A6
  - Juste : #2ECC71
  - Trop bas : #F39C12
  - Trop haut: #E74C3C
"""

from __future__ import annotations

import sys
import threading
import subprocess
import tkinter.filedialog as fd
from pathlib import Path
from typing import Optional, Tuple, List

import numpy as np
import sounddevice as sd
import soundfile as sf
import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from src.pitch_detector import detect_f0, preprocess_signal, FRAME_SIZE, FS  # noqa: E402
from src.music_utils import identify_string, get_tuning_status  # noqa: E402

# chemins
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
ENREG_DIR = BASE_DIR / "data" / "enregistrements"

# palette
COLORS = {
    "bg": "#1E1E2E",
    "panel": "#2B2B3B",
    "text": "#ECF0F1",
    "text_secondary": "#95A5A6",
    "juste": "#2ECC71",
    "bas": "#F39C12",
    "haut": "#E74C3C",
}


def load_wav(filepath: Path) -> Tuple[np.ndarray, int]:
    data, fs = sf.read(str(filepath))
    if data.ndim == 2:
        data = data.mean(axis=1)
    return data, fs


class TunerGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Accordeur de Guitare - GUI")
        self.configure(fg_color=COLORS["bg"])
        self.geometry("920x1000")

        RAW_DIR.mkdir(parents=True, exist_ok=True)
        ENREG_DIR.mkdir(parents=True, exist_ok=True)

        self._build_layout()
        self._bind_shortcuts()
        self.refresh_file_list()

    # UI -----------------------------------------------------------------
    def _build_layout(self) -> None:
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # top panel note
        top = ctk.CTkFrame(self, fg_color=COLORS["panel"])
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        top.grid_columnconfigure(0, weight=1)

        self.label_note = ctk.CTkLabel(
            top, text="--", font=("Segoe UI", 64, "bold"), text_color=COLORS["text"]
        )
        self.label_note.grid(row=0, column=0, pady=(8, 0))

        self.label_status = ctk.CTkLabel(
            top, text="Choisissez un fichier ou enregistrez", font=("Segoe UI", 18),
            text_color=COLORS["text_secondary"]
        )
        self.label_status.grid(row=1, column=0, pady=(0, 8))
        self.label_rec = ctk.CTkLabel(
            top, text="", font=("Segoe UI", 16, "bold"), text_color=COLORS["haut"]
        )
        self.label_rec.grid(row=0, column=1, padx=8)

        # middle panel: gauge + info + actions
        mid = ctk.CTkFrame(self, fg_color=COLORS["panel"])
        mid.grid(row=1, column=0, sticky="nsew", padx=16, pady=6)
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_rowconfigure(1, weight=1)

        # gauge (progress bar centrée, -50..+50 cents)
        gauge_frame = ctk.CTkFrame(mid, fg_color="transparent")
        gauge_frame.grid(row=0, column=0, pady=(12, 0))
        self.gauge = ctk.CTkProgressBar(
            gauge_frame, width=520, height=18, corner_radius=9, fg_color="#11111a"
        )
        self.gauge.set(0.5)  # centre
        self.gauge.grid(row=0, column=0, padx=12, pady=8)
        self.gauge_label = ctk.CTkLabel(
            gauge_frame, text="0 cent", font=("Segoe UI", 14), text_color=COLORS["text_secondary"]
        )
        self.gauge_label.grid(row=1, column=0)

        # bottom of mid: file list + actions + info
        bottom = ctk.CTkFrame(mid, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_columnconfigure(2, weight=2)
        bottom.grid_rowconfigure(0, weight=1)

        # file list
        list_frame = ctk.CTkFrame(bottom, fg_color=COLORS["panel"])
        list_frame.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(list_frame, text="Fichiers WAV (les dossiers raw + enregistrements)", text_color=COLORS["text"]).grid(
            row=0, column=0, padx=6, pady=(6, 0)
        )
        self.file_list = ctk.CTkTextbox(list_frame, height=200, fg_color="#1E1E2E", text_color=COLORS["text"])
        self.file_list.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)

        # controls
        ctrl = ctk.CTkFrame(bottom, fg_color=COLORS["panel"])
        ctrl.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        ctrl.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(ctrl, text="Contrôles", text_color=COLORS["text"]).grid(row=0, column=0, pady=(6, 2))
        self.button_refresh = ctk.CTkButton(ctrl, text="Rafraîchir", command=self.refresh_file_list)
        self.button_refresh.grid(row=1, column=0, padx=8, pady=4, sticky="ew")
        self.button_analyze = ctk.CTkButton(ctrl, text="Analyser sélection", command=self.analyze_selected)
        self.button_analyze.grid(row=2, column=0, padx=8, pady=4, sticky="ew")
        self.button_record = ctk.CTkButton(ctrl, text="🔴 Enregistrer 4s", command=self.record_and_analyze)
        self.button_record.grid(row=3, column=0, padx=8, pady=4, sticky="ew")
        self.button_scope = ctk.CTkButton(ctrl, text="Oscillo temps réel", command=self.toggle_scope)
        self.button_scope.grid(row=4, column=0, padx=8, pady=4, sticky="ew")
        self.button_visualiser = ctk.CTkButton(ctrl, text="Visualiser FFT (script)", command=self.launch_visualiser)
        self.button_visualiser.grid(row=5, column=0, padx=8, pady=4, sticky="ew")

        # info (freq + device)
        info = ctk.CTkFrame(bottom, fg_color=COLORS["panel"])
        info.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)
        info.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(info, text="Informations", text_color=COLORS["text"]).grid(row=0, column=0, pady=(6, 2))
        self.label_freq = ctk.CTkLabel(info, text="Freq: -- Hz", text_color=COLORS["text_secondary"], anchor="w")
        self.label_freq.grid(row=1, column=0, sticky="w", padx=8)
        self.label_cents = ctk.CTkLabel(info, text="Cents: --", text_color=COLORS["text_secondary"], anchor="w")
        self.label_cents.grid(row=2, column=0, sticky="w", padx=8)
        self.label_file = ctk.CTkLabel(info, text="Fichier: --", text_color=COLORS["text_secondary"], anchor="w")
        self.label_file.grid(row=3, column=0, sticky="w", padx=8)

        # plot area
        plot_frame = ctk.CTkFrame(self, fg_color=COLORS["panel"])
        plot_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=(6, 12))
        plot_frame.grid_columnconfigure(0, weight=1)
        plot_frame.grid_rowconfigure(0, weight=1)

        fig = Figure(figsize=(7.5, 3.2), dpi=100, facecolor=COLORS["panel"])
        self.ax_time = fig.add_subplot(1, 3, 1)
        self.ax_freq_full = fig.add_subplot(1, 3, 2)
        self.ax_freq_zoom = fig.add_subplot(1, 3, 3)
        self.canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.fig = fig
        # oscillo live buffer
        self._scope_running = False
        self._scope_buffer = np.zeros(FS // 2)
        self._scope_lock = threading.Lock()
        self._scope_stream = None

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-r>", lambda e: self.refresh_file_list())
        self.bind("<Control-R>", lambda e: self.refresh_file_list())
        self.bind("<Escape>", lambda e: self.destroy())

    # Data ----------------------------------------------------------------
    def refresh_file_list(self) -> None:
        files: List[Tuple[Path, str]] = []
        for folder, label in [(RAW_DIR, "raw"), (ENREG_DIR, "enregistrements")]:
            files += [(p, label) for p in folder.glob("*.wav")]
        # trier par date décroissante (plus récents en haut)
        files.sort(key=lambda item: item[0].stat().st_mtime, reverse=True)

        self.files = files
        self.file_list.configure(state="normal")
        self.file_list.delete("1.0", "end")
        if not files:
            self.file_list.insert("end", "Aucun fichier trouvé dans data/raw ou data/enregistrements\n")
        else:
            for idx, (p, label) in enumerate(files, 1):
                self.file_list.insert("end", f"{idx}. {p.name} ({label})\n")
        self.file_list.configure(state="disabled")

    # Helpers -------------------------------------------------------------
    def pick_file_by_input(self) -> Optional[Path]:
        # Lire dernière ligne d'entrée utilisateur dans le textbox (simple approximation)
        # On prend la ligne courante dans l'entrée clavier : demander via popup simple
        num = ctk.CTkInputDialog(text="Numéro de fichier à analyser ?", title="Choix fichier")
        resp = num.get_input()
        if not resp:
            return None
        try:
            idx = int(resp)
        except ValueError:
            return None
        if idx < 1 or idx > len(self.files):
            return None
        return self.files[idx - 1][0]

    def _update_display(self, f0: Optional[float], cents: Optional[float], note: Optional[str], status: str) -> None:
        if f0 is None or cents is None or note is None:
            self.label_note.configure(text="--", text_color=COLORS["text_secondary"])
            self.label_status.configure(text="Aucune fréquence détectée", text_color=COLORS["text_secondary"])
            self.gauge.set(0.5)
            self.gauge_label.configure(text="--")
            self.label_freq.configure(text="Freq: -- Hz")
            self.label_cents.configure(text="Cents: --")
            return

        self.label_note.configure(text=note, text_color=COLORS["text"])
        self.label_freq.configure(text=f"Freq: {f0:.2f} Hz")
        self.gauge_label.configure(text=f"{cents:+.1f} cents")
        self.label_cents.configure(text=f"Cents: {cents:+.1f}")

        # statut couleur + jauge
        if status == "juste":
            color = COLORS["juste"]
            text = "Accordé (juste)"
        elif status == "trop_bas":
            color = COLORS["bas"]
            text = "Trop bas"
        else:
            color = COLORS["haut"]
            text = "Trop haut"

        # gauge set 0..1
        val = max(-50.0, min(50.0, cents)) / 100.0 + 0.5
        self.gauge.configure(progress_color=color)
        self.gauge.set(val)
        self.label_status.configure(text=text, text_color=color)
        self.label_file.configure(text=self.label_file.cget("text"))

    def _plot(self, frame: np.ndarray, fs: int) -> None:
        if self._scope_running:
            return
        self.ax_time.clear()
        self.ax_freq_full.clear()
        self.ax_freq_zoom.clear()

        t = np.arange(len(frame)) / fs
        self.ax_time.plot(t, frame, color=COLORS["text_secondary"])
        self.ax_time.set_title("Fenêtre temps", color=COLORS["text"], fontsize=10)
        self.ax_time.set_xlabel("Temps (s)", color=COLORS["text_secondary"])
        self.ax_time.set_ylabel("Amplitude", color=COLORS["text_secondary"])
        self.ax_time.tick_params(colors=COLORS["text_secondary"])
        self.ax_time.grid(alpha=0.2)

        fft_vals = np.abs(np.fft.rfft(frame))
        fft_freqs = np.fft.rfftfreq(len(frame), 1 / fs)
        # plein spectre
        self.ax_freq_full.plot(fft_freqs, fft_vals, color=COLORS["text_secondary"])
        self.ax_freq_full.set_xlim(0, 2000)
        self.ax_freq_full.set_title("Spectre complet", color=COLORS["text"], fontsize=10)
        self.ax_freq_full.set_xlabel("Fréquence (Hz)", color=COLORS["text_secondary"])
        self.ax_freq_full.set_ylabel("Amplitude", color=COLORS["text_secondary"])
        self.ax_freq_full.tick_params(colors=COLORS["text_secondary"])
        self.ax_freq_full.grid(alpha=0.2)

        # zoom guitare avec annotations top 5
        self.ax_freq_zoom.plot(fft_freqs, fft_vals, color=COLORS["text_secondary"])
        self.ax_freq_zoom.set_xlim(70, 1500)
        self.ax_freq_zoom.set_title("Zoom guitare (70-1500 Hz)", color=COLORS["text"], fontsize=10)
        self.ax_freq_zoom.set_xlabel("Fréquence (Hz)", color=COLORS["text_secondary"])
        self.ax_freq_zoom.set_ylabel("Amplitude", color=COLORS["text_secondary"])
        self.ax_freq_zoom.tick_params(colors=COLORS["text_secondary"])
        self.ax_freq_zoom.grid(alpha=0.2)

        # top 5 pics
        if len(fft_vals) > 0:
            mag_db = 20 * np.log10(fft_vals + 1e-12)
            threshold = mag_db.max() - 20
            peaks_idx = np.where(mag_db > threshold)[0]
            if len(peaks_idx) > 0:
                sorted_idx = peaks_idx[np.argsort(mag_db[peaks_idx])[::-1]]
                for idx in sorted_idx[:5]:
                    f = float(fft_freqs[idx])
                    m = float(mag_db[idx])
                    self.ax_freq_zoom.annotate(
                        f"{f:.1f} Hz", xy=(f, m), xytext=(f, m + 6.0),
                        color=COLORS["text_secondary"],
                        arrowprops=dict(arrowstyle="->", color=COLORS["text_secondary"], lw=0.6),
                        fontsize=8,
                    )

        self.fig.tight_layout()
        self.canvas.draw()

    # Actions -------------------------------------------------------------
    def analyze_signal(self, signal: np.ndarray, fs: int) -> None:
        # arrêter oscillo live pour libérer l'axe temps
        self._stop_scope()
        if len(signal) < FRAME_SIZE:
            self._update_display(None, None, None, "none")
            return
        # choisir une fenêtre au centre
        start = max(0, len(signal) // 3)
        frame = signal[start:start + FRAME_SIZE]
        frame = frame[:FRAME_SIZE]

        f0 = detect_f0(frame, fs=fs)
        if f0 is None:
            self._update_display(None, None, None, "none")
            return

        note, cents = identify_string(f0)
        status = get_tuning_status(cents)
        self._update_display(f0, cents, note, status)
        self._plot(frame, fs)

    def analyze_selected(self) -> None:
        file = self.pick_file_by_input()
        if not file:
            return
        signal, fs = load_wav(file)
        self.analyze_signal(signal, fs)
        self.label_file.configure(text=f"Fichier: {file.name}")

    def launch_visualiser(self) -> None:
        """Lance le script visualiser.py dans un processus séparé."""
        try:
            self._stop_scope()
            initial = BASE_DIR / "data" / "enregistrements"
            if not initial.exists():
                initial = BASE_DIR / "data" / "raw"
            filepath = fd.askopenfilename(
                initialdir=str(initial),
                title="Choisir un fichier WAV",
                filetypes=[("WAV files", "*.wav")],
            )
            if not filepath:
                self.label_status.configure(text="Visualiser annulé", text_color=COLORS["text_secondary"])
                return
            cmd = [sys.executable, str(BASE_DIR / "src" / "visualiser.py"), "--file", filepath]
            subprocess.Popen(cmd, cwd=BASE_DIR)
            self.label_status.configure(text="Visualiser lancé", text_color=COLORS["text_secondary"])
        except Exception as e:
            self.label_status.configure(text=f"Erreur visualiser: {e}", text_color=COLORS["haut"])

    # --- Oscilloscope live ----------------------------------------------
    def _scope_callback(self, indata, frames, time, status) -> None:  # type: ignore[override]
        data = indata[:, 0] if indata.ndim == 2 else indata
        with self._scope_lock:
            buf = np.concatenate([self._scope_buffer, data])
            # garder 0.5 s
            max_len = FS // 2
            if buf.size > max_len:
                buf = buf[-max_len:]
            self._scope_buffer = buf

    def _update_scope(self) -> None:
        if not self._scope_running:
            return
        with self._scope_lock:
            buf = self._scope_buffer.copy()
        if buf.size == 0:
            self.after(80, self._update_scope)
            return
        t = np.arange(buf.size) / FS
        self.ax_time.clear()
        self.ax_time.plot(t, buf, color=COLORS["text_secondary"])
        self.ax_time.set_xlim(t[0], t[-1])
        self.ax_time.set_title("Oscilloscope (live)", color=COLORS["text"], fontsize=10)
        self.ax_time.set_xlabel("Temps (s)", color=COLORS["text_secondary"])
        self.ax_time.set_ylabel("Amplitude", color=COLORS["text_secondary"])
        self.ax_time.tick_params(colors=COLORS["text_secondary"])
        self.ax_time.grid(alpha=0.2)
        self.fig.tight_layout()
        self.canvas.draw()
        self.after(80, self._update_scope)

    def _stop_scope(self) -> None:
        if not getattr(self, "_scope_running", False):
            return
        self._scope_running = False
        if self._scope_stream is not None:
            try:
                self._scope_stream.stop()
                self._scope_stream.close()
            except Exception:
                pass
            self._scope_stream = None
        self.button_scope.configure(text="Oscillo temps réel")
        self.label_status.configure(text="Oscillo arrêté", text_color=COLORS["text_secondary"])

    def _start_scope(self) -> None:
        self._stop_scope()
        self._scope_buffer = np.zeros(FS // 2)
        try:
            stream = sd.InputStream(
                samplerate=FS,
                channels=1,
                callback=self._scope_callback,
                blocksize=1024,
            )
            stream.start()
            self._scope_stream = stream
            self._scope_running = True
            self.button_scope.configure(text="Arrêter oscillo")
            self.label_status.configure(text="Oscilloscope en cours...", text_color=COLORS["text_secondary"])
            self._update_scope()
        except Exception as e:
            self.label_status.configure(text=f"Oscillo indisponible : {e}", text_color=COLORS["haut"])
            self._scope_running = False
            self._scope_stream = None

    def toggle_scope(self) -> None:
        if getattr(self, "_scope_running", False):
            self._stop_scope()
        else:
            self._start_scope()

    # --- Recording with blinking indicator -------------------------------
    def _blink_rec(self) -> None:
        if not getattr(self, "_rec_running", False):
            self.label_rec.configure(text="")
            return
        current = self.label_rec.cget("text")
        self.label_rec.configure(text="● REC" if current == "" else "", text_color=COLORS["haut"])
        self.after(400, self._blink_rec)

    def _record_worker(self, n_samples: int) -> None:
        try:
            recording = sd.rec(n_samples, samplerate=FS, channels=1, dtype="float64")
            sd.wait()
            if recording.ndim == 2:
                signal = recording[:, 0]
            else:
                signal = recording
            ENREG_DIR.mkdir(parents=True, exist_ok=True)
            fname = f"enreg_gui_{len(list(ENREG_DIR.glob('*.wav')))+1}.wav"
            filepath = ENREG_DIR / fname
            sf.write(str(filepath), signal, FS)
            # UI updates back on main thread
            self.after(0, lambda: self._post_record(signal, filepath))
        except Exception as e:
            self.after(0, lambda: self.label_status.configure(text=f"Erreur enregistrement: {e}", text_color=COLORS["haut"]))
        finally:
            self._rec_running = False

    def _post_record(self, signal: np.ndarray, filepath: Path) -> None:
        self.refresh_file_list()
        self.label_status.configure(text=f"Fichier sauvegardé : {filepath.name}", text_color=COLORS["text"])
        self.label_file.configure(text=f"Fichier: {filepath.name}")
        self.label_rec.configure(text="")
        self.analyze_signal(signal, FS)

    def record_and_analyze(self) -> None:
        if getattr(self, "_rec_running", False):
            return
        self._stop_scope()
        duration = 4.0
        n_samples = int(duration * FS)
        self._rec_running = True
        self.label_status.configure(text="Enregistrement...", text_color=COLORS["text_secondary"])
        self.label_rec.configure(text="● REC", text_color=COLORS["haut"])
        self._blink_rec()
        threading.Thread(target=self._record_worker, args=(n_samples,), daemon=True).start()

if __name__ == "__main__":
    app = TunerGUI()
    app.mainloop()
