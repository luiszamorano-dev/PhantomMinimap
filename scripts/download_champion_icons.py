import os
import requests
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime, timedelta
import sys
import threading
import logging
from ttkthemes import ThemedTk
from PIL import Image, ImageTk

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("champion_downloader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChampionDownloaderGUI:
    def __init__(self):
        self.root = ThemedTk(theme="arc")
        self.root.title("PhantomMinimap - Actualizador de Campeones")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Configuración inicial
        self.current_version = ""
        self.region = "la1"
        self.language = "es_MX"
        self.total_champs = 0
        self.success_count = 0
        self.failed_count = 0
        self.failed_list = []
        
        # Directorios importantes
        self.base_dir = Path(__file__).parent.parent
        self.assets_dir = self.base_dir / "assets"
        self.config_dir = self.base_dir / "config"
        self.src_dir = self.base_dir / "src"
        
        # Asegurar que existen los directorios
        self.assets_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
        
        # Cargar configuración
        self.settings_path = self.config_dir / "settings.json"
        self.load_settings()
        
        # Configurar UI
        self.setup_ui()
        self.check_connection()

    def load_settings(self):
        """Carga o inicializa la configuración"""
        default_settings = {
            "region": "la1",
            "language": "es_MX",
            "last_version": "",
            "cache_expiry": ""
        }
        
        try:
            if self.settings_path.exists() and self.settings_path.stat().st_size > 0:
                with open(self.settings_path, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = default_settings
                with open(self.settings_path, 'w') as f:
                    json.dump(self.settings, f, indent=2)
                    
            self.region = self.settings["region"]
            self.language = self.settings["language"]
            
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            self.settings = default_settings
            # Crear archivo de configuración nuevo si está corrupto
            with open(self.settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)

    def setup_ui(self):
        """Configura todos los elementos de la interfaz gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.logo_label = ttk.Label(
            header_frame,
            text="🛡️ PhantomMinimap",
            font=("Arial", 14, "bold")
        )
        self.logo_label.pack(side=tk.LEFT)
        
        # Panel de estado
        status_frame = ttk.LabelFrame(
            main_frame,
            text=" Estado ",
            padding=10
        )
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_label = ttk.Label(
            status_frame,
            text="Verificando conexión...",
            font=("Arial", 10)
        )
        self.status_label.pack(anchor=tk.W)
        
        self.version_label = ttk.Label(
            status_frame,
            text="Versión del juego: Desconocida",
            font=("Arial", 10)
        )
        self.version_label.pack(anchor=tk.W)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(
            main_frame,
            orient=tk.HORIZONTAL,
            mode='determinate'
        )
        self.progress.pack(fill=tk.X, pady=(0, 15))
        
        # Área de detalles
        details_frame = ttk.LabelFrame(
            main_frame,
            text=" Detalles ",
            padding=10
        )
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        self.details_text = scrolledtext.ScrolledText(
            details_frame,
            height=12,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Configurar estilos de texto
        self.details_text.tag_config("success", foreground="green")
        self.details_text.tag_config("error", foreground="red")
        self.details_text.tag_config("warning", foreground="orange")
        self.details_text.tag_config("info", foreground="blue")
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.action_button = ttk.Button(
            button_frame,
            text="Iniciar Descarga",
            command=self.start_download
        )
        self.action_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Cerrar",
            command=self.root.quit
        ).pack(side=tk.RIGHT, padx=5)

    def check_connection(self):
        """Verifica la conexión a internet"""
        def check():
            try:
                requests.get("https://ddragon.leagueoflegends.com", timeout=5)
                self.root.after(0, self.on_connection_success)
            except Exception as e:
                self.root.after(0, self.on_connection_error, str(e))
        
        threading.Thread(target=check, daemon=True).start()
    
    def on_connection_success(self):
        """Callback cuando hay conexión"""
        self.status_label.config(text="✓ Conectado al servidor")
        self.log_message("Conexión establecida", "success")
        self.get_latest_version()
    
    def on_connection_error(self, error):
        """Callback cuando falla la conexión"""
        self.status_label.config(text="✗ Sin conexión")
        self.log_message(f"Error de conexión: {error}", "error")
        self.action_button.config(state=tk.DISABLED)
        messagebox.showerror(
            "Error de Conexión",
            "No se pudo conectar al servidor.\nVerifica tu conexión a internet.",
            parent=self.root
        )
    
    def log_message(self, message, tag=None):
        """Añade un mensaje al área de detalles"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} {message}\n", tag)
        self.details_text.config(state=tk.DISABLED)
        self.details_text.see(tk.END)
    
    def start_download(self):
        """Inicia el proceso de descarga (simulado)"""
        self.log_message("Iniciando descarga...", "info")
        self.progress["value"] = 0
        self.action_button.config(state=tk.DISABLED)
        
        # Simular descarga
        for i in range(1, 101):
            if not self.root:
                break
            self.progress["value"] = i
            self.root.update_idletasks()
            self.root.after(100)
        
        self.log_message("Descarga completada", "success")
        self.action_button.config(state=tk.NORMAL)

    def get_latest_version(self):
        """Simula la obtención de la versión"""
        self.current_version = "15.12.1"
        self.version_label.config(text=f"Versión del juego: {self.current_version}")
        self.log_message(f"Versión detectada: {self.current_version}", "info")

if __name__ == "__main__":
    app = ChampionDownloaderGUI()
    app.root.mainloop()