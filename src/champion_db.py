import json
import request

class ChampionDatabase:
    def __init__(self):
        self.champions = self._load_champions()

    def _load_champions(self):
        """Carga lso datos de campeones desde el Data Dragon de LoL"""
        version = "14.12.1"
        url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/es_ES/champion.json"

        try:
            response = request.get(url)
            data = response.json()
            return {champ["key"]: champ["name"] for champ in data["data"].values()}
        except:
            # Fallback local
            return {"266": "Aatrox", "103": "Ahri", "84": "akali"}  # Ejemplo básico

        def get_champion_name(self, champion_id):
            """Obtiene el nombre de un campeón por su ID"""
            return self.champions.get(str(champion_id), "Desconocido")

    # Ejemplo de uso
if __name__ == "__main__":
    db = ChampionDatabase()
    print(db.get_champion_name(266))  # Devuelve "Aatrox"