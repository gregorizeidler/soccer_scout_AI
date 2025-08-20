import requests
import asyncio
from typing import List, Dict, Optional
from config import settings

class SportmonksAPI:
    def __init__(self):
        self.base_url = settings.SPORTMONKS_BASE_URL
        self.api_key = settings.SPORTMONKS_API_KEY
        self.headers = {
            "Authorization": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Fazer requisição para a API da Sportmonks"""
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        
        try:
            # Usar requests de forma assíncrona simulada
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: requests.get(url, headers=self.headers, params=params)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error making request to {url}: {str(e)}")
            # Retornar dados mockados para desenvolvimento
            return self._get_mock_data(endpoint)
    
    def _get_mock_data(self, endpoint: str) -> Dict:
        """Dados mockados para desenvolvimento quando a API não está disponível"""
        if "players" in endpoint:
            return {
                "data": [
                    {
                        "id": 1,
                        "name": "Bruno Fernandes",
                        "position": "Attacking Midfield",
                        "age": 29,
                        "nationality": "Portugal",
                        "team": "Manchester United",
                        "market_value": 75.0,
                        "goals_season": 12,
                        "assists_season": 8,
                        "appearances": 35,
                        "league": "Premier League",
                        "height": 179,
                        "weight": 69,
                        "preferred_foot": "Right"
                    },
                    {
                        "id": 2,
                        "name": "Pedri",
                        "position": "Central Midfield",
                        "age": 21,
                        "nationality": "Spain",
                        "team": "FC Barcelona",
                        "market_value": 90.0,
                        "goals_season": 5,
                        "assists_season": 12,
                        "appearances": 42,
                        "league": "La Liga",
                        "height": 174,
                        "weight": 60,
                        "preferred_foot": "Right"
                    },
                    {
                        "id": 3,
                        "name": "Erling Haaland",
                        "position": "Centre-Forward",
                        "age": 24,
                        "nationality": "Norway",
                        "team": "Manchester City",
                        "market_value": 180.0,
                        "goals_season": 28,
                        "assists_season": 6,
                        "appearances": 38,
                        "league": "Premier League",
                        "height": 194,
                        "weight": 88,
                        "preferred_foot": "Left"
                    }
                ]
            }
        elif "leagues" in endpoint:
            return {
                "data": [
                    {"id": 1, "name": "Premier League", "country": "England"},
                    {"id": 2, "name": "La Liga", "country": "Spain"},
                    {"id": 3, "name": "Serie A", "country": "Italy"},
                    {"id": 4, "name": "Bundesliga", "country": "Germany"},
                    {"id": 5, "name": "Ligue 1", "country": "France"}
                ]
            }
        return {"data": []}
    
    async def get_leagues(self) -> List[Dict]:
        """Obter todas as ligas disponíveis"""
        response = await self._make_request("football/leagues")
        return response.get("data", [])
    
    async def search_players(self, 
                           position: str = None,
                           max_value: float = None,
                           min_goals: int = None,
                           league: str = None,
                           age_max: int = None,
                           age_min: int = None,
                           limit: int = 20) -> List[Dict]:
        """
        Buscar jogadores com base em critérios específicos
        """
        params = {"limit": limit}
        
        # A Sportmonks API tem endpoints específicos para diferentes tipos de busca
        # Aqui simulamos uma busca completa
        response = await self._make_request("football/players", params)
        players = response.get("data", [])
        
        # Filtrar resultados localmente (na API real, isso seria feito via parâmetros)
        filtered_players = []
        for player in players:
            # Aplicar filtros
            if position and position.lower() not in player.get("position", "").lower():
                continue
            if max_value and player.get("market_value", 0) > max_value:
                continue
            if min_goals and player.get("goals_season", 0) < min_goals:
                continue
            if league and league.lower() not in player.get("league", "").lower():
                continue
            if age_max and player.get("age", 0) > age_max:
                continue
            if age_min and player.get("age", 0) < age_min:
                continue
                
            filtered_players.append(player)
            
            if len(filtered_players) >= limit:
                break
        
        return filtered_players
    
    async def get_player_details(self, player_id: int) -> Dict:
        """Obter detalhes completos de um jogador específico"""
        response = await self._make_request(f"football/players/{player_id}")
        return response.get("data", {})
    
    async def get_player_statistics(self, player_id: int, season: str = "2024") -> Dict:
        """Obter estatísticas detalhadas de um jogador"""
        response = await self._make_request(f"football/players/{player_id}/statistics")
        return response.get("data", {})
    
    async def get_teams_by_league(self, league_id: int) -> List[Dict]:
        """Obter times de uma liga específica"""
        response = await self._make_request(f"football/leagues/{league_id}/teams")
        return response.get("data", [])
    
    async def get_transfers(self, player_id: int = None, team_id: int = None) -> List[Dict]:
        """Obter informações de transferências"""
        endpoint = "football/transfers"
        params = {}
        
        if player_id:
            params["player_id"] = player_id
        if team_id:
            params["team_id"] = team_id
            
        response = await self._make_request(endpoint, params)
        return response.get("data", [])