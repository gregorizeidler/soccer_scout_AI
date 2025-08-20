"""
⚽ Soccer Scout AI - Serviços Específicos para Clubes
Funcionalidades avançadas para necessidades reais de clubes de futebol
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from openai import OpenAI
from config import settings
from services.advanced_filters import AdvancedPlayerFilters, ClubSpecificFilters
from database.models import get_db, Player

class ClubScoutingService:
    """Serviço principal de scouting para clubes"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.filters = AdvancedPlayerFilters()
        self.club_filters = ClubSpecificFilters()
    
    async def intelligent_player_search(self, query: str, club_context: Dict = None) -> Dict:
        """Busca inteligente baseada em linguagem natural"""
        
        # Extrair critérios da consulta usando IA
        criteria = await self._extract_criteria_from_query(query, club_context)
        
        # Buscar jogadores com critérios extraídos
        players = await self.filters.advanced_player_search(criteria)
        
        # Analisar adequação tática se especificado
        if criteria.get('tactical_system'):
            players = await self._analyze_tactical_fit(players, criteria['tactical_system'])
        
        # Gerar explicação da busca
        explanation = await self._generate_search_explanation(query, criteria, players)
        
        return {
            'query': query,
            'criteria_extracted': criteria,
            'players_found': players,
            'total_count': len(players),
            'explanation': explanation,
            'search_time': datetime.now().isoformat()
        }
    
    async def compare_players(self, player_ids: List[int], comparison_type: str = "complete") -> Dict:
        """Comparação avançada entre jogadores"""
        
        db = next(get_db())
        players = db.query(Player).filter(Player.id.in_(player_ids)).all()
        
        if len(players) < 2:
            return {"error": "Precisa de pelo menos 2 jogadores para comparar"}
        
        comparison = {
            'players': [self._player_summary(p) for p in players],
            'comparison_type': comparison_type,
            'analysis': {}
        }
        
        if comparison_type == "complete":
            comparison['analysis'] = await self._complete_comparison(players)
        elif comparison_type == "tactical":
            comparison['analysis'] = await self._tactical_comparison(players)
        elif comparison_type == "financial":
            comparison['analysis'] = await self._financial_comparison(players)
        
        return comparison
    
    async def market_opportunities(self, position: str = None, max_value: float = None) -> Dict:
        """Identificar oportunidades no mercado"""
        
        opportunities = {
            'free_agents': await self._get_free_agents(position, max_value),
            'contract_ending': await self._get_contract_ending_soon(position, max_value),
            'undervalued': await self._get_undervalued_players(position, max_value),
            'loan_opportunities': await self._get_loan_opportunities(position, max_value),
            'rising_stars': await self._get_rising_stars(position, max_value)
        }
        
        # Análise de mercado com IA
        market_analysis = await self._analyze_market_trends(opportunities)
        
        return {
            'opportunities': opportunities,
            'market_analysis': market_analysis,
            'generated_at': datetime.now().isoformat()
        }
    
    async def generate_scouting_report(self, player_id: int, club_context: Dict = None) -> Dict:
        """Gerar relatório completo de scouting"""
        
        db = next(get_db())
        player = db.query(Player).filter(Player.id == player_id).first()
        
        if not player:
            return {"error": "Jogador não encontrado"}
        
        # Análise base do jogador
        player_analysis = self._detailed_player_analysis(player)
        
        # Análise tática se clube_context fornecido
        tactical_analysis = None
        if club_context and club_context.get('tactical_system'):
            tactical_analysis = await self._analyze_single_player_tactics(
                player, club_context['tactical_system']
            )
        
        # Análise financeira
        financial_analysis = self._financial_analysis(player, club_context)
        
        # Predição de performance
        performance_prediction = await self._predict_player_performance(player)
        
        # Comparação com similares
        similar_players = await self._find_similar_players(player)
        
        # Gerar relatório final com IA
        ai_summary = await self._generate_ai_summary(
            player, player_analysis, tactical_analysis, 
            financial_analysis, performance_prediction
        )
        
        return {
            'player': self._player_summary(player),
            'detailed_analysis': player_analysis,
            'tactical_analysis': tactical_analysis,
            'financial_analysis': financial_analysis,
            'performance_prediction': performance_prediction,
            'similar_players': similar_players,
            'ai_summary': ai_summary,
            'report_generated_at': datetime.now().isoformat()
        }
    
    async def _extract_criteria_from_query(self, query: str, club_context: Dict = None) -> Dict:
        """Extrair critérios de busca da linguagem natural"""
        
        if not self.client:
            return self._basic_criteria_extraction(query)
        
        prompt = f"""
        Analise esta consulta de um clube de futebol e extraia os critérios de busca:
        
        CONSULTA: "{query}"
        
        Contexto do clube (se fornecido): {club_context or 'Não fornecido'}
        
        Extraia e retorne APENAS um JSON com os critérios:
        {{
            "position": ["posições válidas"],
            "age_min": número ou null,
            "age_max": número ou null,
            "market_value_max": número em milhões ou null,
            "nationality": ["países"] ou null,
            "preferred_foot": "Right/Left/Both" ou null,
            "goals_min": número ou null,
            "assists_min": número ou null,
            "pace_min": número 1-10 ou null,
            "physical_min": número 1-10 ou null,
            "passing_min": número 1-10 ou null,
            "height_min": número em cm ou null,
            "free_agents": true/false ou null,
            "loan_available": true/false ou null,
            "contract_ending_soon": true/false ou null,
            "injury_prone": false se mencionado ou null,
            "champions_league": true se mencionado ou null,
            "international_experience": true se mencionado ou null,
            "tactical_system": "4-3-3/4-2-3-1/etc" se mencionado ou null,
            "characteristics": ["rápido", "forte", "técnico"] ou null
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            criteria = json.loads(response.choices[0].message.content)
            return criteria
            
        except Exception as e:
            print(f"Erro na extração IA: {e}")
            return self._basic_criteria_extraction(query)
    
    def _basic_criteria_extraction(self, query: str) -> Dict:
        """Extração básica sem IA"""
        criteria = {}
        query_lower = query.lower()
        
        # Posições
        positions_map = {
            'centroavante': 'Centre-Forward', 'atacante': 'Centre-Forward',
            'ponta': 'Winger', 'lateral': 'Full-Back', 'zagueiro': 'Centre-Back',
            'volante': 'Defensive Midfield', 'meia': 'Central Midfield',
            'goleiro': 'Goalkeeper'
        }
        
        for pt_pos, en_pos in positions_map.items():
            if pt_pos in query_lower:
                criteria['position'] = [en_pos]
                break
        
        # Idade
        import re
        age_match = re.search(r'até (\d+) anos?', query_lower)
        if age_match:
            criteria['age_max'] = int(age_match.group(1))
        
        # Valor
        value_match = re.search(r'até (\d+) milhõe?s?', query_lower)
        if value_match:
            criteria['market_value_max'] = float(value_match.group(1))
        
        # Características
        if 'rápido' in query_lower or 'velocidade' in query_lower:
            criteria['pace_min'] = 7.0
        
        if 'forte' in query_lower or 'físico' in query_lower:
            criteria['physical_min'] = 7.0
        
        if 'gols' in query_lower:
            criteria['goals_min'] = 5
        
        return criteria
    
    def _player_summary(self, player: Player) -> Dict:
        """Resumo completo do jogador"""
        return {
            'id': player.id,
            'name': player.name,
            'position': player.position,
            'age': player.age,
            'nationality': player.nationality,
            'current_team': player.current_team,
            'market_value': player.market_value,
            'contract_end': player.contract_end_date.isoformat() if player.contract_end_date else None,
            'goals_season': player.goals_season,
            'assists_season': player.assists_season,
            'overall_rating': player.overall_rating,
            'pace': player.pace,
            'shooting': player.shooting,
            'passing': player.passing,
            'dribbling': player.dribbling,
            'defending': player.defending,
            'physical': player.physical,
            'height': player.height,
            'preferred_foot': player.preferred_foot,
            'international_caps': player.international_caps,
            'free_agent': player.free_agent,
            'loan_player': player.loan_player,
            'injury_prone': player.injury_prone,
            'market_trend': player.market_trend,
            'potential_rating': player.potential_rating
        }
    
    async def _generate_search_explanation(self, query: str, criteria: Dict, players: List) -> str:
        """Gerar explicação da busca realizada"""
        
        if not self.client:
            return f"Busca realizada com {len(criteria)} critérios, {len(players)} jogadores encontrados."
        
        prompt = f"""
        Explique de forma clara e profissional os resultados desta busca:
        
        CONSULTA ORIGINAL: "{query}"
        CRITÉRIOS EXTRAÍDOS: {criteria}
        JOGADORES ENCONTRADOS: {len(players)}
        
        Explique em português, de forma que um dirigente de clube entenda:
        1. O que foi buscado
        2. Quantos jogadores atendem os critérios  
        3. Principais características dos resultados
        4. Se algum critério limitou muito os resultados
        
        Máximo 200 palavras, tom profissional.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content
        except:
            return f"Busca realizada com base em {len(criteria)} critérios específicos. Foram encontrados {len(players)} jogadores que atendem às suas necessidades."
    
    async def _get_free_agents(self, position: str = None, max_value: float = None) -> List[Dict]:
        """Buscar agentes livres"""
        criteria = {'free_agents': True, 'overall_rating_min': 6.5}
        if position:
            criteria['position'] = [position]
        if max_value:
            criteria['market_value_max'] = max_value
        
        return await self.filters.advanced_player_search(criteria)
    
    async def _get_contract_ending_soon(self, position: str = None, max_value: float = None) -> List[Dict]:
        """Buscar jogadores com contrato terminando"""
        criteria = {'contract_ending_soon': True, 'overall_rating_min': 6.5}
        if position:
            criteria['position'] = [position]
        if max_value:
            criteria['market_value_max'] = max_value
        
        return await self.filters.advanced_player_search(criteria)
    
    async def _get_undervalued_players(self, position: str = None, max_value: float = None) -> List[Dict]:
        """Buscar jogadores subvalorizados"""
        # Lógica: rating alto mas valor baixo
        criteria = {
            'overall_rating_min': 7.5,
            'market_value_max': max_value or 15.0  # Máximo 15M
        }
        if position:
            criteria['position'] = [position]
        
        return await self.filters.advanced_player_search(criteria)
    
    async def _get_loan_opportunities(self, position: str = None, max_value: float = None) -> List[Dict]:
        """Buscar oportunidades de empréstimo"""
        criteria = {'loan_available': True, 'age_max': 25}
        if position:
            criteria['position'] = [position]
        
        return await self.filters.advanced_player_search(criteria)
    
    async def _get_rising_stars(self, position: str = None, max_value: float = None) -> List[Dict]:
        """Buscar estrelas em ascensão"""
        criteria = {
            'age_max': 23,
            'potential_rating_min': 7.5,
            'market_trend': 'rising'
        }
        if position:
            criteria['position'] = [position]
        if max_value:
            criteria['market_value_max'] = max_value
        
        return await self.filters.advanced_player_search(criteria)

class PlayerComparisonService:
    """Serviço especializado em comparação de jogadores"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def detailed_comparison(self, players: List[Player]) -> Dict:
        """Comparação detalhada entre jogadores"""
        
        comparison = {
            'players_count': len(players),
            'categories': {
                'physical': self._compare_physical(players),
                'technical': self._compare_technical(players),
                'performance': self._compare_performance(players),
                'financial': self._compare_financial(players),
                'potential': self._compare_potential(players)
            },
            'overall_ranking': self._rank_players(players),
            'best_for_scenarios': await self._scenario_analysis(players)
        }
        
        return comparison
    
    def _compare_physical(self, players: List[Player]) -> Dict:
        """Comparar atributos físicos"""
        return {
            'height': {p.name: p.height for p in players},
            'pace': {p.name: p.pace for p in players},
            'physical': {p.name: p.physical for p in players},
            'injury_prone': {p.name: p.injury_prone for p in players}
        }
    
    def _compare_technical(self, players: List[Player]) -> Dict:
        """Comparar habilidades técnicas"""
        return {
            'overall_rating': {p.name: p.overall_rating for p in players},
            'shooting': {p.name: p.shooting for p in players},
            'passing': {p.name: p.passing for p in players},
            'dribbling': {p.name: p.dribbling for p in players},
            'defending': {p.name: p.defending for p in players}
        }
    
    def _compare_performance(self, players: List[Player]) -> Dict:
        """Comparar performance estatística"""
        return {
            'goals_season': {p.name: p.goals_season for p in players},
            'assists_season': {p.name: p.assists_season for p in players},
            'pass_accuracy': {p.name: p.pass_accuracy for p in players},
            'dribble_success': {p.name: p.dribble_success_rate for p in players}
        }
    
    def _compare_financial(self, players: List[Player]) -> Dict:
        """Comparar aspectos financeiros"""
        return {
            'market_value': {p.name: p.market_value for p in players},
            'salary_annual': {p.name: p.salary_annual for p in players},
            'contract_end': {p.name: p.contract_end_date.isoformat() if p.contract_end_date else None for p in players},
            'free_agent': {p.name: p.free_agent for p in players}
        }
    
    def _compare_potential(self, players: List[Player]) -> Dict:
        """Comparar potencial e perspectivas"""
        return {
            'age': {p.name: p.age for p in players},
            'potential_rating': {p.name: p.potential_rating for p in players},
            'market_trend': {p.name: p.market_trend for p in players},
            'international_caps': {p.name: p.international_caps for p in players}
        }
    
    def _rank_players(self, players: List[Player]) -> List[Dict]:
        """Ranking geral dos jogadores"""
        ranked = sorted(players, key=lambda p: p.overall_rating or 0, reverse=True)
        
        return [
            {
                'rank': i + 1,
                'name': p.name,
                'overall_rating': p.overall_rating,
                'position': p.position,
                'age': p.age,
                'market_value': p.market_value
            }
            for i, p in enumerate(ranked)
        ]
    
    async def _scenario_analysis(self, players: List[Player]) -> Dict:
        """Análise de qual jogador é melhor para cada cenário"""
        
        scenarios = {
            'immediate_impact': max(players, key=lambda p: p.overall_rating or 0).name,
            'long_term_investment': max(players, key=lambda p: (p.potential_rating or 0) - (p.age or 30)).name,
            'best_value': min(players, key=lambda p: (p.market_value or 999) / max(p.overall_rating or 1, 1)).name,
            'lowest_risk': min(players, key=lambda p: p.age + (10 if p.injury_prone else 0)).name
        }
        
        return scenarios