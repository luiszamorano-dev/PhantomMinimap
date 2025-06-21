import time
import threading
from obswebsocket import obsws, requests
import os
from PIL import Image

class OBSIntegration:
    def __init__(self, host="localhost", port=4444, password=""):
        self.ws = obsws(host, port, password)
        self.running = False
        self.thread = None
        self.overlay_path = os.path.abspath("temp_overlay.png")
        
    def connect(self):
        try:
            self.ws.connect()
            print("Conexión a OBS establecida")
            return True
        except Exception as e:
            print(f"Error conectando a OBS: {e}")
            return False
    
    def disconnect(self):
        self.ws.disconnect()
        print("Desconectado de OBS")
    
    def create_image_source(self, source_name="MinimapaFalso"):
        """Crea una fuente de imagen en OBS si no existe"""
        try:
            # Verificar si la fuente ya existe
            sources = self.ws.call(requests.GetSourcesList())
            for source in sources.getSources():
                if source['name'] == source_name:
                    print(f"Fuente '{source_name}' ya existe")
                    return
            
            # Crear nueva fuente
            self.ws.call(requests.CreateSource(
                sourceName=source_name,
                sourceKind="image_source",
                sceneName="Escena"  # Nombre de tu escena principal
            ))
            print(f"Fuente '{source_name}' creada")
            
            # Configurar la ruta de la imagen
            self.update_image(source_name, self.overlay_path)
        except Exception as e:
            print(f"Error creando fuente: {e}")
    
    def update_image(self, source_name, image_path):
        """Actualiza la imagen de una fuente existente"""
        try:
            self.ws.call(requests.SetSourceSettings(
                sourceName=source_name,
                sourceSettings={"file": image_path}
            ))
            # print(f"Imagen actualizada: {image_path}")
        except Exception as e:
            print(f"Error actualizando imagen: {e}")
    
    def start_streaming_fake_minimap(self, capture, generator, update_interval=2):
        """Inicia el hilo para transmitir el minimapa falso a OBS"""
        if not self.connect():
            return False
        
        self.create_image_source()
        self.running = True
        self.thread = threading.Thread(
            target=self._update_loop,
            args=(capture, generator, update_interval)
        )
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def _update_loop(self, capture, generator, update_interval):
        """Bucle principal de actualización para OBS"""
        while self.running:
            try:
                # 1. Capturar minimapa
                minimap_frame = capture.capture_minimap()
                if minimap_frame is None:
                    time.sleep(update_interval)
                    continue
                
                # 2. Detectar posiciones reales (simulado)
                # En una implementación real, usaríamos nuestro detector de iconos
                real_allies, real_enemies = capture.detect_icons(minimap_frame)
                
                # 3. Generar overlay falso
                fake_overlay = generator.generate_fake_map(
                    minimap_frame, 
                    real_allies, 
                    real_enemies
                )
                
                # 4. Guardar imagen temporal
                fake_overlay.save(self.overlay_path)
                
                # 5. Actualizar OBS
                self.update_image("MinimapaFalso", self.overlay_path)
                
            except Exception as e:
                print(f"Error en bucle de actualización: {e}")
            
            time.sleep(update_interval)
    
    def stop(self):
        """Detiene la transmisión"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.disconnect()

# Ejemplo de uso
if __name__ == "__main__":
    # Importar módulos necesarios para la prueba
    from minimap_capture import MinimapCapture
    from fake_map_generator import FakeMapGenerator
    
    # Configurar capturador
    capture = MinimapCapture()
    capture.set_auto_detect(True)
    
    # Configurar generador
    generator = FakeMapGenerator()
    generator.set_team_composition({
        "aliados": ["Ashe", "Janna", "Garen", "LeeSin", "Zed"],
        "enemigos": ["Caitlyn", "Lux", "Darius", "Khazix", "Yasuo"]
    })
    
    # Configurar OBS
    obs = OBSIntegration(password="tupassword")  # Usa tu contraseña real de OBS
    
    try:
        if obs.start_streaming_fake_minimap(capture, generator):
            print("Transmisión activa. Presiona Ctrl+C para detener...")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("Deteniendo...")
    finally:
        obs.stop()