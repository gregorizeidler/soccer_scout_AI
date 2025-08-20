"""
📋 Soccer Scout AI - Serviço de Shortlists e Dossiês
Sistema para criar listas, tags, prioridades e relatórios de scouting
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from database.models import get_db, Player
from services.enhanced_sportmonks_api import EnhancedSportmonksAPI
from services.openai_service import OpenAIService
import json
import uuid

class ShortlistService:
    """Gerenciador de shortlists e dossiês para clubes"""
    
    def __init__(self):
        self.sportmonks_api = EnhancedSportmonksAPI()
        self.openai_service = OpenAIService()
    
    async def create_shortlist(
        self, 
        club_id: str,
        name: str, 
        position: str,
        criteria: Dict[str, Any],
        user_id: str
    ) -> Dict:
        """Criar nova shortlist baseada em critérios"""
        
        shortlist_id = str(uuid.uuid4())
        
        # Buscar jogadores baseado nos critérios
        players = await self._find_players_for_criteria(criteria)
        
        # Criar shortlist
        shortlist = {
            'id': shortlist_id,
            'club_id': club_id,
            'name': name,
            'position': position,
            'criteria': criteria,
            'players': [],
            'created_by': user_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'active',
            'tags': [],
            'notes': ""
        }
        
        # Adicionar jogadores com status inicial
        for player in players:
            player_entry = {
                'player_id': player['id'],
                'player_data': player,
                'status': 'to_observe',  # to_observe, contacted, negotiating, signed, rejected
                'priority': 'medium',    # high, medium, low
                'fit_score': await self._calculate_fit_score(player, criteria),
                'risk_score': await self._calculate_risk_score(player),
                'value_score': await self._calculate_value_score(player),
                'scout_notes': "",
                'added_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            shortlist['players'].append(player_entry)
        
        # Salvar shortlist (em produção seria no banco)
        await self._save_shortlist(shortlist)
        
        return shortlist
    
    async def update_player_status(
        self, 
        shortlist_id: str, 
        player_id: int, 
        new_status: str,
        notes: str = "",
        priority: str = None
    ) -> bool:
        """Atualizar status de um jogador na shortlist"""
        
        shortlist = await self._get_shortlist(shortlist_id)
        if not shortlist:
            return False
        
        # Encontrar jogador
        for player_entry in shortlist['players']:
            if player_entry['player_id'] == player_id:
                player_entry['status'] = new_status
                player_entry['last_updated'] = datetime.now().isoformat()
                
                if notes:
                    player_entry['scout_notes'] = notes
                if priority:
                    player_entry['priority'] = priority
                
                break
        
        # Atualizar timestamp da shortlist
        shortlist['updated_at'] = datetime.now().isoformat()
        
        # Salvar mudanças
        await self._save_shortlist(shortlist)
        
        return True
    
    async def generate_player_dossier(self, player_id: int, club_context: Dict = None) -> Dict:
        """Gerar dossiê completo de um jogador"""
        
        # 1. Dados básicos
        player_profile = await self.sportmonks_api.get_player_complete_profile(player_id)
        
        # 2. Estatísticas da temporada
        season_stats = await self.sportmonks_api.get_player_season_statistics(player_id)
        
        # 3. Análise tática
        tactical_analysis = None
        if club_context and club_context.get('tactical_system'):
            from ai_services.tactical_analyzer import TacticalAnalyzer
            tactical_analyzer = TacticalAnalyzer()
            tactical_analysis = await tactical_analyzer.analyze_player_tactical_fit(
                player_profile, club_context['tactical_system']
            )
        
        # 4. Predição de performance
        from ai_services.performance_predictor import PerformancePredictor
        predictor = PerformancePredictor()
        performance_prediction = await predictor.predict_player_future_performance(
            player_profile, "12_months"
        )
        
        # 5. Histórico de transferências
        transfer_history = await self.sportmonks_api.get_player_transfer_history(player_id)
        
        # 6. Situação contratual
        contract_situation = await self.sportmonks_api.get_player_contract_situation(player_id)
        
        # 7. Histórico de lesões
        injury_timeline = await self.sportmonks_api.get_player_injury_timeline(player_id)
        
        # 8. Jogadores similares
        similar_players = await self.sportmonks_api.find_similar_players(player_id, 5)
        
        # 9. Análise de mercado
        market_analysis = await self._analyze_player_market_position(player_profile)
        
        # 10. Resumo executivo gerado por IA
        executive_summary = await self._generate_executive_summary(
            player_profile, season_stats, tactical_analysis, performance_prediction
        )
        
        # Compilar dossiê
        dossier = {
            'player_id': player_id,
            'generated_at': datetime.now().isoformat(),
            'player_profile': player_profile,
            'season_statistics': season_stats,
            'tactical_analysis': tactical_analysis,
            'performance_prediction': performance_prediction,
            'transfer_history': transfer_history,
            'contract_situation': contract_situation,
            'injury_timeline': injury_timeline,
            'similar_players': similar_players,
            'market_analysis': market_analysis,
            'executive_summary': executive_summary,
            'recommendation': self._generate_recommendation(
                player_profile, tactical_analysis, performance_prediction, market_analysis
            ),
            'risk_assessment': self._assess_overall_risk(
                injury_timeline, contract_situation, performance_prediction
            )
        }
        
        return dossier
    
    async def compare_shortlist_players(self, shortlist_id: str, player_ids: List[int]) -> Dict:
        """Comparar jogadores dentro de uma shortlist"""
        
        comparison_data = {
            'comparison_id': str(uuid.uuid4()),
            'shortlist_id': shortlist_id,
            'player_ids': player_ids,
            'generated_at': datetime.now().isoformat(),
            'players': [],
            'comparison_matrix': {},
            'recommendation': {}
        }
        
        # Buscar dados de cada jogador
        for player_id in player_ids:
            player_profile = await self.sportmonks_api.get_player_complete_profile(player_id)
            season_stats = await self.sportmonks_api.get_player_season_statistics(player_id)
            
            comparison_data['players'].append({
                'id': player_id,
                'profile': player_profile,
                'stats': season_stats
            })
        
        # Gerar matriz de comparação
        comparison_data['comparison_matrix'] = self._build_comparison_matrix(
            comparison_data['players']
        )
        
        # Gerar recomendação com IA
        comparison_data['recommendation'] = await self._generate_comparison_recommendation(
            comparison_data['players'], comparison_data['comparison_matrix']
        )
        
        return comparison_data
    
    async def export_shortlist_report(self, shortlist_id: str, format: str = 'json') -> Dict:
        """Exportar relatório da shortlist (JSON/PDF/CSV)"""
        
        shortlist = await self._get_shortlist(shortlist_id)
        if not shortlist:
            return {'error': 'Shortlist não encontrada'}
        
        # Gerar relatório detalhado
        report = {
            'shortlist': shortlist,
            'summary': self._generate_shortlist_summary(shortlist),
            'top_recommendations': self._get_top_recommendations(shortlist, 5),
            'status_breakdown': self._analyze_status_breakdown(shortlist),
            'export_metadata': {
                'generated_at': datetime.now().isoformat(),
                'format': format,
                'total_players': len(shortlist['players']),
                'club_id': shortlist['club_id']
            }
        }
        
        if format == 'pdf':
            # Em produção, geraria PDF usando reportlab ou similar
            report['pdf_url'] = f"/reports/shortlist_{shortlist_id}.pdf"
        elif format == 'csv':
            # Em produção, geraria CSV
            report['csv_data'] = self._convert_to_csv_format(shortlist)
        
        return report
    
    async def get_club_shortlists(self, club_id: str, status: str = 'all') -> List[Dict]:
        """Listar todas as shortlists de um clube"""
        
        # Em produção, buscaria do banco de dados
        shortlists = await self._get_club_shortlists_from_db(club_id)
        
        if status != 'all':
            shortlists = [s for s in shortlists if s.get('status') == status]
        
        # Adicionar estatísticas resumidas
        for shortlist in shortlists:
            shortlist['stats'] = self._calculate_shortlist_stats(shortlist)
        
        return shortlists
    
    # ========================================
    # 🛠️ MÉTODOS PRIVADOS
    # ========================================
    
    async def _find_players_for_criteria(self, criteria: Dict) -> List[Dict]:
        """Encontrar jogadores baseado nos critérios"""
        
        # Usar o sistema de filtros avançados
        from services.advanced_filters import AdvancedPlayerFilters
        filters = AdvancedPlayerFilters()
        
        return await filters.advanced_player_search(criteria)
    
    async def _calculate_fit_score(self, player: Dict, criteria: Dict) -> float:
        """Calcular score de adequação do jogador aos critérios"""
        
        score = 0.0
        total_criteria = 0
        
        # Verificar cada critério
        if 'position' in criteria:
            if player.get('position') == criteria['position']:
                score += 1.0
            total_criteria += 1
        
        if 'age_max' in criteria:
            player_age = player.get('age', 30)
            if player_age <= criteria['age_max']:
                score += 1.0
            total_criteria += 1
        
        if 'market_value_max' in criteria:
            player_value = player.get('market_value', 0)
            if player_value <= criteria['market_value_max']:
                score += 1.0
            total_criteria += 1
        
        # Adicionar outros critérios...
        
        return (score / max(total_criteria, 1)) * 10  # Score de 0-10
    
    async def _calculate_risk_score(self, player: Dict) -> float:
        """Calcular score de risco (0-10, onde 0 = baixo risco)"""
        
        risk_factors = 0
        
        # Idade (jogadores muito jovens ou velhos são mais arriscados)
        age = player.get('age', 25)
        if age < 18 or age > 32:
            risk_factors += 2
        elif age < 20 or age > 30:
            risk_factors += 1
        
        # Histórico de lesões
        if player.get('injury_prone', False):
            risk_factors += 2
        
        # Valor de mercado vs performance
        market_value = player.get('market_value', 0)
        overall_rating = player.get('overall_rating', 6)
        if market_value > 50 and overall_rating < 7.5:
            risk_factors += 1
        
        # Situação contratual
        if player.get('contract_end_date'):
            try:
                contract_end = datetime.fromisoformat(player['contract_end_date'].replace('Z', '+00:00'))
                months_left = (contract_end - datetime.now()).days // 30
                if months_left < 6:
                    risk_factors += 1
            except:
                pass
        
        return min(risk_factors * 1.5, 10)  # Máximo 10
    
    async def _calculate_value_score(self, player: Dict) -> float:
        """Calcular score de value for money (0-10)"""
        
        market_value = player.get('market_value', 0)
        overall_rating = player.get('overall_rating', 6)
        potential_rating = player.get('potential_rating', 6)
        age = player.get('age', 25)
        
        # Fórmula simplificada de value for money
        if market_value == 0:
            return 10.0  # Agente livre = excelente valor
        
        # Rating vs preço
        value_ratio = overall_rating / (market_value / 10)
        
        # Bônus por potencial
        potential_bonus = max(0, potential_rating - overall_rating) * 0.5
        
        # Bônus por idade (jogadores jovens têm mais valor futuro)
        age_bonus = max(0, (28 - age) * 0.1) if age < 28 else 0
        
        total_score = value_ratio + potential_bonus + age_bonus
        
        return min(total_score, 10)
    
    async def _analyze_player_market_position(self, player: Dict) -> Dict:
        """Analisar posição do jogador no mercado"""
        
        position = player.get('position', 'Unknown')
        age = player.get('age', 25)
        market_value = player.get('market_value', 0)
        
        # Buscar jogadores similares para comparação
        similar_players = await self.sportmonks_api.find_similar_players(
            player.get('id', 0), 20
        )
        
        # Calcular percentis
        similar_values = [p.get('market_value', 0) for p in similar_players]
        similar_ratings = [p.get('overall_rating', 6) for p in similar_players]
        
        value_percentile = self._calculate_percentile(market_value, similar_values)
        rating_percentile = self._calculate_percentile(
            player.get('overall_rating', 6), similar_ratings
        )
        
        return {
            'position_in_market': {
                'value_percentile': value_percentile,
                'rating_percentile': rating_percentile
            },
            'market_segment': self._determine_market_segment(market_value, position),
            'competition_level': len(similar_players),
            'price_trend': self._analyze_price_trend(player),
            'recommendation': self._generate_market_recommendation(
                value_percentile, rating_percentile, market_value
            )
        }
    
    def _calculate_percentile(self, value: float, comparison_list: List[float]) -> float:
        """Calcular percentil de um valor em uma lista"""
        if not comparison_list:
            return 50.0
        
        sorted_list = sorted(comparison_list)
        position = sum(1 for v in sorted_list if v < value)
        
        return (position / len(sorted_list)) * 100
    
    def _determine_market_segment(self, market_value: float, position: str) -> str:
        """Determinar segmento de mercado"""
        if market_value == 0:
            return "free_agent"
        elif market_value < 5:
            return "budget"
        elif market_value < 20:
            return "mid_tier"
        elif market_value < 50:
            return "premium"
        else:
            return "elite"
    
    def _analyze_price_trend(self, player: Dict) -> str:
        """Analisar tendência de preço"""
        age = player.get('age', 25)
        market_trend = player.get('market_trend', 'stable')
        
        if market_trend == 'rising':
            return 'increasing'
        elif market_trend == 'declining':
            return 'decreasing'
        elif age < 24:
            return 'likely_to_increase'
        elif age > 30:
            return 'likely_to_decrease'
        else:
            return 'stable'
    
    def _generate_market_recommendation(self, value_percentile: float, rating_percentile: float, market_value: float) -> str:
        """Gerar recomendação baseada na análise de mercado"""
        if rating_percentile > 70 and value_percentile < 30:
            return "Excellent value - underpriced for performance"
        elif rating_percentile > value_percentile + 20:
            return "Good value - outperforming market expectations"
        elif value_percentile > rating_percentile + 20:
            return "Overpriced - consider alternatives"
        else:
            return "Fair market value"
    
    async def _generate_executive_summary(self, player_profile: Dict, season_stats: Dict, tactical_analysis: Dict, performance_prediction: Dict) -> str:
        """Gerar resumo executivo usando IA"""
        
        try:
            prompt = f"""
            Gere um resumo executivo profissional para este jogador:
            
            PERFIL: {player_profile.get('name')} - {player_profile.get('position')} - {player_profile.get('age')} anos
            ESTATÍSTICAS: {season_stats.get('raw_stats', {})}
            ANÁLISE TÁTICA: {tactical_analysis}
            PREDIÇÃO: {performance_prediction}
            
            Formato: Máximo 200 palavras, tom profissional, focado em adequação para contratação.
            Inclua pontos fortes, pontos fracos e recomendação final.
            """
            
            summary = await self.openai_service.generate_explanation(
                prompt, [], {}
            )
            
            return summary
            
        except Exception as e:
            return f"Resumo automático não disponível. {player_profile.get('name')} é um {player_profile.get('position')} de {player_profile.get('age')} anos."
    
    def _generate_recommendation(self, player_profile: Dict, tactical_analysis: Dict, performance_prediction: Dict, market_analysis: Dict) -> str:
        """Gerar recomendação final"""
        
        overall_rating = player_profile.get('overall_rating', 6)
        market_recommendation = market_analysis.get('recommendation', '')
        
        if overall_rating >= 8.5 and 'excellent' in market_recommendation.lower():
            return "Strongly Recommended - High quality player at excellent value"
        elif overall_rating >= 7.5:
            return "Recommended - Good player with solid potential"
        elif overall_rating >= 6.5:
            return "Consider - Decent option depending on specific needs"
        else:
            return "Not Recommended - Below required quality standards"
    
    def _assess_overall_risk(self, injury_timeline: List, contract_situation: Dict, performance_prediction: Dict) -> Dict:
        """Avaliar risco geral"""
        
        risk_level = "Low"
        risk_factors = []
        
        # Analisar lesões
        if injury_timeline and len(injury_timeline) > 2:
            risk_level = "Medium"
            risk_factors.append("Multiple injury history")
        
        # Analisar contrato
        if contract_situation.get('months_remaining', 24) < 12:
            risk_level = "High"
            risk_factors.append("Contract expiring soon")
        
        # Analisar predição de performance
        prediction_trend = performance_prediction.get('trend', 'stable')
        if prediction_trend == 'declining':
            risk_level = "Medium" if risk_level == "Low" else "High"
            risk_factors.append("Declining performance trend")
        
        return {
            'level': risk_level,
            'factors': risk_factors,
            'mitigation_strategies': self._suggest_risk_mitigation(risk_factors)
        }
    
    def _suggest_risk_mitigation(self, risk_factors: List[str]) -> List[str]:
        """Sugerir estratégias de mitigação de risco"""
        strategies = []
        
        if "Multiple injury history" in risk_factors:
            strategies.append("Thorough medical examination before signing")
            strategies.append("Performance-based contract clauses")
        
        if "Contract expiring soon" in risk_factors:
            strategies.append("Negotiate pre-contract agreement")
            strategies.append("Move quickly to avoid competition")
        
        if "Declining performance trend" in risk_factors:
            strategies.append("Focus on role-specific performance metrics")
            strategies.append("Consider loan-to-buy option")
        
        return strategies
    
    def _build_comparison_matrix(self, players: List[Dict]) -> Dict:
        """Construir matriz de comparação"""
        
        matrix = {
            'technical': {},
            'physical': {},
            'market': {},
            'risk': {}
        }
        
        for player in players:
            player_id = player['id']
            profile = player['profile']
            
            matrix['technical'][player_id] = {
                'overall_rating': profile.get('overall_rating', 6),
                'passing': profile.get('passing', 6),
                'shooting': profile.get('shooting', 6),
                'dribbling': profile.get('dribbling', 6)
            }
            
            matrix['physical'][player_id] = {
                'pace': profile.get('pace', 6),
                'physical': profile.get('physical', 6),
                'height': profile.get('height', 175)
            }
            
            matrix['market'][player_id] = {
                'market_value': profile.get('market_value', 0),
                'age': profile.get('age', 25),
                'potential': profile.get('potential_rating', 6)
            }
        
        return matrix
    
    async def _generate_comparison_recommendation(self, players: List[Dict], matrix: Dict) -> str:
        """Gerar recomendação de comparação usando IA"""
        
        try:
            player_names = [p['profile'].get('name', f"Player {p['id']}") for p in players]
            
            prompt = f"""
            Compare estes jogadores e recomende o melhor para contratação:
            
            JOGADORES: {', '.join(player_names)}
            MATRIZ DE COMPARAÇÃO: {matrix}
            
            Considere: qualidade técnica, valor de mercado, potencial, idade, risco.
            Resposta: máximo 150 palavras, justificativa clara.
            """
            
            recommendation = await self.openai_service.generate_explanation(
                prompt, [], {}
            )
            
            return recommendation
            
        except Exception as e:
            return f"Recomendação baseada em análise automática dos {len(players)} jogadores comparados."
    
    # Mock methods para desenvolvimento (em produção seria banco de dados)
    async def _save_shortlist(self, shortlist: Dict) -> None:
        """Salvar shortlist (mock - em produção seria DB)"""
        pass
    
    async def _get_shortlist(self, shortlist_id: str) -> Optional[Dict]:
        """Buscar shortlist (mock)"""
        return None
    
    async def _get_club_shortlists_from_db(self, club_id: str) -> List[Dict]:
        """Buscar shortlists do clube (mock)"""
        return []
    
    def _generate_shortlist_summary(self, shortlist: Dict) -> Dict:
        """Gerar resumo da shortlist"""
        total_players = len(shortlist.get('players', []))
        
        status_counts = {}
        priority_counts = {}
        
        for player in shortlist.get('players', []):
            status = player.get('status', 'unknown')
            priority = player.get('priority', 'medium')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            'total_players': total_players,
            'status_breakdown': status_counts,
            'priority_breakdown': priority_counts,
            'avg_fit_score': sum(p.get('fit_score', 0) for p in shortlist.get('players', [])) / max(total_players, 1),
            'top_priority_count': priority_counts.get('high', 0)
        }
    
    def _get_top_recommendations(self, shortlist: Dict, limit: int) -> List[Dict]:
        """Obter top recomendações da shortlist"""
        players = shortlist.get('players', [])
        
        # Ordenar por fit_score
        sorted_players = sorted(players, key=lambda x: x.get('fit_score', 0), reverse=True)
        
        return sorted_players[:limit]
    
    def _analyze_status_breakdown(self, shortlist: Dict) -> Dict:
        """Analisar distribuição de status"""
        status_analysis = {
            'to_observe': {'count': 0, 'percentage': 0},
            'contacted': {'count': 0, 'percentage': 0},
            'negotiating': {'count': 0, 'percentage': 0},
            'signed': {'count': 0, 'percentage': 0},
            'rejected': {'count': 0, 'percentage': 0}
        }
        
        total = len(shortlist.get('players', []))
        
        for player in shortlist.get('players', []):
            status = player.get('status', 'to_observe')
            if status in status_analysis:
                status_analysis[status]['count'] += 1
        
        # Calcular percentuais
        for status, data in status_analysis.items():
            data['percentage'] = (data['count'] / max(total, 1)) * 100
        
        return status_analysis
    
    def _convert_to_csv_format(self, shortlist: Dict) -> str:
        """Converter shortlist para formato CSV"""
        # Implementação simplificada
        return "Player,Position,Age,Market Value,Status,Fit Score,Priority\n"
    
    def _calculate_shortlist_stats(self, shortlist: Dict) -> Dict:
        """Calcular estatísticas da shortlist"""
        return {
            'total_players': len(shortlist.get('players', [])),
            'last_updated': shortlist.get('updated_at'),
            'active_negotiations': len([
                p for p in shortlist.get('players', []) 
                if p.get('status') == 'negotiating'
            ])
        }