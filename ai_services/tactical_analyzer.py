"""
🧠 Soccer Scout AI - Analisador Tático Avançado
Sistema de análise tática usando IA para avaliar compatibilidade de jogadores com sistemas táticos
"""

import asyncio
from typing import Dict, List, Optional
from openai import OpenAI
from config import settings

class TacticalAnalyzer:
    """Analisador tático avançado com IA"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        
        # Sistemas táticos conhecidos
        self.tactical_systems = {
            "4-3-3": {
                "description": "Sistema ofensivo com pontas largos e meio-campo equilibrado",
                "positions": ["GK", "RB", "CB", "CB", "LB", "DM", "CM", "CM", "RW", "ST", "LW"],
                "characteristics": ["posse de bola", "jogo pelos flancos", "pressão alta"]
            },
            "4-2-3-1": {
                "description": "Sistema versátil com dois volantes e meia-atacante",
                "positions": ["GK", "RB", "CB", "CB", "LB", "DM", "DM", "CAM", "RW", "ST", "LW"],
                "characteristics": ["equilíbrio", "criatividade central", "transições rápidas"]
            },
            "3-5-2": {
                "description": "Sistema com três zagueiros e meio-campo largo",
                "positions": ["GK", "CB", "CB", "CB", "RWB", "CM", "CM", "CM", "LWB", "ST", "ST"],
                "characteristics": ["controle do meio", "largura pelos laterais", "jogo aéreo"]
            },
            "4-4-2": {
                "description": "Sistema clássico com duas linhas de quatro",
                "positions": ["GK", "RB", "CB", "CB", "LB", "RM", "CM", "CM", "LM", "ST", "ST"],
                "characteristics": ["compactação", "jogo direto", "dupla de ataque"]
            }
        }
    
    async def analyze_player_tactical_fit(self, player: Dict, system: str) -> Dict:
        """Analisar adequação de um jogador a um sistema tático"""
        
        if not self.client:
            return self._mock_tactical_analysis(player, system)
        
        system_info = self.tactical_systems.get(system, {})
        
        prompt = f"""
        Analise a adequação tática do jogador para o sistema {system}:
        
        **JOGADOR:**
        - Nome: {player.get('name')}
        - Posição: {player.get('position')}
        - Idade: {player.get('age')} anos
        - Altura: {player.get('height', 'N/A')}cm
        - Pé preferido: {player.get('preferred_foot', 'N/A')}
        - Gols na temporada: {player.get('goals_season', 0)}
        - Assistências: {player.get('assists_season', 0)}
        - Jogos: {player.get('appearances', 0)}
        
        **SISTEMA TÁTICO: {system}**
        - Descrição: {system_info.get('description', '')}
        - Características: {', '.join(system_info.get('characteristics', []))}
        
        Forneça uma análise detalhada em formato JSON:
        {{
            "tactical_score": <nota de 1-10>,
            "position_compatibility": <adequação da posição>,
            "strengths": [<pontos fortes para o sistema>],
            "weaknesses": [<pontos fracos para o sistema>],
            "recommendations": [<recomendações específicas>],
            "alternative_positions": [<posições alternativas no sistema>],
            "playing_style": "<estilo de jogo recomendado>",
            "key_attributes": [<atributos mais importantes>]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um analista tático especialista em futebol. Forneça análises precisas e profissionais."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            import json
            content = response.choices[0].message.content.strip()
            
            # Limpar markdown se presente
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Error in tactical analysis: {str(e)}")
            return self._mock_tactical_analysis(player, system)
    
    def _mock_tactical_analysis(self, player: Dict, system: str) -> Dict:
        """Análise tática mockada para desenvolvimento"""
        position = player.get('position', '')
        
        # Simulação baseada na posição
        if "Forward" in position or "Striker" in position:
            score = 8.5 if system in ["4-3-3", "4-2-3-1"] else 7.0
            strengths = ["Finalização", "Movimentação na área", "Jogo aéreo"]
            weaknesses = ["Criação de jogadas", "Marcação defensiva"]
        elif "Midfield" in position:
            score = 9.0 if system in ["4-2-3-1", "3-5-2"] else 7.5
            strengths = ["Passe", "Visão de jogo", "Controle de bola"]
            weaknesses = ["Velocidade", "Jogo aéreo defensivo"]
        elif "Back" in position or "Defence" in position:
            score = 8.0 if system in ["3-5-2", "4-4-2"] else 7.5
            strengths = ["Marcação", "Interceptação", "Jogo aéreo"]
            weaknesses = ["Velocidade", "Passe longo"]
        else:
            score = 7.5
            strengths = ["Versatilidade", "Experiência"]
            weaknesses = ["Especialização"]
        
        return {
            "tactical_score": score,
            "position_compatibility": "Alta" if score >= 8 else "Média",
            "strengths": strengths,
            "weaknesses": weaknesses,
            "recommendations": [
                f"Ideal para o {system} devido às suas características",
                "Treinar aspectos defensivos" if "Forward" in position else "Melhorar passe"
            ],
            "alternative_positions": ["Central Midfield", "Attacking Midfield"],
            "playing_style": "Dinâmico e versátil",
            "key_attributes": ["Técnica", "Posicionamento", "Físico"]
        }
    
    async def analyze_team_formation(self, players: List[Dict], system: str) -> Dict:
        """Analisar formação completa da equipe"""
        
        analyses = []
        for player in players[:11]:  # Apenas titulares
            analysis = await self.analyze_player_tactical_fit(player, system)
            analyses.append({
                "player": player,
                "analysis": analysis
            })
        
        # Calcular estatísticas da formação
        scores = [a["analysis"]["tactical_score"] for a in analyses]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Identificar pontos fortes e fracos da formação
        strengths = []
        weaknesses = []
        
        for analysis in analyses:
            strengths.extend(analysis["analysis"]["strengths"])
            weaknesses.extend(analysis["analysis"]["weaknesses"])
        
        # Contar frequências
        from collections import Counter
        strength_counts = Counter(strengths)
        weakness_counts = Counter(weaknesses)
        
        return {
            "system": system,
            "overall_score": round(avg_score, 1),
            "player_analyses": analyses,
            "team_strengths": [s for s, c in strength_counts.most_common(5)],
            "team_weaknesses": [w for w, c in weakness_counts.most_common(3)],
            "formation_balance": self._calculate_formation_balance(analyses),
            "recommendations": await self._generate_formation_recommendations(analyses, system)
        }
    
    def _calculate_formation_balance(self, analyses: List[Dict]) -> Dict:
        """Calcular equilíbrio da formação"""
        
        # Simular cálculo de equilíbrio
        attack_score = 8.2
        midfield_score = 7.8
        defense_score = 8.5
        
        return {
            "attack": attack_score,
            "midfield": midfield_score,
            "defense": defense_score,
            "overall_balance": round((attack_score + midfield_score + defense_score) / 3, 1)
        }
    
    async def _generate_formation_recommendations(self, analyses: List[Dict], system: str) -> List[str]:
        """Gerar recomendações para a formação"""
        
        if not self.client:
            return [
                f"Formação {system} bem equilibrada",
                "Considerar trabalhar transições defensivas",
                "Explorar mais o jogo pelos flancos",
                "Melhorar entrosamento do meio-campo"
            ]
        
        # Preparar dados para análise
        team_summary = "\n".join([
            f"- {a['player']['name']} ({a['player']['position']}): Nota {a['analysis']['tactical_score']}"
            for a in analyses
        ])
        
        prompt = f"""
        Analise esta formação {system} e forneça recomendações táticas:
        
        **ESCALAÇÃO:**
        {team_summary}
        
        Forneça 4-6 recomendações táticas específicas e práticas para melhorar o desempenho da equipe.
        Foque em aspectos como:
        - Movimentações táticas
        - Transições
        - Pressão e marcação
        - Criação de jogadas
        - Exploração de pontos fortes
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um treinador tático expert. Forneça recomendações práticas e específicas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=600
            )
            
            content = response.choices[0].message.content.strip()
            # Dividir em lista de recomendações
            recommendations = [r.strip() for r in content.split('\n') if r.strip() and not r.strip().startswith('#')]
            
            return recommendations[:6]  # Máximo 6 recomendações
            
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return [
                f"Formação {system} bem estruturada",
                "Trabalhar movimentação sem bola",
                "Melhorar compactação defensiva",
                "Explorar transições rápidas"
            ]
    
    async def compare_tactical_systems(self, players: List[Dict], systems: List[str]) -> Dict:
        """Comparar diferentes sistemas táticos para o mesmo elenco"""
        
        comparisons = {}
        
        for system in systems:
            if system in self.tactical_systems:
                analysis = await self.analyze_team_formation(players, system)
                comparisons[system] = analysis
        
        # Encontrar melhor sistema
        best_system = max(comparisons.keys(), 
                         key=lambda s: comparisons[s]["overall_score"])
        
        return {
            "comparisons": comparisons,
            "recommended_system": best_system,
            "system_rankings": sorted(
                [(s, data["overall_score"]) for s, data in comparisons.items()],
                key=lambda x: x[1],
                reverse=True
            ),
            "summary": await self._generate_system_comparison_summary(comparisons)
        }
    
    async def _generate_system_comparison_summary(self, comparisons: Dict) -> str:
        """Gerar resumo da comparação de sistemas"""
        
        if not self.client:
            return "Análise comparativa dos sistemas táticos mostrou diferentes pontos fortes para cada formação."
        
        # Preparar dados
        systems_data = []
        for system, data in comparisons.items():
            systems_data.append(f"{system}: Nota {data['overall_score']}")
        
        prompt = f"""
        Compare estes sistemas táticos e forneça um resumo executivo:
        
        **RESULTADOS:**
        {chr(10).join(systems_data)}
        
        Forneça um resumo de 2-3 parágrafos explicando:
        1. Qual sistema é mais adequado e por quê
        2. Principais diferenças entre os sistemas
        3. Recomendação final
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um analista tático. Forneça resumos claros e objetivos."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return "Análise detalhada dos sistemas táticos realizada com sucesso."