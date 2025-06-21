import os
import requests
import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
import sys
import threading

class ChampionDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Actualizador de Campeones - PhantomMinimap")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Variables
        self.current_version = ""
        self.total_champs = 0
        self.success_count = 0
        self.failed_count = 0
        self.failed_list = []
        self.is_downloading = False
        self.stop_flag = False
        
        # Estilo
        self.setup_ui()
        
        # Iniciar verificación de conexión
        self.check_connection()

    def setup_ui(self):
        """Configura todos los elementos de la interfaz"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo (puedes reemplazar con tu propio logo)
        self.logo_label = ttk.Label(main_frame, text="🎮 PhantomMinimap", font=("Arial", 16, "bold"))
        self.logo_label.pack(pady=(0, 20))
        
        # Panel de estado
        self.status_frame = ttk.LabelFrame(main_frame, text=" Estado ", padding=10)
        self.status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Verificando conexión...")
        self.status_label.pack(anchor=tk.W)
        
        self.version_label = ttk.Label(self.status_frame, text="Versión del juego: Desconocida")
        self.version_label.pack(anchor=tk.W)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, pady=10)
        
        # Log de actividad
        self.log_frame = ttk.LabelFrame(main_frame, text=" Bitácora ", padding=10)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(self.log_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.action_button = ttk.Button(button_frame, text="Iniciar", command=self.toggle_download)
        self.action_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cerrar", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        
        # Configuración de estilos
        self.root.style = ttk.Style()
        self.root.style.configure("TButton", padding=6)
        self.root.style.configure("TLabelFrame", font=("Arial", 10, "bold"))

    def log_message(self, message, tag=None):
        """Añade un mensaje al log con formato"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n", tag)
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
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
        self.log_message("Conexión a internet establecida correctamente", "success")
        self.get_latest_version()
        
    def on_connection_error(self, error):
        """Callback cuando falla la conexión"""
        self.status_label.config(text="✗ Sin conexión")
        self.log_message(f"Error de conexión: {error}", "error")
        self.action_button.config(state=tk.DISABLED)
        messagebox.showerror(
            "Error de Conexión",
            "No se pudo conectar al servidor.\n"
            "Verifica tu conexión a internet e intenta nuevamente.",
            parent=self.root
        )
        
    def get_latest_version(self):
        """Obtiene la última versión del juego"""
        def fetch_version():
            try:
                response = requests.get("https://ddragon.leagueoflegends.com/api/versions.json", timeout=5)
                versions = response.json()
                self.current_version = versions[0]
                self.root.after(0, self.update_version_ui)
            except Exception as e:
                self.root.after(0, self.on_version_error, str(e))
        
        threading.Thread(target=fetch_version, daemon=True).start()
        
    def update_version_ui(self):
        """Actualiza la UI con la versión obtenida"""
        self.version_label.config(text=f"Versión del juego: {self.current_version}")
        self.log_message(f"Versión más reciente detectada: {self.current_version}")
        self.check_existing_icons()
        
    def on_version_error(self, error):
        """Maneja errores al obtener la versión"""
        self.log_message(f"Error al obtener versión: {error}", "error")
        self.version_label.config(text="Versión: Desconocida (usando respaldo)")
        self.current_version = "14.14.1"  # Versión de respaldo
        
    def check_existing_icons(self):
        """Verifica si ya existen iconos descargados"""
        self.icons_dir = os.path.join(Path(__file__).parent.parent, "assets", "icons")
        os.makedirs(self.icons_dir, exist_ok=True)
        
        metadata_file = os.path.join(self.icons_dir, "metadata.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                if metadata.get("version") == self.current_version:
                    self.status_label.config(text="✓ Iconos ya están actualizados")
                    self.log_message("No se encontraron actualizaciones necesarias")
                    return
        
        self.log_message("Preparado para descargar iconos...")
        self.action_button.config(state=tk.NORMAL)
        
    def toggle_download(self):
        """Inicia/detiene la descarga"""
        if self.is_downloading:
            self.stop_flag = True
            self.action_button.config(state=tk.DISABLED)
            self.log_message("Deteniendo descarga...", "warning")
        else:
            self.start_download()
            
    def start_download(self):
        """Inicia el proceso de descarga en un hilo separado"""
        self.is_downloading = True
        self.stop_flag = False
        self.success_count = 0
        self.failed_count = 0
        self.failed_list = []
        
        self.action_button.config(text="Detener")
        self.progress.config(value=0)
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        self.log_message("Iniciando descarga de iconos...", "info")
        
        # Obtener lista de campeones (simulado - reemplaza con tu implementación real)
        from src.champion_db import ChampionDatabase
        db = ChampionDatabase()
        self.total_champs = len(db.champions)
        
        threading.Thread(target=self.download_thread, args=(db.champions,), daemon=True).start()
        
    def download_thread(self, champions):
        """Hilo para descargar los iconos"""
        icon_url = f"https://ddragon.leagueoflegends.com/cdn/{self.current_version}/img/champion/"
        
        for i, (champ_id, champ_name) in enumerate(champions.items()):
            if self.stop_flag:
                break
                
            normalized = self.normalize_name(champ_name)
            file_name = champ_name.replace("'", "").replace(" ", "").lower()
            file_path = os.path.join(self.icons_dir, f"{file_name}.png")
            
            # Actualizar UI
            self.root.after(0, self.update_progress, i, champ_name)
            
            try:
                response = requests.get(icon_url + f"{normalized}.png", timeout=10)
                response.raise_for_status()
                
                with open(file_path, "wb") as f:
                    f.write(response.content)
                
                self.success_count += 1
                self.root.after(0, self.log_message, f"Descargado: {champ_name}", "success")
            except Exception as e:
                self.failed_count += 1
                self.failed_list.append((champ_name, str(e)))
                self.root.after(0, self.log_message, f"Error con {champ_name}: {str(e)}", "error")
            
            # Pequeña pausa para evitar saturar el servidor
            if not self.stop_flag:
                threading.Event().wait(0.1)
        
        self.root.after(0, self.download_complete)
        
    def normalize_name(self, champ_name):
        """Normaliza nombres según la API oficial"""
        special_cases = {
            "AurelionSol": "AurelionSol",
            "Wukong": "MonkeyKing",
            # ... (todos tus casos especiales)
        }
        normalized = champ_name.replace("'", "").replace(" ", "").replace(".", "")
        return special_cases.get(normalized, normalized)
        
    def update_progress(self, current, champ_name):
        """Actualiza la barra de progreso y contadores"""
        progress = (current + 1) / self.total_champs * 100
        self.progress.config(value=progress)
        self.status_label.config(
            text=f"Descargando... ({current + 1}/{self.total_champs}) | {champ_name[:12]}..."
        )
        
    def download_complete(self):
        """Limpieza post-descarga"""
        self.is_downloading = False
        self.action_button.config(text="Iniciar", state=tk.NORMAL)
        
        if self.stop_flag:
            self.status_label.config(text="Descarga detenida por el usuario")
            self.log_message("Descarga interrumpida por el usuario", "warning")
        else:
            self.status_label.config(text="✓ Descarga completada")
            self.log_message("Proceso de descarga finalizado", "info")
            
            # Guardar metadatos
            metadata = {
                "version": self.current_version,
                "timestamp": datetime.now().isoformat(),
                "downloaded": self.success_count,
                "failed": self.failed_count
            }
            
            with open(os.path.join(self.icons_dir, "metadata.json"), 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Mostrar resumen
            self.show_summary()
            
    def show_summary(self):
        """Muestra un resumen de la descarga"""
        summary = (
            f"RESUMEN DE DESCARGA:\n"
            f"• Versión: {self.current_version}\n"
            f"• Iconos descargados: {self.success_count}/{self.total_champs}\n"
            f"• Fallidos: {self.failed_count}\n"
        )
        
        if self.failed_list:
            summary += "\nCampeones con errores:\n"
            for name, error in self.failed_list:
                summary += f"- {name}: {error}\n"
        
        self.log_message(summary, "info")
        
        # Mostrar ventana emergente
        messagebox.showinfo(
            "Descarga Completada",
            f"Proceso finalizado con:\n"
            f"{self.success_count} iconos descargados\n"
            f"{self.failed_count} errores\n\n"
            f"Revisa la bitácora para detalles.",
            parent=self.root
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = ChampionDownloaderGUI(root)
    
    # Configurar tags para colores en el log
    app.log_text.tag_config("error", foreground="red")
    app.log_text.tag_config("success", foreground="green")
    app.log_text.tag_config("warning", foreground="orange")
    app.log_text.tag_config("info", foreground="blue")
    
    root.mainloop()