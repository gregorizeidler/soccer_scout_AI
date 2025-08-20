"""
🔍 Soccer Scout AI - Sistema de Filtros Avançados para Clubes
Filtros ultra específicos para necessidades reais de clubes de futebol
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from database.models import Player, get_db

class AdvancedPlayerFilters:
    """Sistema de filtros avançados para busca de jogadores"""
    
    def __init__(self):
        self.supported_filters = {
            # Básicos
            'position', 'age_min', 'age_max', 'nationality', 'height_min', 'height_max',
            'preferred_foot', 'market_value_min', 'market_value_max',
            
            # Contratuais
            'contract_ending_soon', 'free_agents', 'loan_available', 'release_clause_max',
            'salary_max',
            
            # Performance
            'goals_min', 'assists_min', 'minutes_min', 'pass_accuracy_min',
            'dribble_success_min', 'tackle_success_min', 'overall_rating_min',
            
            # Características especiais
            'pace_min', 'physical_min', 'international_experience', 'injury_prone',
            'champions_league_experience', 'weak_foot_min', 'skill_moves_min',
            
            # Tendências
            'market_trend', 'potential_rating_min', 'rising_value_only'
        }
    
    async def advanced_player_search(self, filters: Dict[str, Any]) -> List[Dict]:
        """Busca avançada com múltiplos filtros"""
        
        db = next(get_db())
        query = db.query(Player)
        
        # Aplicar filtros básicos
        query = self._apply_basic_filters(query, filters)
        
        # Aplicar filtros contratuais
        query = self._apply_contract_filters(query, filters)
        
        # Aplicar filtros de performance
        query = self._apply_performance_filters(query, filters)
        
        # Aplicar filtros especiais
        query = self._apply_special_filters(query, filters)
        
        # Ordenação inteligente
        query = self._apply_intelligent_sorting(query, filters)
        
        # Limitar resultados
        limit = filters.get('limit', 20)
        players = query.limit(limit).all()
        
        return [self._player_to_dict(player) for player in players]
    
    def _apply_basic_filters(self, query, filters):
        """Filtros básicos de posição, idade, etc."""
        
        if 'position' in filters:
            positions = filters['position'] if isinstance(filters['position'], list) else [filters['position']]
            query = query.filter(Player.position.in_(positions))
        
        if 'age_min' in filters:
            query = query.filter(Player.age >= filters['age_min'])
        
        if 'age_max' in filters:
            query = query.filter(Player.age <= filters['age_max'])
        
        if 'nationality' in filters:
            nationalities = filters['nationality'] if isinstance(filters['nationality'], list) else [filters['nationality']]
            query = query.filter(or_(
                Player.nationality.in_(nationalities),
                Player.second_nationality.in_(nationalities)
            ))
        
        if 'preferred_foot' in filters:
            query = query.filter(Player.preferred_foot == filters['preferred_foot'])
        
        if 'height_min' in filters:
            query = query.filter(Player.height >= filters['height_min'])
        
        if 'height_max' in filters:
            query = query.filter(Player.height <= filters['height_max'])
        
        if 'market_value_min' in filters:
            query = query.filter(Player.market_value >= filters['market_value_min'])
        
        if 'market_value_max' in filters:
            query = query.filter(Player.market_value <= filters['market_value_max'])
        
        return query
    
    def _apply_contract_filters(self, query, filters):
        """Filtros relacionados a contratos e situação financeira"""
        
        if filters.get('free_agents'):
            query = query.filter(Player.free_agent == True)
        
        if filters.get('contract_ending_soon'):
            # Contrato termina em até 6 meses
            cutoff_date = date.today() + timedelta(days=180)
            query = query.filter(Player.contract_end_date <= cutoff_date)
        
        if filters.get('loan_available'):
            query = query.filter(Player.loan_player == True)
        
        if 'release_clause_max' in filters:
            query = query.filter(
                and_(
                    Player.release_clause.isnot(None),
                    Player.release_clause <= filters['release_clause_max']
                )
            )
        
        if 'salary_max' in filters:
            query = query.filter(
                or_(
                    Player.salary_annual.is_(None),
                    Player.salary_annual <= filters['salary_max']
                )
            )
        
        return query
    
    def _apply_performance_filters(self, query, filters):
        """Filtros de performance e estatísticas"""
        
        if 'goals_min' in filters:
            query = query.filter(Player.goals_season >= filters['goals_min'])
        
        if 'assists_min' in filters:
            query = query.filter(Player.assists_season >= filters['assists_min'])
        
        if 'minutes_min' in filters:
            query = query.filter(Player.minutes_played >= filters['minutes_min'])
        
        if 'pass_accuracy_min' in filters:
            query = query.filter(Player.pass_accuracy >= filters['pass_accuracy_min'])
        
        if 'dribble_success_min' in filters:
            query = query.filter(Player.dribble_success_rate >= filters['dribble_success_min'])
        
        if 'tackle_success_min' in filters:
            query = query.filter(Player.tackle_success_rate >= filters['tackle_success_min'])
        
        if 'overall_rating_min' in filters:
            query = query.filter(Player.overall_rating >= filters['overall_rating_min'])
        
        return query
    
    def _apply_special_filters(self, query, filters):
        """Filtros especiais e características únicas"""
        
        if 'pace_min' in filters:
            query = query.filter(Player.pace >= filters['pace_min'])
        
        if 'physical_min' in filters:
            query = query.filter(Player.physical >= filters['physical_min'])
        
        if filters.get('international_experience'):
            query = query.filter(Player.international_caps > 0)
        
        if filters.get('champions_league_experience'):
            query = query.filter(Player.champions_league == True)
        
        if filters.get('injury_prone') is False:
            query = query.filter(Player.injury_prone == False)
        
        if 'weak_foot_min' in filters:
            query = query.filter(Player.weak_foot_rating >= filters['weak_foot_min'])
        
        if 'skill_moves_min' in filters:
            query = query.filter(Player.skill_moves >= filters['skill_moves_min'])
        
        if 'market_trend' in filters:
            query = query.filter(Player.market_trend == filters['market_trend'])
        
        if 'potential_rating_min' in filters:
            query = query.filter(Player.potential_rating >= filters['potential_rating_min'])
        
        if filters.get('rising_value_only'):
            query = query.filter(Player.market_trend == 'rising')
        
        return query
    
    def _apply_intelligent_sorting(self, query, filters):
        """Ordenação inteligente baseada nos filtros"""
        
        # Se busca por gols, ordena por gols
        if 'goals_min' in filters:
            query = query.order_by(Player.goals_season.desc())
        
        # Se busca por valor, ordena por valor
        elif 'market_value_max' in filters:
            query = query.order_by(Player.market_value.asc())
        
        # Se busca jovens, ordena por potencial
        elif filters.get('age_max', 100) <= 23:
            query = query.order_by(Player.potential_rating.desc())
        
        # Ordenação padrão por rating geral
        else:
            query = query.order_by(Player.overall_rating.desc())
        
        return query
    
    def _player_to_dict(self, player: Player) -> Dict:
        """Converter player model para dicionário"""
        return {
            'id': player.id,
            'name': player.name,
            'position': player.position,
            'age': player.age,
            'nationality': player.nationality,
            'current_team': player.current_team,
            'market_value': player.market_value,
            'goals_season': player.goals_season,
            'assists_season': player.assists_season,
            'overall_rating': player.overall_rating,
            'contract_end_date': player.contract_end_date.isoformat() if player.contract_end_date else None,
            'free_agent': player.free_agent,
            'height': player.height,
            'preferred_foot': player.preferred_foot,
            'pace': player.pace,
            'shooting': player.shooting,
            'passing': player.passing,
            'dribbling': player.dribbling,
            'defending': player.defending,
            'physical': player.physical,
            'potential_rating': player.potential_rating,
            'market_trend': player.market_trend,
            'international_caps': player.international_caps,
            'injury_prone': player.injury_prone,
            'champions_league': player.champions_league,
            'release_clause': player.release_clause,
            'salary_annual': player.salary_annual
        }

class ClubSpecificFilters:
    """Filtros específicos para diferentes tipos de necessidades de clubes"""
    
    @staticmethod
    def get_counter_attack_strikers(max_value: float = None, max_age: int = None) -> Dict:
        """Centroavantes ideais para contra-ataques"""
        return {
            'position': 'Centre-Forward',
            'pace_min': 7.0,
            'shooting_min': 7.0,
            'physical_min': 6.5,
            'market_value_max': max_value,
            'age_max': max_age,
            'injury_prone': False
        }
    
    @staticmethod
    def get_ball_playing_defenders(max_value: float = None) -> Dict:
        """Zagueiros que jogam bem com os pés"""
        return {
            'position': 'Centre-Back',
            'passing_min': 7.0,
            'pass_accuracy_min': 85.0,
            'defending_min': 7.5,
            'height_min': 180,
            'market_value_max': max_value
        }
    
    @staticmethod
    def get_creative_midfielders(max_value: float = None) -> Dict:
        """Meias criativos"""
        return {
            'position': ['Central Midfield', 'Attacking Midfield'],
            'passing_min': 8.0,
            'key_passes_per_game_min': 2.0,
            'assists_min': 5,
            'market_value_max': max_value
        }
    
    @staticmethod
    def get_young_prospects(max_value: float = None) -> Dict:
        """Jovens promessas"""
        return {
            'age_max': 21,
            'potential_rating_min': 7.5,
            'market_trend': 'rising',
            'market_value_max': max_value,
            'minutes_min': 500  # Pelo menos alguma experiência
        }
    
    @staticmethod
    def get_free_agents_opportunities() -> Dict:
        """Oportunidades em agentes livres"""
        return {
            'free_agents': True,
            'overall_rating_min': 7.0,
            'age_max': 32,
            'injury_prone': False
        }
    
    @staticmethod
    def get_loan_opportunities() -> Dict:
        """Oportunidades de empréstimo"""
        return {
            'loan_available': True,
            'age_max': 25,
            'potential_rating_min': 7.0
        }
    
    @staticmethod
    def get_position_specific_filters(position: str, tactical_system: str) -> Dict:
        """Filtros específicos por posição e sistema tático"""
        
        filters = {}
        
        if position == "Centre-Forward":
            if "counter" in tactical_system.lower() or "4-5-1" in tactical_system:
                filters.update({
                    'pace_min': 7.0,
                    'shooting_min': 7.0,
                    'physical_min': 6.5
                })
            elif "possession" in tactical_system.lower() or "4-3-3" in tactical_system:
                filters.update({
                    'shooting_min': 7.5,
                    'passing_min': 6.5,
                    'dribbling_min': 6.5
                })
        
        elif position == "Centre-Back":
            filters.update({
                'defending_min': 7.5,
                'height_min': 180,
                'aerial_duel_success_rate_min': 65.0
            })
            
            if "playing from back" in tactical_system.lower():
                filters['passing_min'] = 7.0
        
        elif position == "Central Midfield":
            filters.update({
                'passing_min': 7.0,
                'pass_accuracy_min': 85.0
            })
            
            if "defensive" in tactical_system.lower():
                filters['defending_min'] = 6.5
            elif "attacking" in tactical_system.lower():
                filters['assists_min'] = 3
        
        return filters