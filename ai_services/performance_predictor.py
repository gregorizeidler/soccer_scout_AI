"""
🔮 Soccer Scout AI - Preditor de Performance
Sistema de machine learning para prever performance de jogadores e tendências de mercado
"""

import asyncio
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from openai import OpenAI
from config import settings

class PerformancePredictor:
    """Preditor de performance usando IA e análise estatística"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
    
    async def predict_player_future_performance(self, player: Dict, timeframe: str = "6_months") -> Dict:
        """Prever performance futura de um jogador"""
        
        if not self.client:
            return self._mock_performance_prediction(player, timeframe)
        
        # Calcular tendências atuais
        current_stats = self._extract_player_stats(player)
        
        prompt = f"""
        Analise e preveja a performance futura deste jogador:
        
        **JOGADOR:** {player.get('name')} ({player.get('age')} anos)
        **POSIÇÃO:** {player.get('position')}
        **ESTATÍSTICAS ATUAIS:**
        - Gols: {player.get('goals_season', 0)}
        - Assistências: {player.get('assists_season', 0)}
        - Jogos: {player.get('appearances', 0)}
        - Valor de mercado: €{player.get('market_value', 0)}M
        - Liga: {player.get('league', 'N/A')}
        
        **PERÍODO DE PREVISÃO:** {timeframe}
        
        Forneça uma análise preditiva em JSON:
        {{
            "performance_trend": "<crescente/estável/declinante>",
            "predicted_stats": {{
                "goals": <gols esperados>,
                "assists": <assistências esperadas>,
                "market_value_change": <variação % do valor>
            }},
            "peak_performance_period": "<quando atingirá o pico>",
            "risk_factors": [<fatores de risco>],
            "growth_potential": {{
                "score": <1-10>,
                "areas": [<áreas de melhoria>]
            }},
            "market_prediction": {{
                "value_trend": "<alta/estável/baixa>",
                "transfer_probability": "<alta/média/baixa>",
                "ideal_clubs": [<clubes ideais>]
            }},
            "injury_risk": {{
                "level": "<baixo/médio/alto>",
                "factors": [<fatores de risco>]
            }},
            "confidence_level": <0-100>
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um analista de performance esportiva especializado em futebol. Use análise estatística e tendências para fazer previsões precisas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1200
            )
            
            content = response.choices[0].message.content.strip()
            
            # Limpar markdown
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Error in performance prediction: {str(e)}")
            return self._mock_performance_prediction(player, timeframe)
    
    def _mock_performance_prediction(self, player: Dict, timeframe: str) -> Dict:
        """Predição mockada para desenvolvimento"""
        age = player.get('age', 25)
        current_goals = player.get('goals_season', 0)
        
        # Simular tendências baseadas na idade
        if age < 23:
            trend = "crescente"
            predicted_goals = int(current_goals * 1.3)
            market_change = 25
        elif age < 28:
            trend = "estável"
            predicted_goals = current_goals
            market_change = 5
        else:
            trend = "declinante"
            predicted_goals = max(0, int(current_goals * 0.8))
            market_change = -15
        
        return {
            "performance_trend": trend,
            "predicted_stats": {
                "goals": predicted_goals,
                "assists": int(player.get('assists_season', 0) * 1.1),
                "market_value_change": market_change
            },
            "peak_performance_period": "Próximos 2-3 anos" if age < 26 else "Já atingido",
            "risk_factors": ["Pressão por resultados", "Competição interna"],
            "growth_potential": {
                "score": max(10 - age//3, 5),
                "areas": ["Finalização", "Tomada de decisão"]
            },
            "market_prediction": {
                "value_trend": "alta" if trend == "crescente" else "estável",
                "transfer_probability": "média",
                "ideal_clubs": ["Premier League", "La Liga"]
            },
            "injury_risk": {
                "level": "baixo" if age < 28 else "médio",
                "factors": ["Carga de jogos", "Estilo de jogo"]
            },
            "confidence_level": 78
        }
    
    def _extract_player_stats(self, player: Dict) -> Dict:
        """Extrair estatísticas relevantes do jogador"""
        return {
            "goals_per_game": player.get('goals_season', 0) / max(player.get('appearances', 1), 1),
            "assists_per_game": player.get('assists_season', 0) / max(player.get('appearances', 1), 1),
            "market_value_millions": player.get('market_value', 0),
            "age": player.get('age', 0),
            "league_level": self._get_league_level(player.get('league', ''))
        }
    
    def _get_league_level(self, league: str) -> int:
        """Determinar nível da liga (1-5, sendo 1 o mais alto)"""
        top_leagues = ["Premier League", "La Liga", "Serie A", "Bundesliga", "Ligue 1"]
        if any(top in league for top in top_leagues):
            return 1
        return 3  # Nível médio por padrão
    
    async def compare_player_trajectories(self, players: List[Dict]) -> Dict:
        """Comparar trajetórias de múltiplos jogadores"""
        
        predictions = {}
        for player in players:
            prediction = await self.predict_player_future_performance(player)
            predictions[player['name']] = prediction
        
        # Análise comparativa
        comparison = await self._generate_trajectory_comparison(predictions)
        
        return {
            "player_predictions": predictions,
            "comparison_analysis": comparison,
            "investment_ranking": self._rank_investment_potential(predictions),
            "risk_assessment": self._assess_collective_risk(predictions)
        }
    
    def _rank_investment_potential(self, predictions: Dict) -> List[Dict]:
        """Ranquear potencial de investimento"""
        
        rankings = []
        for player_name, prediction in predictions.items():
            
            # Calcular score de investimento
            growth_score = prediction.get('growth_potential', {}).get('score', 5)
            market_trend = prediction.get('market_prediction', {}).get('value_trend', 'estável')
            confidence = prediction.get('confidence_level', 50)
            
            trend_multiplier = {"alta": 1.5, "estável": 1.0, "baixa": 0.5}.get(market_trend, 1.0)
            investment_score = (growth_score * trend_multiplier * confidence) / 100
            
            rankings.append({
                "player": player_name,
                "investment_score": round(investment_score, 2),
                "recommendation": "Comprar" if investment_score > 7 else "Monitorar" if investment_score > 5 else "Evitar"
            })
        
        return sorted(rankings, key=lambda x: x['investment_score'], reverse=True)
    
    def _assess_collective_risk(self, predictions: Dict) -> Dict:
        """Avaliar risco coletivo dos jogadores"""
        
        injury_risks = []
        performance_risks = []
        
        for prediction in predictions.values():
            injury_level = prediction.get('injury_risk', {}).get('level', 'médio')
            injury_risks.append(injury_level)
            
            trend = prediction.get('performance_trend', 'estável')
            performance_risks.append(trend)
        
        return {
            "injury_risk_distribution": {
                "baixo": injury_risks.count("baixo"),
                "médio": injury_risks.count("médio"),
                "alto": injury_risks.count("alto")
            },
            "performance_trends": {
                "crescente": performance_risks.count("crescente"),
                "estável": performance_risks.count("estável"),
                "declinante": performance_risks.count("declinante")
            },
            "overall_risk_level": self._calculate_overall_risk(injury_risks, performance_risks)
        }
    
    def _calculate_overall_risk(self, injury_risks: List[str], performance_risks: List[str]) -> str:
        """Calcular nível de risco geral"""
        
        risk_scores = []
        
        # Pontuação de risco de lesão
        injury_score = {
            "baixo": 1,
            "médio": 2,
            "alto": 3
        }
        
        performance_score = {
            "crescente": 1,
            "estável": 2,
            "declinante": 3
        }
        
        avg_injury = sum(injury_score.get(r, 2) for r in injury_risks) / len(injury_risks)
        avg_performance = sum(performance_score.get(r, 2) for r in performance_risks) / len(performance_risks)
        
        overall_avg = (avg_injury + avg_performance) / 2
        
        if overall_avg <= 1.5:
            return "baixo"
        elif overall_avg <= 2.5:
            return "médio"
        else:
            return "alto"
    
    async def _generate_trajectory_comparison(self, predictions: Dict) -> str:
        """Gerar análise comparativa das trajetórias"""
        
        if not self.client:
            return "Análise comparativa mostra diferentes trajetórias de crescimento entre os jogadores avaliados."
        
        # Preparar resumo dos dados
        summary = []
        for player, pred in predictions.items():
            trend = pred.get('performance_trend', 'estável')
            growth = pred.get('growth_potential', {}).get('score', 5)
            summary.append(f"{player}: {trend}, potencial {growth}/10")
        
        prompt = f"""
        Compare as trajetórias de crescimento destes jogadores:
        
        **ANÁLISES:**
        {chr(10).join(summary)}
        
        Forneça uma análise comparativa de 2-3 parágrafos destacando:
        1. Quais jogadores têm melhor potencial
        2. Diferentes perfis de risco/retorno
        3. Recomendações estratégicas
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um analista de investimentos esportivos. Forneça análises claras e estratégicas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating comparison: {str(e)}")
            return "Análise comparativa realizada considerando múltiplos fatores de performance e risco."
    
    async def predict_market_trends(self, position: str, league: str = None) -> Dict:
        """Prever tendências de mercado para uma posição específica"""
        
        if not self.client:
            return self._mock_market_trends(position, league)
        
        prompt = f"""
        Analise as tendências de mercado para jogadores:
        
        **POSIÇÃO:** {position}
        **LIGA:** {league or "Geral"}
        
        Forneça análise de mercado em JSON:
        {{
            "market_overview": "<visão geral do mercado>",
            "price_trends": {{
                "current_average": <valor médio atual em milhões>,
                "6_month_forecast": "<alta/estável/baixa>",
                "key_factors": [<fatores que influenciam preços>]
            }},
            "demand_analysis": {{
                "demand_level": "<alta/média/baixa>",
                "top_buyers": [<clubes mais ativos>],
                "market_gaps": [<lacunas no mercado>]
            }},
            "investment_opportunities": [<oportunidades específicas>],
            "risk_warnings": [<avisos de risco>],
            "seasonal_patterns": "<padrões sazonais de transferência>"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um analista de mercado de transferências de futebol. Forneça análises baseadas em dados e tendências."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Error predicting market trends: {str(e)}")
            return self._mock_market_trends(position, league)
    
    def _mock_market_trends(self, position: str, league: str) -> Dict:
        """Tendências de mercado mockadas"""
        
        # Simular baseado na posição
        if "Forward" in position or "Striker" in position:
            avg_value = 45
            demand = "alta"
            trend = "alta"
        elif "Midfield" in position:
            avg_value = 35
            demand = "média"
            trend = "estável"
        else:
            avg_value = 25
            demand = "média"
            trend = "estável"
        
        return {
            "market_overview": f"Mercado para {position} mostra {trend} demanda com valores em {trend}.",
            "price_trends": {
                "current_average": avg_value,
                "6_month_forecast": trend,
                "key_factors": ["Performance em competições", "Idade dos jogadores", "Necessidades dos clubes"]
            },
            "demand_analysis": {
                "demand_level": demand,
                "top_buyers": ["Premier League", "PSG", "Real Madrid"],
                "market_gaps": ["Jovens talentos", "Jogadores de experiência"]
            },
            "investment_opportunities": [
                "Jogadores sub-23 com potencial",
                "Mercados emergentes da América do Sul"
            ],
            "risk_warnings": [
                "Inflação de preços",
                "Regulamentações do Fair Play Financeiro"
            ],
            "seasonal_patterns": "Picos em Janeiro e Julho durante janelas de transferência"
        }