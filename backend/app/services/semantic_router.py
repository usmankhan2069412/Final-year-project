import numpy as np
from typing import Optional, Dict
from app.services.embedding import embedding_service
import logging

logger = logging.getLogger(__name__)

class SemanticRouter:
    """
    A lightweight, embedding-based semantic router that classifies user intents
    by comparing cosine similarity of the query against predefined utterances.
    """
    ROUTES = {
        "AGENT_HANDOFF": [
            "talk to human",
            "speak with an agent",
            "connect to a person",
            "i need human support",
            "human representative",
            "talk to support team",
            "transfer to human",
            "mujhe insan se baat karni hai",
            "agent se connect karo",
            "customer care se baat karni hai",
            "human se baat karao",
            "help desk",
            "i want to talk to an admin",
            "can i speak to a real person",
            "representative please"
        ],
        "FRUSTRATION": [
            "this is useless",
            "you are not helping",
            "bakwas",
            "fazool",
            "you don't understand",
            "this bot is stupid",
            "i am angry",
            "terrible service",
            "stop replying like a bot",
            "nonsense"
        ],
        "CONVERSATIONAL": [
            "hi",
            "hello",
            "hey",
            "good morning",
            "good evening",
            "how are you",
            "thanks",
            "thank you",
            "bye",
            "goodbye",
            "assalam o alaikum",
            "salam",
            "kya haal hai",
            "shukriya",
            "allah hafiz",
            "ok",
            "okay"
        ]
    }
    
    _encoded_routes: Dict[str, np.ndarray] = {}
    _initialized = False

    @classmethod
    def _initialize(cls):
        if cls._initialized:
            return
            
        logger.info("Initializing Semantic Router embeddings...")
        try:
            for intent, utterances in cls.ROUTES.items():
                vectors = embedding_service.encode(utterances)
                if vectors.size > 0:
                    # Normalize vectors for cosine similarity (dot product)
                    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                    norms[norms == 0] = 1e-10
                    normalized_vectors = vectors / norms
                    cls._encoded_routes[intent] = normalized_vectors
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Semantic Router: {e}")

    @classmethod
    def classify(cls, message: str, threshold: float = 0.82) -> Optional[str]:
        # Fast short-circuit for exact generic matches
        msg_lower = message.lower().strip()
        words = msg_lower.split()
        if len(words) <= 2 and (msg_lower in cls.ROUTES["CONVERSATIONAL"] or any(w in cls.ROUTES["CONVERSATIONAL"] for w in words)):
            return "CONVERSATIONAL"
            
        if not cls._initialized:
            cls._initialize()
            
        if not cls._initialized or not cls._encoded_routes:
            return None # Fallback if initialization fails
            
        try:
            # Encode user message
            query_vector = embedding_service.encode([message])[0]
            query_norm = np.linalg.norm(query_vector)
            if query_norm == 0:
                return None
            
            normalized_query = query_vector / query_norm
            
            best_intent = None
            best_score = -1.0
            
            for intent, route_vectors in cls._encoded_routes.items():
                # Compute cosine similarities
                similarities = np.dot(route_vectors, normalized_query)
                max_sim = np.max(similarities)
                
                if max_sim > best_score:
                    best_score = max_sim
                    best_intent = intent
            
            if best_score >= threshold:
                logger.info(f"Semantic Router matched '{best_intent}' with score {best_score:.3f}")
                return best_intent
            else:
                logger.info(f"Semantic Router fallback. Highest score was {best_score:.3f} for '{best_intent}'")
                return None
                
        except Exception as e:
            logger.error(f"Semantic classification error: {e}")
            return None
