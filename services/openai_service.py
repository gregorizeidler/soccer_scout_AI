from openai import OpenAI
import json
from typing import Dict, List
from config import settings

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.OPENAI_MODEL
    
    async def parse_scout_query(self, query: str) -> Dict:
        """
        Analisar consulta em linguagem natural e extrair critérios de busca
        
        Exemplo de input: "Quero um meia direita até 50 milhões que fez mais de 10 gols"
        
        Output esperado:
        {
            "position": "Right Midfield",
            "max_value": 50.0,
            "min_goals": 10,
            "league": null,
            "age_max": null,
            "age_min": null
        }
        """
        
        system_prompt = """
        Você é um especialista em análise de consultas de scouting de futebol. 
        Sua tarefa é extrair critérios específicos de busca de jogadores a partir de consultas em linguagem natural.
        
        Posições possíveis:
        - Goalkeeper (goleiro)
        - Centre-Back (zagueiro central)
        - Left-Back (lateral esquerdo)
        - Right-Back (lateral direito)
        - Defensive Midfield (volante)
        - Central Midfield (meio-campo central)
        - Attacking Midfield (meia-atacante)
        - Left Winger (ponta esquerda)
        - Right Winger (ponta direita)
        - Centre-Forward (centroavante)
        - Second Striker (segundo atacante)
        
        Ligas principais:
        - Premier League (Inglaterra)
        - La Liga (Espanha)
        - Serie A (Itália)
        - Bundesliga (Alemanha)
        - Ligue 1 (França)
        - Brasileirão (Brasil)
        
        Responda APENAS com um objeto JSON válido contendo os critérios extraídos.
        Use null para critérios não mencionados.
        
        Exemplo de resposta:
        {
            "position": "Right Winger",
            "max_value": 50.0,
            "min_goals": 10,
            "min_assists": null,
            "league": "Premier League",
            "age_max": 25,
            "age_min": null,
            "nationality": null,
            "min_appearances": null
        }
        """
        
        user_prompt = f"Consulta: {query}"
        
        if not self.client:
            # Mock response para desenvolvimento sem API key
            return self._mock_parse_query(query)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remover markdown se presente
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"Error parsing query with OpenAI: {str(e)}")
            return self._mock_parse_query(query)
    
    def _mock_parse_query(self, query: str) -> Dict:
        """Parser simples para desenvolvimento sem API OpenAI"""
        query_lower = query.lower()
        criteria = {
            "position": None,
            "max_value": None,
            "min_goals": None,
            "min_assists": None,
            "league": None,
            "age_max": None,
            "age_min": None,
            "nationality": None,
            "min_appearances": None
        }
        
        # Extrair posição
        position_mapping = {
            "meia": "Central Midfield",
            "meio": "Central Midfield",
            "volante": "Defensive Midfield",
            "zagueiro": "Centre-Back",
            "lateral": "Left-Back",
            "atacante": "Centre-Forward",
            "centroavante": "Centre-Forward",
            "ponta": "Right Winger",
            "goleiro": "Goalkeeper"
        }
        
        for pt_pos, en_pos in position_mapping.items():
            if pt_pos in query_lower:
                criteria["position"] = en_pos
                break
        
        # Específicos para meia direita/esquerda
        if "meia direita" in query_lower or "meio direita" in query_lower:
            criteria["position"] = "Right Winger"
        elif "meia esquerda" in query_lower or "meio esquerda" in query_lower:
            criteria["position"] = "Left Winger"
        
        # Extrair valor máximo
        import re
        value_match = re.search(r'até (\d+)\s*(milhões?|milhão|mi)', query_lower)
        if value_match:
            criteria["max_value"] = float(value_match.group(1))
        
        # Extrair gols mínimos
        goals_match = re.search(r'(\d+)\+?\s*gols?', query_lower)
        if goals_match:
            criteria["min_goals"] = int(goals_match.group(1))
        
        # Extrair idade
        age_match = re.search(r'até (\d+) anos?', query_lower)
        if age_match:
            criteria["age_max"] = int(age_match.group(1))
            
        young_keywords = ["jovem", "jovens", "novo", "promissor"]
        if any(keyword in query_lower for keyword in young_keywords):
            criteria["age_max"] = 23
        
        # Extrair liga
        league_mapping = {
            "premier league": "Premier League",
            "premier": "Premier League",
            "la liga": "La Liga",
            "espanha": "La Liga",
            "serie a": "Serie A",
            "itália": "Serie A",
            "bundesliga": "Bundesliga",
            "alemanha": "Bundesliga",
            "ligue 1": "Ligue 1",
            "frança": "Ligue 1",
            "brasileirão": "Brasileirão",
            "brasil": "Brasileirão"
        }
        
        for league_key, league_name in league_mapping.items():
            if league_key in query_lower:
                criteria["league"] = league_name
                break
        
        return criteria
    
    async def generate_explanation(self, query: str, players: List[Dict], criteria: Dict) -> str:
        """Gerar explicação detalhada dos resultados da busca"""
        
        if not self.client:
            return self._mock_explanation(query, players, criteria)
        
        system_prompt = """
        Você é um especialista em análise de scouting de futebol. 
        Explique de forma clara e profissional os resultados de uma busca de jogadores,
        destacando como cada jogador atende aos critérios solicitados.
        
        Seja específico sobre estatísticas, valores e características dos jogadores.
        Use linguagem técnica mas acessível para dirigentes de clubes.
        """
        
        user_prompt = f"""
        Consulta original: {query}
        
        Critérios extraídos: {json.dumps(criteria, indent=2)}
        
        Jogadores encontrados: {json.dumps(players[:3], indent=2)}
        
        Explique os resultados da busca e por que estes jogadores atendem aos critérios.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating explanation: {str(e)}")
            return self._mock_explanation(query, players, criteria)
    
    def _mock_explanation(self, query: str, players: List[Dict], criteria: Dict) -> str:
        """Explicação simples para desenvolvimento"""
        count = len(players)
        
        explanation = f"Encontrei {count} jogador(es) que atendem aos seus critérios:\n\n"
        
        for i, player in enumerate(players[:3], 1):
            explanation += f"{i}. **{player['name']}** ({player['age']} anos)\n"
            explanation += f"   - Posição: {player['position']}\n"
            explanation += f"   - Time: {player['team']}\n"
            explanation += f"   - Valor: €{player['market_value']}M\n"
            explanation += f"   - Gols na temporada: {player['goals_season']}\n"
            explanation += f"   - Liga: {player['league']}\n\n"
        
        if criteria.get("max_value"):
            explanation += f"Todos os jogadores estão dentro do orçamento de €{criteria['max_value']}M.\n"
        
        if criteria.get("min_goals"):
            explanation += f"Todos fizeram pelo menos {criteria['min_goals']} gols na temporada.\n"
        
        return explanation