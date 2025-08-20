"""
🤖 Soccer Scout AI - Assistente Virtual Inteligente
Assistente virtual especializado em futebol com IA avançada
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import OpenAI
from config import settings

class IntelligentAssistant:
    """Assistente virtual especializado em análise de futebol"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.conversation_history = []
        self.context_memory = {}
        
        # Base de conhecimento especializada
        self.knowledge_base = {
            "tactical_systems": {
                "4-3-3": "Sistema ofensivo com pontas e meio equilibrado",
                "4-2-3-1": "Versátil com dupla de volantes",
                "3-5-2": "Três zagueiros com laterais subindo",
                "4-4-2": "Clássico com duas linhas de quatro"
            },
            "position_roles": {
                "Goalkeeper": "Último homem, distribuição e defesa",
                "Centre-Back": "Defesa central, marcação e jogo aéreo",
                "Full-Back": "Lateral com funções defensivas e ofensivas",
                "Defensive Midfield": "Volante, proteção e distribuição",
                "Central Midfield": "Meio-campo, criação e marcação",
                "Attacking Midfield": "Meia-atacante, criatividade e gols",
                "Winger": "Ponta, velocidade e cruzamentos",
                "Striker": "Centroavante, finalização e movimentação"
            },
            "leagues_ranking": {
                "Premier League": {"nivel": 1, "pais": "Inglaterra"},
                "La Liga": {"nivel": 1, "pais": "Espanha"},
                "Serie A": {"nivel": 1, "pais": "Itália"},
                "Bundesliga": {"nivel": 1, "pais": "Alemanha"},
                "Ligue 1": {"nivel": 1, "pais": "França"},
                "Brasileirão": {"nivel": 2, "pais": "Brasil"}
            }
        }
    
    async def process_advanced_query(self, query: str, context: Dict = None) -> Dict:
        """Processar consulta avançada com contexto e memória"""
        
        # Adicionar à conversa
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "context": context or {}
        })
        
        # Analisar tipo de consulta
        query_type = await self._classify_query(query)
        
        # Processar baseado no tipo
        if query_type == "tactical_analysis":
            return await self._handle_tactical_query(query, context)
        elif query_type == "player_comparison":
            return await self._handle_comparison_query(query, context)
        elif query_type == "market_analysis":
            return await self._handle_market_query(query, context)
        elif query_type == "transfer_advice":
            return await self._handle_transfer_query(query, context)
        elif query_type == "formation_optimization":
            return await self._handle_formation_query(query, context)
        else:
            return await self._handle_general_query(query, context)
    
    async def _classify_query(self, query: str) -> str:
        """Classificar tipo de consulta"""
        
        query_lower = query.lower()
        
        # Palavras-chave para classificação
        if any(word in query_lower for word in ["tática", "formação", "sistema", "4-3-3", "4-2-3-1"]):
            return "tactical_analysis"
        elif any(word in query_lower for word in ["comparar", "melhor entre", "diferença"]):
            return "player_comparison"
        elif any(word in query_lower for word in ["mercado", "valor", "preço", "transferência"]):
            return "market_analysis"
        elif any(word in query_lower for word in ["contratar", "comprar", "vender", "negociar"]):
            return "transfer_advice"
        elif any(word in query_lower for word in ["escalação", "time", "formação", "esquema"]):
            return "formation_optimization"
        else:
            return "general_query"
    
    async def _handle_tactical_query(self, query: str, context: Dict) -> Dict:
        """Lidar com consultas táticas"""
        
        if not self.client:
            return self._mock_tactical_response(query)
        
        prompt = f"""
        Analise esta consulta tática sobre futebol:
        
        **CONSULTA:** {query}
        **CONTEXTO:** {json.dumps(context, indent=2) if context else "Nenhum"}
        
        Como especialista tático, forneça uma resposta detalhada que inclua:
        1. Análise da situação tática
        2. Recomendações específicas
        3. Exemplos práticos
        4. Considerações estratégicas
        
        Responda de forma conversacional mas técnica, como um treinador experiente.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um treinador tático especialista com vasta experiência. Forneça análises detalhadas e práticas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            
            return {
                "type": "tactical_analysis",
                "response": response_text,
                "confidence": 90,
                "suggestions": [
                    "Quer ver análise de jogadores específicos para este sistema?",
                    "Posso mostrar exemplos de equipes que usam esta tática",
                    "Gostaria de comparar com outros sistemas táticos?"
                ]
            }
            
        except Exception as e:
            print(f"Error in tactical query: {str(e)}")
            return self._mock_tactical_response(query)
    
    def _mock_tactical_response(self, query: str) -> Dict:
        """Resposta tática mockada"""
        return {
            "type": "tactical_analysis",
            "response": "Análise tática: O sistema 4-3-3 oferece grande flexibilidade ofensiva com pontas largos que podem partir para dentro ou ficar na linha. O meio-campo em triângulo permite controle e criação, enquanto a defesa mantém-se compacta. Para implementar com sucesso, é fundamental que os laterais tenham condição física para subir e voltar constantemente.",
            "confidence": 85,
            "suggestions": [
                "Quer ver jogadores ideais para este sistema?",
                "Posso explicar as variações deste sistema",
                "Gostaria de comparar com outras formações?"
            ]
        }
    
    async def _handle_comparison_query(self, query: str, context: Dict) -> Dict:
        """Lidar com consultas de comparação"""
        
        if not self.client:
            return self._mock_comparison_response(query)
        
        prompt = f"""
        Responda a esta consulta de comparação sobre futebol:
        
        **CONSULTA:** {query}
        **DADOS DISPONÍVEIS:** {json.dumps(context, indent=2) if context else "Consulta geral"}
        
        Forneça uma comparação detalhada que inclua:
        1. Pontos fortes e fracos de cada opção
        2. Contextos onde cada um se destaca
        3. Recomendação baseada em critérios objetivos
        4. Análise custo-benefício se aplicável
        
        Seja imparcial e baseie-se em dados quando possível.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um analista imparcial e detalhista. Compare opções de forma objetiva e estruturada."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            return {
                "type": "comparison",
                "response": response.choices[0].message.content.strip(),
                "confidence": 88,
                "suggestions": [
                    "Quer ver mais detalhes sobre algum dos comparados?",
                    "Posso incluir outros jogadores na comparação",
                    "Gostaria de ver análise de adequação tática?"
                ]
            }
            
        except Exception as e:
            return self._mock_comparison_response(query)
    
    def _mock_comparison_response(self, query: str) -> Dict:
        """Resposta de comparação mockada"""
        return {
            "type": "comparison",
            "response": "Comparação: Ambos os jogadores possuem qualidades distintas. O Jogador A destaca-se pela velocidade e drible, sendo ideal para contra-ataques rápidos. O Jogador B tem melhor visão de jogo e passe, adequado para equipes que privilegiam a posse de bola. A escolha depende do estilo tático desejado e da necessidade específica da posição.",
            "confidence": 82,
            "suggestions": [
                "Quer análise tática específica?",
                "Posso mostrar estatísticas detalhadas",
                "Gostaria de ver jogadores similares?"
            ]
        }
    
    async def _handle_market_query(self, query: str, context: Dict) -> Dict:
        """Lidar com consultas de mercado"""
        
        if not self.client:
            return self._mock_market_response(query)
        
        prompt = f"""
        Analise esta consulta sobre mercado de transferências:
        
        **CONSULTA:** {query}
        **CONTEXTO:** {json.dumps(context, indent=2) if context else "Análise geral"}
        
        Como especialista em mercado esportivo, forneça:
        1. Análise atual do mercado
        2. Tendências de preços e valores
        3. Fatores que influenciam as negociações
        4. Previsões e oportunidades
        5. Riscos e cuidados a considerar
        
        Baseie-se em conhecimento do mercado atual e histórico.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um especialista em mercado de transferências com deep knowledge do mercado global."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return {
                "type": "market_analysis",
                "response": response.choices[0].message.content.strip(),
                "confidence": 85,
                "suggestions": [
                    "Quer análise de jogadores específicos?",
                    "Posso mostrar comparação de valores por liga",
                    "Gostaria de ver tendências por posição?"
                ]
            }
            
        except Exception as e:
            return self._mock_market_response(query)
    
    def _mock_market_response(self, query: str) -> Dict:
        """Resposta de mercado mockada"""
        return {
            "type": "market_analysis",
            "response": "Análise de mercado: O mercado atual mostra valorização de jogadores jovens com potencial de crescimento. Meias-atacantes criativos estão em alta demanda, especialmente aqueles que conseguem jogar em múltiplas posições. O Fair Play Financeiro continua influenciando as negociações, favorecendo clubes com gestão financeira equilibrada.",
            "confidence": 80,
            "suggestions": [
                "Quer ver oportunidades específicas?",
                "Posso analisar jogadores por faixa de preço",
                "Gostaria de tendências por idade?"
            ]
        }
    
    async def _handle_transfer_query(self, query: str, context: Dict) -> Dict:
        """Lidar com consultas de transferência"""
        
        if not self.client:
            return self._mock_transfer_response(query)
        
        prompt = f"""
        Analise esta consulta sobre transferências:
        
        **CONSULTA:** {query}
        **CONTEXTO:** {json.dumps(context, indent=2) if context else "Consulta geral"}
        
        Como diretor esportivo experiente, forneça:
        1. Análise da viabilidade da transferência
        2. Aspectos financeiros a considerar
        3. Timing ideal para a negociação
        4. Estratégias de negociação
        5. Alternativas e planos B
        
        Seja estratégico e considere todos os aspectos da negociação.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um diretor esportivo com vasta experiência em negociações complexas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            
            return {
                "type": "transfer_advice",
                "response": response.choices[0].message.content.strip(),
                "confidence": 87,
                "suggestions": [
                    "Quer análise de viabilidade específica?",
                    "Posso mostrar comparação com alternativas",
                    "Gostaria de estratégias de negociação?"
                ]
            }
            
        except Exception as e:
            return self._mock_transfer_response(query)
    
    def _mock_transfer_response(self, query: str) -> Dict:
        """Resposta de transferência mockada"""
        return {
            "type": "transfer_advice",
            "response": "Conselho de transferência: Para uma negociação bem-sucedida, é fundamental timing correto e abordagem estratégica. Considere iniciar conversas informais no meio da temporada, estruture uma proposta competitiva mas realista, e tenha sempre alternativas preparadas. A relação com agentes e conhecimento da situação contratual são cruciais.",
            "confidence": 83,
            "suggestions": [
                "Quer estratégias específicas de negociação?",
                "Posso analisar o timing ideal",
                "Gostaria de ver jogadores alternativos?"
            ]
        }
    
    async def _handle_formation_query(self, query: str, context: Dict) -> Dict:
        """Lidar com consultas de formação/escalação"""
        
        return {
            "type": "formation_optimization",
            "response": "Para otimizar a formação, analise primeiro as características individuais dos jogadores disponíveis, depois determine o sistema tático que melhor explora seus pontos fortes. Considere a compatibilidade entre os jogadores, equilíbrio defensivo-ofensivo, e adaptabilidade durante o jogo.",
            "confidence": 86,
            "suggestions": [
                "Quer análise de jogadores específicos?",
                "Posso mostrar sistemas táticos alternativos",
                "Gostaria de ver adequação de cada posição?"
            ]
        }
    
    async def _handle_general_query(self, query: str, context: Dict) -> Dict:
        """Lidar com consultas gerais"""
        
        if not self.client:
            return self._mock_general_response(query)
        
        prompt = f"""
        Responda a esta consulta sobre futebol:
        
        **PERGUNTA:** {query}
        **CONTEXTO:** {json.dumps(context, indent=2) if context else "Consulta geral"}
        
        Forneça uma resposta informativa e útil como especialista em futebol.
        Inclua detalhes relevantes, exemplos quando apropriado, e seja claro e objetivo.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "Você é um especialista em futebol com knowledge abrangente. Responda de forma clara e informativa."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=800
            )
            
            return {
                "type": "general_response",
                "response": response.choices[0].message.content.strip(),
                "confidence": 85,
                "suggestions": [
                    "Quer mais detalhes sobre algum aspecto?",
                    "Posso explicar conceitos relacionados",
                    "Gostaria de exemplos práticos?"
                ]
            }
            
        except Exception as e:
            return self._mock_general_response(query)
    
    def _mock_general_response(self, query: str) -> Dict:
        """Resposta geral mockada"""
        return {
            "type": "general_response",
            "response": "Resposta: O futebol moderno é caracterizado pela evolução tática constante, importância da versatilidade dos jogadores, e análise de dados cada vez mais sofisticada. As equipes buscam equilíbrio entre tradição e inovação, sempre adaptando-se às novas tendências e tecnologias disponíveis.",
            "confidence": 80,
            "suggestions": [
                "Quer saber sobre aspectos específicos?",
                "Posso explicar conceitos técnicos",
                "Gostaria de análises comparativas?"
            ]
        }
    
    async def get_conversation_summary(self) -> Dict:
        """Obter resumo da conversa atual"""
        
        if not self.conversation_history:
            return {"summary": "Nenhuma conversa anterior", "topics": [], "suggestions": []}
        
        recent_queries = [item["query"] for item in self.conversation_history[-5:]]
        
        return {
            "summary": f"Conversa com {len(self.conversation_history)} interações sobre futebol",
            "recent_topics": recent_queries,
            "main_interests": self._extract_main_interests(),
            "suggestions": [
                "Quer continuar explorando táticas?",
                "Posso sugerir jogadores baseado no que discutimos",
                "Gostaria de análise mais detalhada de algum tópico?"
            ]
        }
    
    def _extract_main_interests(self) -> List[str]:
        """Extrair principais interesses da conversa"""
        
        all_queries = " ".join([item["query"] for item in self.conversation_history])
        
        interests = []
        if "tática" in all_queries.lower():
            interests.append("Análise tática")
        if "jogador" in all_queries.lower():
            interests.append("Análise de jogadores")
        if "mercado" in all_queries.lower():
            interests.append("Mercado de transferências")
        if "formação" in all_queries.lower():
            interests.append("Formações e escalações")
        
        return interests or ["Futebol geral"]
    
    def clear_conversation(self):
        """Limpar histórico de conversa"""
        self.conversation_history = []
        self.context_memory = {}
    
    async def get_smart_suggestions(self, current_context: Dict = None) -> List[str]:
        """Obter sugestões inteligentes baseadas no contexto"""
        
        base_suggestions = [
            "Analise a adequação tática de um jogador específico",
            "Compare diferentes sistemas de jogo",
            "Avalie oportunidades no mercado de transferências",
            "Otimize a formação da sua equipe",
            "Analise tendências do futebol moderno"
        ]
        
        # Personalizar baseado no histórico
        if self.conversation_history:
            last_query = self.conversation_history[-1]["query"].lower()
            
            if "tática" in last_query:
                base_suggestions.insert(0, "Veja exemplos práticos desta tática em ação")
            elif "jogador" in last_query:
                base_suggestions.insert(0, "Compare com jogadores similares")
            elif "mercado" in last_query:
                base_suggestions.insert(0, "Analise tendências de preço para esta posição")
        
        return base_suggestions[:5]