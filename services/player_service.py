import hashlib
import json
from typing import Dict, List
from datetime import datetime, timedelta

from services.sportmonks_api import SportmonksAPI
from services.openai_service import OpenAIService
from database.models import get_db, SearchCache, Player

class PlayerService:
    def __init__(self, sportmonks_api: SportmonksAPI, openai_service: OpenAIService):
        self.sportmonks_api = sportmonks_api
        self.openai_service = openai_service
        self.cache_duration = timedelta(hours=6)  # Cache por 6 horas
    
    async def process_scout_query(self, query: str) -> Dict:
        """
        Processar consulta completa de scouting:
        1. Verificar cache
        2. Analisar query com IA
        3. Buscar jogadores na API
        4. Gerar explicação
        5. Salvar no cache
        """
        
        # Verificar cache primeiro
        query_hash = self._generate_query_hash(query)
        cached_result = self._get_cached_result(query_hash)
        
        if cached_result:
            return cached_result
        
        # 1. Analisar query com IA
        criteria = await self.openai_service.parse_scout_query(query)
        
        # 2. Buscar jogadores
        players = await self.sportmonks_api.search_players(
            position=criteria.get("position"),
            max_value=criteria.get("max_value"),
            min_goals=criteria.get("min_goals"),
            league=criteria.get("league"),
            age_max=criteria.get("age_max"),
            age_min=criteria.get("age_min"),
            limit=10
        )
        
        # 3. Gerar explicação
        explanation = await self.openai_service.generate_explanation(
            query, players, criteria
        )
        
        # 4. Preparar resultado
        result = {
            "players": players,
            "explanation": explanation,
            "query_processed": json.dumps(criteria, indent=2),
            "total_found": len(players),
            "criteria": criteria
        }
        
        # 5. Salvar no cache
        self._save_to_cache(query_hash, query, result)
        
        return result
    
    def _generate_query_hash(self, query: str) -> str:
        """Gerar hash único para a query"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def _get_cached_result(self, query_hash: str) -> Dict:
        """Buscar resultado no cache"""
        try:
            db = next(get_db())
            cache_entry = db.query(SearchCache).filter(
                SearchCache.query_hash == query_hash
            ).first()
            
            if cache_entry:
                # Verificar se o cache ainda é válido
                if datetime.utcnow() - cache_entry.created_at < self.cache_duration:
                    return json.loads(cache_entry.results)
                else:
                    # Cache expirado, remover
                    db.delete(cache_entry)
                    db.commit()
            
            return None
            
        except Exception as e:
            print(f"Error accessing cache: {str(e)}")
            return None
    
    def _save_to_cache(self, query_hash: str, query: str, result: Dict):
        """Salvar resultado no cache"""
        try:
            db = next(get_db())
            
            # Remover entrada existente se houver
            existing = db.query(SearchCache).filter(
                SearchCache.query_hash == query_hash
            ).first()
            
            if existing:
                db.delete(existing)
            
            # Criar nova entrada
            cache_entry = SearchCache(
                query_hash=query_hash,
                query_text=query,
                results=json.dumps(result)
            )
            
            db.add(cache_entry)
            db.commit()
            
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")
    
    async def get_player_profile(self, player_id: int) -> Dict:
        """Obter perfil completo de um jogador"""
        
        # Buscar detalhes básicos
        player_details = await self.sportmonks_api.get_player_details(player_id)
        
        # Buscar estatísticas
        player_stats = await self.sportmonks_api.get_player_statistics(player_id)
        
        # Buscar histórico de transferências
        transfers = await self.sportmonks_api.get_transfers(player_id=player_id)
        
        # Combinar todas as informações
        profile = {
            **player_details,
            "statistics": player_stats,
            "transfer_history": transfers
        }
        
        return profile
    
    async def compare_players(self, player_ids: List[int]) -> Dict:
        """Comparar múltiplos jogadores"""
        
        profiles = []
        for player_id in player_ids[:4]:  # Máximo 4 jogadores
            profile = await self.get_player_profile(player_id)
            profiles.append(profile)
        
        # Gerar análise comparativa com IA
        comparison = await self.openai_service.generate_comparison(profiles)
        
        return {
            "players": profiles,
            "comparison": comparison
        }
    
    async def get_recommendations(self, criteria: Dict) -> Dict:
        """Obter recomendações baseadas em critérios específicos"""
        
        # Buscar jogadores
        players = await self.sportmonks_api.search_players(**criteria)
        
        # Gerar recomendações personalizadas
        recommendations = await self.openai_service.generate_recommendations(
            players, criteria
        )
        
        return {
            "players": players,
            "recommendations": recommendations,
            "criteria": criteria
        }
    
    async def get_market_insights(self, position: str, league: str = None) -> Dict:
        """Obter insights do mercado para uma posição específica"""
        
        # Buscar jogadores da posição
        players = await self.sportmonks_api.search_players(
            position=position,
            league=league,
            limit=50
        )
        
        # Calcular estatísticas de mercado
        values = [p.get("market_value", 0) for p in players if p.get("market_value")]
        
        if values:
            market_stats = {
                "average_value": sum(values) / len(values),
                "max_value": max(values),
                "min_value": min(values),
                "total_players": len(players)
            }
        else:
            market_stats = {
                "average_value": 0,
                "max_value": 0,
                "min_value": 0,
                "total_players": 0
            }
        
        return {
            "position": position,
            "league": league,
            "market_statistics": market_stats,
            "top_players": players[:10]
        }