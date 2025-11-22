import spacy
from SPARQLWrapper import SPARQLWrapper, JSON
from typing import List, Dict, Any
import requests

class KnowledgeGraphService:
    def __init__(self):
        print("Loading spaCy model for entity recognition...")
        self.nlp = spacy.load("en_core_web_sm")
        self.wikidata_endpoint = "https://query.wikidata.org/sparql"
        print("Knowledge Graph Service initialized")
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract named entities from text using spaCy.
        
        Args:
            text: Input text
            
        Returns:
            List of entities with type and text
        """
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Filter out invalid entities
            entity_text = ent.text.strip()
            
            # Skip if:
            # - Too short (< 2 chars)
            # - All uppercase gibberish (likely OCR errors)
            # - Contains too many special characters
            if len(entity_text) < 2:
                continue
            
            # Skip if it's all caps and longer than 10 chars (likely OCR error)
            if entity_text.isupper() and len(entity_text) > 10:
                continue
            
            # Skip if more than 30% special characters
            special_char_count = sum(1 for c in entity_text if not c.isalnum() and not c.isspace())
            if special_char_count / len(entity_text) > 0.3:
                continue
            
            entities.append({
                "text": entity_text,
                "label": ent.label_,  # PERSON, ORG, GPE, LOC, etc.
                "start": ent.start_char,
                "end": ent.end_char
            })
        
        return entities
    
    def link_to_wikidata(self, entity_text: str, entity_type: str = None) -> Dict[str, Any]:
        """
        Link an entity to Wikidata using the Wikidata API.
        
        Args:
            entity_text: The entity text to search for
            entity_type: Optional entity type hint
            
        Returns:
            Wikidata entity information or None
        """
        try:
            # Use Wikidata search API
            search_url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbsearchentities",
                "format": "json",
                "language": "en",
                "search": entity_text,
                "limit": 1
            }
            
            response = requests.get(search_url, params=params, timeout=5)
            
            # Check if response is valid JSON
            if response.status_code != 200:
                return None
            
            try:
                data = response.json()
            except ValueError:
                print(f"Invalid JSON response for entity '{entity_text}'")
                return None
            
            if data.get("search") and len(data["search"]) > 0:
                result = data["search"][0]
                entity_id = result["id"]
                
                # Get additional info
                return {
                    "wikidata_id": entity_id,
                    "label": result.get("label", entity_text),
                    "description": result.get("description", ""),
                    "url": f"https://www.wikidata.org/wiki/{entity_id}"
                }
        except requests.exceptions.Timeout:
            print(f"Timeout linking entity '{entity_text}' to Wikidata")
        except requests.exceptions.RequestException as e:
            print(f"Request error linking entity '{entity_text}' to Wikidata: {e}")
        except Exception as e:
            print(f"Error linking entity '{entity_text}' to Wikidata: {e}")
        
        return None
    
    def get_entity_relations(self, wikidata_id: str) -> Dict[str, Any]:
        """
        Get relations for a Wikidata entity (e.g., location, type, etc.)
        
        Args:
            wikidata_id: Wikidata entity ID (e.g., Q243 for Eiffel Tower)
            
        Returns:
            Dictionary of relations
        """
        try:
            sparql = SPARQLWrapper(self.wikidata_endpoint)
            
            # Query for basic relations
            query = f"""
            SELECT ?propertyLabel ?valueLabel WHERE {{
              wd:{wikidata_id} ?property ?value.
              ?prop wikibase:directClaim ?property.
              
              # Filter for useful properties
              FILTER(?property IN (wdt:P31, wdt:P17, wdt:P131, wdt:P276, wdt:P361))
              
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
            }}
            LIMIT 10
            """
            
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            results = sparql.query().convert()
            
            relations = {}
            for result in results["results"]["bindings"]:
                prop = result["propertyLabel"]["value"]
                value = result["valueLabel"]["value"]
                relations[prop] = value
            
            return relations
        except Exception as e:
            print(f"Error getting relations for {wikidata_id}: {e}")
            return {}
    
    def enrich_text(self, text: str) -> Dict[str, Any]:
        """
        Extract entities from text and enrich with Wikidata information.
        
        Args:
            text: Input text
            
        Returns:
            Enriched entity information
        """
        entities = self.extract_entities(text)
        enriched = []
        
        for entity in entities:
            wikidata_info = self.link_to_wikidata(entity["text"], entity["label"])
            
            if wikidata_info:
                entity_data = {
                    **entity,
                    "wikidata": wikidata_info
                }
                
                # Get relations for important entities (landmarks, people, orgs)
                if entity["label"] in ["PERSON", "ORG", "GPE", "FAC"]:
                    relations = self.get_entity_relations(wikidata_info["wikidata_id"])
                    entity_data["relations"] = relations
                
                enriched.append(entity_data)
            else:
                enriched.append(entity)
        
        return {
            "text": text,
            "entities": enriched,
            "entity_count": len(enriched)
        }

if __name__ == "__main__":
    # Test the service
    kg = KnowledgeGraphService()
    result = kg.enrich_text("The Eiffel Tower is in Paris, France.")
    print(result)
