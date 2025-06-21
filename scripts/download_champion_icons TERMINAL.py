import os
import requests
import json
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
import sys

# Configuración
BASE_DATA_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
ICON_BASE_URL = "https://ddragon.leagueoflegends.com/cdn/{}/img/champion/"

# Añade el directorio src al path
sys.path.append(str(Path(__file__).parent.parent))
from src.champion_db import ChampionDatabase

class ChampionIconDownloader:
    def __init__(self):
        self.version = self.get_latest_version()
        self.icon_url = ICON_BASE_URL.format(self.version)
        self.db = ChampionDatabase()
        self.icons_dir = "assets/icons"
        os.makedirs(self.icons_dir, exist_ok=True)
        self.metadata_file = os.path.join(self.icons_dir, "metadata.json")
        
    def get_latest_version(self):
        """Obtiene automáticamente la última versión del juego"""
        try:
            response = requests.get(BASE_DATA_URL, timeout=5)
            versions = response.json()
            return versions[0]  # La primera es siempre la más reciente
        except Exception as e:
            print(f"⚠️ Error al obtener versión: {e}. Usando versión por defecto.")
            return "14.14.1"

    def normalize_name(self, champ_name):
        """Normaliza nombres según la API oficial"""
        special_cases = {
            "AurelionSol": "AurelionSol",
            "Wukong": "MonkeyKing",
            "MaestroYi": "MasterYi",
            # ... (todos tus casos especiales)
        }
        normalized = champ_name.replace("'", "").replace(" ", "").replace(".", "")
        return special_cases.get(normalized, normalized)

    def load_metadata(self):
        """Carga metadatos de descargas previas"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"version": "", "downloaded": {}}

    def save_metadata(self, data):
        """Guarda metadatos de la descarga"""
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=2)

    def check_for_updates(self):
        """Verifica si hay iconos nuevos o actualizados"""
        metadata = self.load_metadata()
        needs_update = metadata.get("version") != self.version
        
        if not needs_update:
            print("🔍 Verificando integridad de iconos...")
            existing_files = set(f.split('.')[0] for f in os.listdir(self.icons_dir) 
                           if f.endswith('.png'))
            for champ_id, champ_name in tqdm(self.db.champions.items(), desc="Verificando"):
                file_name = champ_name.replace("'", "").replace(" ", "").lower()
                if file_name not in existing_files:
                    needs_update = True
                    break
        
        return needs_update

    def download_icons(self):
        """Descarga todos los iconos con interfaz mejorada"""
        metadata = self.load_metadata()
        is_first_run = not metadata.get("version")
        
        if is_first_run:
            print("🎮 Descargando base de datos de campeones por primera vez...")
        else:
            if not self.check_for_updates():
                print("✅ Los iconos ya están actualizados.")
                return
            
            print(f"🔄 Actualizando iconos (v{metadata['version']} → v{self.version})...")

        success = []
        failed = []
        metadata["version"] = self.version
        
        # Barra de progreso mejorada
        with tqdm(self.db.champions.items(), desc="📦 Descargando", unit="icon", 
                 bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}") as pbar:
            for champ_id, champ_name in pbar:
                normalized = self.normalize_name(champ_name)
                file_name = champ_name.replace("'", "").replace(" ", "").lower()
                file_path = os.path.join(self.icons_dir, f"{file_name}.png")
                
                try:
                    response = requests.get(self.icon_url + f"{normalized}.png", timeout=5)
                    response.raise_for_status()
                    
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    
                    success.append(champ_name)
                    metadata["downloaded"][champ_id] = file_name
                    pbar.set_postfix_str(f"✅ {champ_name[:10]}...")
                except Exception as e:
                    failed.append((champ_name, str(e)))
                    pbar.set_postfix_str(f"❌ {champ_name[:10]}...")

        self.save_metadata(metadata)
        self.show_summary(success, failed)

    def show_summary(self, success, failed):
        """Muestra un resumen visual detallado"""
        print("\n" + "="*50)
        print(f"📊 RESUMEN - Versión {self.version}")
        print(f"🟢 Descargados: {len(success)}")
        print(f"🔴 Fallidos:    {len(failed)}")
        
        if failed:
            print("\n📝 Errores encontrados:")
            for name, error in failed:
                print(f" - {name}: {error}")
        
        print("\n💾 Iconos guardados en:", os.path.abspath(self.icons_dir))
        print("⏰ Última actualización:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*50 + "\n")

if __name__ == "__main__":
    downloader = ChampionIconDownloader()
    downloader.download_icons()