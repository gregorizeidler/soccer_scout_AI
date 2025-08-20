"""
📊 Soccer Scout AI - Gerador de Relatórios Automáticos
Sistema de geração automática de relatórios de scouting usando IA
"""

import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
from openai import OpenAI
from config import settings

class ReportGenerator:
    """Gerador automático de relatórios de scouting com IA"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        
    async def generate_player_scouting_report(self, player: Dict, detailed: bool = True) -> Dict:
        """Gerar relatório completo de scouting de um jogador"""
        
        if not self.client:
            return self._mock_scouting_report(player, detailed)
        
        prompt = f"""
        Gere um relatório de scouting profissional para:
        
        **JOGADOR:** {player.get('name')}
        **DADOS:**
        - Idade: {player.get('age')} anos
        - Posição: {player.get('position')}
        - Time atual: {player.get('team')}
        - Liga: {player.get('league')}
        - Valor de mercado: €{player.get('market_value', 0)}M
        - Nacionalidade: {player.get('nationality')}
        - Altura: {player.get('height', 'N/A')}cm
        - Pé preferido: {player.get('preferred_foot', 'N/A')}
        - Gols (temporada): {player.get('goals_season', 0)}
        - Assistências: {player.get('assists_season', 0)}
        - Jogos: {player.get('appearances', 0)}
        
        **NÍVEL DE DETALHAMENTO:** {'Completo' if detailed else 'Resumido'}
        
        Forneça um relatório estruturado em JSON:
        {{
            "executive_summary": "<resumo executivo de 2-3 linhas>",
            "player_profile": {{
                "playing_style": "<estilo de jogo>",
                "key_strengths": [<principais qualidades>],
                "areas_for_improvement": [<pontos a melhorar>],
                "unique_attributes": [<características únicas>]
            }},
            "technical_analysis": {{
                "ball_skills": "<avaliação das habilidades com bola>",
                "shooting": "<análise de finalização>",
                "passing": "<qualidade de passe>",
                "dribbling": "<capacidade de drible>",
                "first_touch": "<primeiro toque>",
                "weak_foot": "<uso do pé fraco>"
            }},
            "physical_attributes": {{
                "pace": "<velocidade>",
                "strength": "<força física>",
                "stamina": "<resistência>",
                "agility": "<agilidade>",
                "aerial_ability": "<jogo aéreo>",
                "injury_history": "<histórico de lesões>"
            }},
            "mental_attributes": {{
                "decision_making": "<tomada de decisão>",
                "composure": "<compostura>",
                "work_rate": "<intensidade>",
                "leadership": "<liderança>",
                "adaptability": "<adaptabilidade>"
            }},
            "tactical_fit": {{
                "preferred_systems": [<sistemas táticos ideais>],
                "position_versatility": "<versatilidade posicional>",
                "role_in_team": "<papel na equipe>",
                "tactical_discipline": "<disciplina tática>"
            }},
            "market_analysis": {{
                "current_value_assessment": "<avaliação do valor atual>",
                "transfer_feasibility": "<viabilidade de transferência>",
                "contract_situation": "<situação contratual>",
                "competition_for_signature": "<concorrência por assinatura>"
            }},
            "risk_assessment": {{
                "injury_risk": "<risco de lesão>",
                "adaptation_risk": "<risco de adaptação>",
                "performance_consistency": "<consistência de performance>",
                "age_related_decline": "<declínio relacionado à idade>"
            }},
            "recommendation": {{
                "overall_rating": "<nota de 1-10>",
                "transfer_recommendation": "<recomendação de contratação>",
                "ideal_transfer_value": "<valor ideal de transferência>",
                "priority_level": "<alta/média/baixa>",
                "timeline": "<prazo recomendado para abordagem>"
            }},
            "comparable_players": [<jogadores similares para comparação>],
            "scout_notes": [<observações específicas do scout>]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um scout profissional de futebol com 20 anos de experiência. Gere relatórios detalhados, objetivos e profissionais."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            report_data = json.loads(content)
            
            # Adicionar metadados
            report_data["metadata"] = {
                "generated_at": datetime.now().isoformat(),
                "scout_id": "AI_SYSTEM",
                "report_version": "1.0",
                "confidence_level": 85
            }
            
            return report_data
            
        except Exception as e:
            print(f"Error generating scouting report: {str(e)}")
            return self._mock_scouting_report(player, detailed)
    
    def _mock_scouting_report(self, player: Dict, detailed: bool) -> Dict:
        """Relatório de scouting mockado para desenvolvimento"""
        
        position = player.get('position', '')
        age = player.get('age', 25)
        
        return {
            "executive_summary": f"{player.get('name')} é um {position.lower()} de {age} anos com potencial interessante para clubes que buscam qualidade técnica e versatilidade tática.",
            "player_profile": {
                "playing_style": "Técnico e inteligente",
                "key_strengths": ["Visão de jogo", "Passe preciso", "Finalização"],
                "areas_for_improvement": ["Velocidade", "Jogo aéreo", "Consistência"],
                "unique_attributes": ["Ambidestro", "Liderança natural"]
            },
            "technical_analysis": {
                "ball_skills": "Excelente controle de bola e primeira recepção",
                "shooting": "Finalização precisa com ambos os pés",
                "passing": "Passe longo e curto de alta qualidade",
                "dribbling": "Drible efetivo em espaços reduzidos",
                "first_touch": "Primeiro toque refinado sob pressão",
                "weak_foot": "Uso competente do pé fraco"
            },
            "physical_attributes": {
                "pace": "Velocidade adequada para a posição",
                "strength": "Força física suficiente para disputas",
                "stamina": "Boa resistência durante 90 minutos",
                "agility": "Agilidade acima da média",
                "aerial_ability": "Jogo aéreo limitado",
                "injury_history": "Histórico de lesões limpo"
            },
            "mental_attributes": {
                "decision_making": "Tomada de decisão madura e eficaz",
                "composure": "Mantém calma em momentos decisivos",
                "work_rate": "Intensidade constante durante o jogo",
                "leadership": "Qualidades de liderança em desenvolvimento",
                "adaptability": "Adapta-se bem a diferentes sistemas"
            },
            "tactical_fit": {
                "preferred_systems": ["4-2-3-1", "4-3-3", "3-5-2"],
                "position_versatility": "Pode atuar em múltiplas posições",
                "role_in_team": "Peça-chave na criação e finalização",
                "tactical_discipline": "Boa disciplina tática e posicionamento"
            },
            "market_analysis": {
                "current_value_assessment": "Valor condizente com o mercado atual",
                "transfer_feasibility": "Transferência viável no próximo período",
                "contract_situation": "Contrato até 2026",
                "competition_for_signature": "Interesse de clubes europeus"
            },
            "risk_assessment": {
                "injury_risk": "Baixo risco baseado no histórico",
                "adaptation_risk": "Risco moderado de adaptação",
                "performance_consistency": "Performance consistente na temporada",
                "age_related_decline": "Ainda no auge da carreira"
            },
            "recommendation": {
                "overall_rating": "8.2/10",
                "transfer_recommendation": "Recomendado para contratação",
                "ideal_transfer_value": f"€{player.get('market_value', 30)}M",
                "priority_level": "alta" if age < 26 else "média",
                "timeline": "Janela de transferência de verão"
            },
            "comparable_players": ["Player A", "Player B", "Player C"],
            "scout_notes": [
                "Jogador com grande potencial de crescimento",
                "Adequado ao estilo de jogo da equipe",
                "Investimento com bom retorno esperado"
            ],
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "scout_id": "AI_SYSTEM",
                "report_version": "1.0",
                "confidence_level": 85
            }
        }
    
    async def generate_team_analysis_report(self, players: List[Dict], team_name: str = "Equipe Alvo") -> Dict:
        """Gerar relatório de análise de equipe completa"""
        
        if not self.client:
            return self._mock_team_analysis(players, team_name)
        
        # Preparar dados da equipe
        team_summary = self._prepare_team_summary(players)
        
        prompt = f"""
        Analise esta equipe de futebol e gere um relatório completo:
        
        **EQUIPE:** {team_name}
        **ELENCO:** {len(players)} jogadores
        
        **RESUMO DO ELENCO:**
        {team_summary}
        
        Forneça análise completa em JSON:
        {{
            "team_overview": {{
                "squad_size": <tamanho do elenco>,
                "average_age": <idade média>,
                "total_market_value": <valor total em milhões>,
                "nationality_distribution": [<distribuição por nacionalidade>],
                "experience_level": "<nível de experiência>"
            }},
            "positional_analysis": {{
                "goalkeeper": "<análise dos goleiros>",
                "defense": "<análise da defesa>",
                "midfield": "<análise do meio-campo>",
                "attack": "<análise do ataque>",
                "depth_assessment": "<avaliação da profundidade do elenco>"
            }},
            "team_strengths": [<pontos fortes da equipe>],
            "team_weaknesses": [<pontos fracos da equipe>],
            "tactical_flexibility": {{
                "formation_options": [<formações possíveis>],
                "style_variations": [<variações de estilo>],
                "player_versatility": "<versatilidade dos jogadores>"
            }},
            "transfer_priorities": {{
                "immediate_needs": [<necessidades imediatas>],
                "future_planning": [<planejamento futuro>],
                "budget_allocation": "<alocação de orçamento recomendada>"
            }},
            "competitive_assessment": {{
                "league_competitiveness": "<competitividade na liga>",
                "european_potential": "<potencial europeu>",
                "development_trajectory": "<trajetória de desenvolvimento>"
            }},
            "management_recommendations": [<recomendações para a gestão>],
            "overall_grade": "<nota geral A-F>"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um diretor esportivo experiente. Analise equipes de forma estratégica e abrangente."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Error generating team analysis: {str(e)}")
            return self._mock_team_analysis(players, team_name)
    
    def _prepare_team_summary(self, players: List[Dict]) -> str:
        """Preparar resumo da equipe para análise"""
        
        summary_lines = []
        for player in players[:15]:  # Limitar a 15 jogadores para o prompt
            line = f"- {player.get('name')} ({player.get('age')}a, {player.get('position')}, €{player.get('market_value', 0)}M)"
            summary_lines.append(line)
        
        return "\n".join(summary_lines)
    
    def _mock_team_analysis(self, players: List[Dict], team_name: str) -> Dict:
        """Análise de equipe mockada"""
        
        avg_age = sum(p.get('age', 25) for p in players) / len(players) if players else 25
        total_value = sum(p.get('market_value', 0) for p in players)
        
        return {
            "team_overview": {
                "squad_size": len(players),
                "average_age": round(avg_age, 1),
                "total_market_value": round(total_value, 1),
                "nationality_distribution": ["Brasil 30%", "Argentina 20%", "Europa 50%"],
                "experience_level": "Misto entre experiência e juventude"
            },
            "positional_analysis": {
                "goalkeeper": "Posição bem coberta com opções confiáveis",
                "defense": "Defesa sólida mas pode precisar de reforços",
                "midfield": "Meio-campo criativo e bem distribuído",
                "attack": "Ataque potente com boas opções",
                "depth_assessment": "Elenco com boa profundidade na maioria das posições"
            },
            "team_strengths": [
                "Criatividade no meio-campo",
                "Versatilidade tática",
                "Qualidade técnica individual",
                "Espírito de equipe"
            ],
            "team_weaknesses": [
                "Falta de velocidade nas laterais",
                "Dependência de jogadores-chave",
                "Inconsistência defensiva"
            ],
            "tactical_flexibility": {
                "formation_options": ["4-3-3", "4-2-3-1", "3-5-2"],
                "style_variations": ["Posse de bola", "Contra-ataque", "Pressão alta"],
                "player_versatility": "Vários jogadores podem atuar em múltiplas posições"
            },
            "transfer_priorities": {
                "immediate_needs": ["Lateral-direito", "Volante defensivo"],
                "future_planning": ["Sucessor do capitão", "Jovens talentos"],
                "budget_allocation": "60% reforços imediatos, 40% investimento futuro"
            },
            "competitive_assessment": {
                "league_competitiveness": "Competitivo para títulos nacionais",
                "european_potential": "Pode competir em competições europeias",
                "development_trajectory": "Equipe em desenvolvimento ascendente"
            },
            "management_recommendations": [
                "Focar no desenvolvimento dos jovens",
                "Melhorar a consistência defensiva",
                "Diversificar as opções táticas",
                "Investir em tecnologia de análise"
            ],
            "overall_grade": "B+"
        }
    
    async def generate_transfer_feasibility_report(self, player: Dict, target_club: str) -> Dict:
        """Gerar relatório de viabilidade de transferência"""
        
        if not self.client:
            return self._mock_transfer_feasibility(player, target_club)
        
        prompt = f"""
        Analise a viabilidade de transferência:
        
        **JOGADOR:** {player.get('name')}
        - Clube atual: {player.get('team')}
        - Valor: €{player.get('market_value', 0)}M
        - Idade: {player.get('age')} anos
        - Posição: {player.get('position')}
        
        **CLUBE INTERESSADO:** {target_club}
        
        Avalie a viabilidade em JSON:
        {{
            "feasibility_score": <0-100>,
            "financial_aspects": {{
                "transfer_fee_estimate": "<estimativa da taxa>",
                "salary_expectations": "<expectativas salariais>",
                "additional_costs": [<custos adicionais>],
                "financial_feasibility": "<alta/média/baixa>"
            }},
            "sporting_factors": {{
                "position_need": "<necessidade da posição>",
                "tactical_fit": "<adequação tática>",
                "squad_integration": "<integração ao elenco>",
                "playing_time_guarantee": "<garantia de tempo de jogo>"
            }},
            "negotiation_challenges": [<desafios na negociação>],
            "success_probability": "<alta/média/baixa>",
            "timeline_estimate": "<prazo estimado>",
            "alternative_strategies": [<estratégias alternativas>],
            "recommendation": "<recomendação final>"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um especialista em transferências de futebol. Analise viabilidade considerando todos os aspectos."},
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
            print(f"Error generating transfer feasibility: {str(e)}")
            return self._mock_transfer_feasibility(player, target_club)
    
    def _mock_transfer_feasibility(self, player: Dict, target_club: str) -> Dict:
        """Relatório de viabilidade mockado"""
        
        value = player.get('market_value', 30)
        feasibility = 75 if value < 50 else 60 if value < 100 else 40
        
        return {
            "feasibility_score": feasibility,
            "financial_aspects": {
                "transfer_fee_estimate": f"€{value}M - €{value + 10}M",
                "salary_expectations": f"€{value // 10}M por ano",
                "additional_costs": ["Comissão de agente", "Bônus por performance"],
                "financial_feasibility": "alta" if value < 50 else "média"
            },
            "sporting_factors": {
                "position_need": "Alta necessidade da posição",
                "tactical_fit": "Boa adequação ao sistema",
                "squad_integration": "Integração facilitada",
                "playing_time_guarantee": "Tempo de jogo assegurado"
            },
            "negotiation_challenges": [
                "Competição de outros clubes",
                "Resistência do clube atual",
                "Timing da negociação"
            ],
            "success_probability": "alta" if feasibility > 70 else "média",
            "timeline_estimate": "2-4 semanas",
            "alternative_strategies": [
                "Empréstimo com opção de compra",
                "Negociação em janela futura",
                "Jogador + dinheiro"
            ],
            "recommendation": "Prosseguir com negociação" if feasibility > 60 else "Considerar alternativas"
        }