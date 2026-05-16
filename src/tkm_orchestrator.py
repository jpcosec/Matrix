import json
from unified_engine import UnifiedMatrixEngine

class TKMOrchestrator:
    """
    TKM Atom: Representacion_Flotante vs Omnirepresentacion.
    Orchestrates the LLM-driven ingestion of natural language facts into the engine.
    """
    def __init__(self, engine: UnifiedMatrixEngine):
        self.engine = engine

    def get_ingestion_prompt(self, text: str, context_name: str, mode: str = "M") -> str:
        """
        Generates the prompt for the LLM to process a new fact.
        mode: 'M' (Texto/Episódico) or 'G' (Grafo/Canónico).
        """
        mirror = self.engine.get_context_mirror(context_name)
        
        prompt = f"""
        TASK: Map the following natural language text into a Tractatus Knowledge Machine (TKM) logical space.
        MODE: {'EPISODIC (M) - Priority: Fidelity to the surface text' if mode == 'M' else 'CANONICAL (G) - Priority: Structural Integrity and Non-redundancy'}
        
        CURRENT CONTEXT:
        {mirror}
        
        INPUT TEXT: "{text}"
        
        INSTRUCTIONS:
        1. Identify the Subject (X) and the Property/Relation (Y).
        2. Choose one of the following ACTIONS:
           - MAP_IDENTITY: The subject/property exists exactly in the current axes.
           - MAP_SEMANTIC: The subject/property is semantically equivalent (synonym) to an existing symbol.
           - EXPAND_SCHEMA: The subject/property is new and requires adding a new axis or context.
        3. Respond ONLY with a JSON object in this format:
        {{
            "action": "MAP_IDENTITY | MAP_SEMANTIC | EXPAND_SCHEMA",
            "subject": {{
                "id": "existing_symbol_id or new_id",
                "is_new": bool,
                "sign": "the text used in the input"
            }},
            "property": {{
                "id": "existing_symbol_id or new_id",
                "is_new": bool,
                "sign": "the text used in the input",
                "rationale": "Why this axis?"
            }},
            "value": true | false
        }}
        """
        return prompt

    def process_llm_response(self, response_json: str, context_name: str, mode: str = "M"):
        """
        Parses the LLM response and updates the engine.
        """
        if isinstance(response_json, str):
            data = json.loads(response_json)
        else:
            data = response_json

        action = data["action"]
        subject = data["subject"]
        prop = data["property"]
        value = data["value"]

        # 1. Update Registry for Signs
        if subject.get("sign"):
            self.engine.registry.add_sign(subject["id"], subject["sign"])
        if prop.get("sign"):
            self.engine.registry.add_sign(prop["id"], prop["sign"])
        
        # 2. Update Engine Structure and Facts
        if subject.get("is_new"):
            self.engine.add_object(context_name, subject["id"])
        if prop.get("is_new"):
            self.engine.add_dimension(context_name, prop["id"], meta={"rationale": prop.get("rationale")})
            
        self.engine.set_fact(context_name, subject["id"], prop["id"], value, mode=mode)

