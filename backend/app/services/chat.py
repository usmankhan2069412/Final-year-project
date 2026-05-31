import uuid
import logging
import re
import os
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TypedDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.language import detect_message_language
from app.db.base_repository import MessageRepository, ConversationRepository
from app.models.chatbot import Chatbot
from app.models.persona import Persona, PersonaTrait
from app.models.conversation import Conversation, Message as DBMessage, ConversationStatus, MessageRole
from app.models.ai_model import AIModelConfig
from app.services.bot import model_config_service
from app.services.vector_store import VectorStoreService

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

# --- LangGraph State Definition ---
class AgentState(TypedDict, total=False):
    user_message: str
    history: List[DBMessage]
    api_key: Optional[str]
    model_name: str
    persona: Persona
    traits: List[str]
    chatbot_id: str
    
    # Pipeline variables
    intent: Optional[str]
    rewritten_query: Optional[str]
    sources: List[Dict[str, Any]]
    context_text: str
    is_relevant: bool
    
    # Final Output
    response: str
    status: ConversationStatus


from app.services.semantic_router import SemanticRouter

# --- Intent Heuristics Classifier (DEPRECATED) ---
# We keep this strictly for reference or completely remove it. It's been replaced by SemanticRouter.
# ------------------------------------------------

# --- Agent Graph Executor ---
class AgentGraphExecutor:
    """
    Pure graph executor operating on state dictionary variables.
    Decoupled entirely from database models/transactions.
    """
    @staticmethod
    def _get_llm(state: AgentState, temperature: float = 0.3) -> Optional[ChatOpenAI]:
        if not state.get("api_key"):
            return None
        return ChatOpenAI(api_key=state["api_key"], model=state["model_name"], temperature=temperature)

    @staticmethod
    def _content_terms(text: str) -> set[str]:
        stop_words = {
            "the", "and", "for", "are", "you", "your", "with", "that", "this", "what", "when", "where",
            "how", "why", "can", "could", "would", "should", "about", "from", "into", "have", "has",
            "hai", "hain", "kya", "aur", "mein", "mujhe", "aap", "ap", "ke", "ki", "ka", "ko", "se",
        }
        return {
            word
            for word in re.findall(r"\w+", text.lower())
            if len(word) > 2 and word not in stop_words
        }

    @classmethod
    def _has_lexical_relevance(cls, query: str, context: str) -> bool:
        query_terms = cls._content_terms(query)
        if not query_terms:
            return bool(context.strip())

        context_terms = cls._content_terms(context)
        overlap = query_terms & context_terms
        if not overlap:
            return False

        overlap_ratio = len(overlap) / max(len(query_terms), 1)
        return len(overlap) >= 2 or overlap_ratio >= 0.35

    # --- Node Functions ---
    @staticmethod
    def route_intent(state: AgentState) -> AgentState:
        # 1. Fast Semantic Routing using Embeddings
        intent = SemanticRouter.classify(state["user_message"])
        if intent:
            return {"intent": intent}
                
        # 2. Fallback directly to RAG_LOOKUP
        return {"intent": "RAG_LOOKUP"}

    @staticmethod
    def agent_handoff_node(state: AgentState) -> AgentState:
        lang = state["persona"].language
        if lang == "multilingual":
            lang = detect_message_language(state["user_message"], state.get("history"))
            
        if lang == "urdu":
            text = "میں آپ کی درخواست کو کسٹمر سپورٹ ایجنٹ کو منتقل کر رہا ہوں۔ ہماری ٹیم جلد ہی آپ سے رابطہ کرے گی۔"
        elif lang == "english":
            text = "I am transferring your request to a support agent. Someone from our team will contact you shortly."
        else:
            text = "Main aap ki request support agent ko transfer kar raha hoon. Thodi der mein humari team aap se rabta karegi."
            
        return {"response": text, "status": ConversationStatus.ESCALATED}

    @staticmethod
    def conversational_node(state: AgentState) -> AgentState:
        llm = AgentGraphExecutor._get_llm(state, temperature=0.7)
        greeting = getattr(state["persona"], "greeting", None) or "Hello! How can I help you today?"
        
        if llm:
            try:
                detected_lang = detect_message_language(state["user_message"], state.get("history"))
                lang_name = {
                    "urdu": "Urdu Script",
                    "roman_urdu": "Roman Urdu (Urdu written in English alphabets)",
                    "english": "English"
                }.get(detected_lang, "English")

                desc = getattr(state["persona"], "description", None) or ""
                desc_str = f"Description/Role: {desc}\n" if desc else ""
                sys_msg = SystemMessage(content=(
                    f"You are {state['persona'].name or 'Aina Bot'}. "
                    f"Your traits are: {', '.join(state['traits'])}. "
                    f"{desc_str}"
                    "IMPORTANT GUIDELINES:\n"
                    "1. Act strictly as a human representative. Never mention that you are an AI, a bot, or reading from a 'context' or 'database'.\n"
                    "2. Use natural, conversational language. Be polite and empathetic.\n"
                    f"3. Greet the user and chat politely. Your main greeting is: '{greeting}'.\n"
                    f"4. You MUST strictly speak and reply in: {lang_name}."
                ))
                messages = [sys_msg]
                for m in state["history"][-6:]:
                    role = HumanMessage if m.role == MessageRole.USER else AIMessage
                    messages.append(role(content=m.content))
                messages.append(HumanMessage(content=state["user_message"]))
                
                result = llm.invoke(messages).content.strip()
                return {"response": result}
            except Exception as e:
                logger.warning(f"LLM conversational generation failed: {e}")
                
        return {"response": greeting}

    @staticmethod
    def rewrite_node(state: AgentState) -> AgentState:
        llm = AgentGraphExecutor._get_llm(state)
        user_msg = state["user_message"]
        
        if not state["history"] or not llm:
            return {"rewritten_query": user_msg}
            
        try:
            history_str = ""
            for m in state["history"][-4:]:
                role_label = "USER" if m.role == MessageRole.USER else "BOT"
                history_str += f"{role_label}: {m.content}\n"
                
            sys_msg = SystemMessage(content=(
                "You are a search query rewriter. Given the chat history and the latest user message, rewrite the user message to be a standalone search query.\n"
                "CRITICAL RULES:\n"
                "1. If the user introduces a NEW topic, DO NOT mix it with the previous topic.\n"
                "2. If the user uses a pronoun ('it', 'this') and the history makes it 100% obvious, replace the pronoun. If it is ambiguous, leave it broad.\n"
                "3. If the latest message is already standalone, output it exactly as is.\n"
                "Do not answer the question; just output the rewritten query."
            ))
            h_msg = HumanMessage(content=f"History:\n{history_str}\nLatest user message: \"{user_msg}\"\nStandalone query:")
            
            rewritten = llm.invoke([sys_msg, h_msg]).content.strip()
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
            return {"rewritten_query": rewritten}
        except Exception as e:
            logger.warning(f"Query rewrite failed: {e}")
            return {"rewritten_query": user_msg}

    @staticmethod
    def retrieve_node(state: AgentState) -> AgentState:
        rewritten = state.get("rewritten_query")
        original = state["user_message"]
        
        # If no rewrite or exactly the same, do a single search
        if not rewritten or rewritten.lower().strip() == original.lower().strip():
            sources_list = VectorStoreService.search_hybrid(state["chatbot_id"], original, top_k=4)
        else:
            # Multi-Query Retrieval: search both and merge
            sources_rewritten = VectorStoreService.search_hybrid(state["chatbot_id"], rewritten, top_k=3)
            sources_original = VectorStoreService.search_hybrid(state["chatbot_id"], original, top_k=3)
            
            seen_chunks = set()
            sources_list = []
            
            # Interleave to balance results, deduplicating by chunk_id
            for r, o in zip(sources_rewritten + [None]*3, sources_original + [None]*3):
                if r and r["chunk_id"] not in seen_chunks:
                    sources_list.append(r)
                    seen_chunks.add(r["chunk_id"])
                if o and o["chunk_id"] not in seen_chunks:
                    sources_list.append(o)
                    seen_chunks.add(o["chunk_id"])
                    
            # Keep top 4 combined
            sources_list = sources_list[:4]
        
        context_text = "\n\n".join(
            f"[Source {idx + 1}]\n{chunk['text']}"
            for idx, chunk in enumerate(sources_list)
        )
        sources = [
            {
                "chunk_id": chunk["chunk_id"],
                "source_id": chunk["source_id"],
                "text": chunk["text"],
                "score": chunk["score"]
            }
            for chunk in sources_list
        ]
        return {"sources": sources, "context_text": context_text}

    @staticmethod
    def validate_node(state: AgentState) -> AgentState:
        sources = state.get("sources", [])
        if not sources:
            return {"is_relevant": False, "context_text": ""}
            
        llm = AgentGraphExecutor._get_llm(state)
        query = state.get("rewritten_query") or state["user_message"]
        
        if not llm:
            return {"is_relevant": AgentGraphExecutor._has_lexical_relevance(query, state.get("context_text", ""))}
            
        try:
            sys_msg = SystemMessage(content=(
                "You are an expert Semantic Reranker and Hallucination Filter. "
                "Evaluate each provided source text against the user query. "
                "Determine which sources contain relevant information to answer the query.\n"
                "Respond ONLY with a comma-separated list of the Source IDs that are relevant (e.g., 0, 2). "
                "If NONE of the sources are relevant, reply exactly with NONE."
            ))
            
            sources_text = ""
            for idx, src in enumerate(sources):
                sources_text += f"[Source {idx}]\n{src['text']}\n\n"
                
            h_msg = HumanMessage(content=f"Query: \"{query}\"\n\nSources:\n{sources_text}\nRelevant Source IDs:")
            
            answer = llm.invoke([sys_msg, h_msg]).content.strip().upper()
            
            if answer == "NONE" or not answer:
                return {"is_relevant": False, "sources": [], "context_text": ""}
                
            valid_indices = []
            for part in answer.replace(" ", "").split(","):
                if part.isdigit():
                    idx = int(part)
                    if 0 <= idx < len(sources):
                        valid_indices.append(idx)
                        
            if not valid_indices:
                return {"is_relevant": False, "sources": [], "context_text": ""}
                
            filtered_sources = [sources[i] for i in valid_indices]
            
            new_context_text = "\n\n".join(
                f"[Source {idx + 1}]\n{chunk['text']}"
                for idx, chunk in enumerate(filtered_sources)
            )
            
            return {
                "is_relevant": True, 
                "sources": filtered_sources, 
                "context_text": new_context_text
            }
        except Exception as e:
            logger.warning(f"Semantic validation failed: {e}")
            return {"is_relevant": True}

    @staticmethod
    def _generate_mock_response(query: str, context: str, persona: Persona, traits: List[str]) -> str:
        query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 3]
        sentences = re.split(r'[.!?\n]+', context)
        
        matched_sentence = ""
        best_match_count = 0
        for s in sentences:
            s_lower = s.lower()
            cnt = sum(1 for w in query_words if w in s_lower)
            if cnt > best_match_count:
                best_match_count = cnt
                matched_sentence = s.strip()
                
        if not matched_sentence and sentences:
            for s in sentences:
                if s.strip():
                    matched_sentence = s.strip()
                    break

        lang = detect_message_language(query)
        if lang == "urdu":
            ans = f"معلومات کے مطابق: {matched_sentence}۔" if matched_sentence else "معاف کیجئے گا، میرے پاس اس کے متعلق معلومات نہیں ہیں۔"
        elif lang == "roman_urdu":
            ans = f"Maine details check ki hain: {matched_sentence}." if matched_sentence else "I'm sorry, mere paas is ki exact details nahi hain."
        else:
            ans = f"Here is what I found: {matched_sentence}." if matched_sentence else "I'm sorry, I couldn't find that specific information right now."

        if "Friendly" in traits:
            ans += " I am here to help."
        elif "Professional" in traits:
            ans = f"Dear User, {ans}"
            
        return ans

    @staticmethod
    def rag_answer_node(state: AgentState) -> AgentState:
        if not state.get("is_relevant") or not state.get("context_text"):
            # Check for custom fallback in persona first
            fallback_msg = getattr(state["persona"], "fallback", None)
            if fallback_msg:
                return {"response": fallback_msg}
                
            lang = state["persona"].language
            if lang == "multilingual":
                lang = detect_message_language(state["user_message"], state.get("history"))
                
            if lang == "urdu":
                ans = "معاف کیجئے گا، میرے پاس فی الحال اس کی تفصیلات موجود نہیں ہیں۔ کیا میں آپ کا رابطہ ہماری ٹیم سے کروا دوں؟"
            elif lang == "roman_urdu":
                ans = "I'm sorry, mere paas is waqt iski exact details nahi hain. Kya main aapka rabta apni support team se karwa doon?"
            elif lang == "english":
                ans = "I'm sorry, I don't have the exact details for that right now. Would you like me to connect you to someone from our team who can help?"
            else:
                detected = detect_message_language(state["user_message"], state.get("history"))
                if detected == "urdu":
                    ans = "معاف کیجئے گا، میرے پاس فی الحال اس کی تفصیلات موجود نہیں ہیں۔ کیا میں آپ کا رابطہ ہماری ٹیم سے کروا دوں؟"
                elif detected == "roman_urdu":
                    ans = "I'm sorry, mere paas is waqt iski exact details nahi hain. Kya main aapka rabta apni support team se karwa doon?"
                else:
                    ans = "I'm sorry, I don't have the exact details for that right now. Would you like me to connect you to someone from our team who can help?"
            return {"response": ans}

        llm = AgentGraphExecutor._get_llm(state)
        if llm:
            try:
                desc = getattr(state["persona"], "description", None) or ""
                desc_str = f"Description/Role: {desc}\n" if desc else ""
                sys_msg = SystemMessage(content=(
                    f"You are {state['persona'].name or 'Aina Bot'}. Traits: {', '.join(state['traits'])}. "
                    f"{desc_str}"
                    "IMPORTANT GUIDELINES:\n"
                    "1. Act strictly as a human representative. Never mention that you are an AI, a bot, or reading from a 'context' or 'database'.\n"
                    "2. Use ONLY the following context to answer the user's query. If you do not know the answer, politely say you don't know without breaking character. "
                    "3. Generate the response in the user's input language (English, Urdu script, or Roman Urdu).\n\n"
                    f"Context:\n{state['context_text']}"
                ))
                messages = [sys_msg]
                for m in state["history"][-6:]:
                    role = HumanMessage if m.role == MessageRole.USER else AIMessage
                    messages.append(role(content=m.content))
                messages.append(HumanMessage(content=state["user_message"]))
                
                ans = llm.invoke(messages).content.strip()
                return {"response": ans}
            except Exception as e:
                logger.warning(f"RAG generation failed: {e}")
                
        # Mock fallback
        ans = AgentGraphExecutor._generate_mock_response(
            state.get("rewritten_query") or state["user_message"], 
            state["context_text"], 
            state["persona"], 
            state["traits"]
        )
        return {"response": ans}

    @classmethod
    def build_graph(cls):
        workflow = StateGraph(AgentState)
        
        workflow.add_node("route", cls.route_intent)
        workflow.add_node("agent_handoff", cls.agent_handoff_node)
        workflow.add_node("conversational", cls.conversational_node)
        workflow.add_node("rewrite", cls.rewrite_node)
        workflow.add_node("retrieve", cls.retrieve_node)
        workflow.add_node("validate", cls.validate_node)
        workflow.add_node("rag_answer", cls.rag_answer_node)
        
        workflow.set_entry_point("route")
        
        def route_condition(state: AgentState):
            return state["intent"]
            
        workflow.add_conditional_edges("route", route_condition, {
            "AGENT_HANDOFF": "agent_handoff",
            "FRUSTRATION": "agent_handoff",
            "CONVERSATIONAL": "conversational",
            "RAG_LOOKUP": "rewrite"
        })
        
        workflow.add_edge("agent_handoff", END)
        workflow.add_edge("conversational", END)
        workflow.add_edge("rewrite", "retrieve")
        workflow.add_edge("retrieve", "validate")
        workflow.add_edge("validate", "rag_answer")
        workflow.add_edge("rag_answer", END)
        
        return workflow.compile()

    @classmethod
    def execute(cls, initial_state: AgentState) -> AgentState:
        graph = cls.build_graph()
        return graph.invoke(initial_state)


# --- Chat Service Orchestrator ---
class ChatService:
    """
    Orchestrator class managing DB transactions, security, lookup, and updates.
    Invokes the pure AgentGraphExecutor for LangGraph execution.
    """
    message_repo = MessageRepository()
    conversation_repo = ConversationRepository()

    @staticmethod
    def route_intent(state: AgentState) -> AgentState:
        return AgentGraphExecutor.route_intent(state)

    @classmethod
    def get_rag_response(
        cls, db: Session, org_id: uuid.UUID, chatbot_id: uuid.UUID, user_message: str, conversation_id: Optional[uuid.UUID] = None, deployment_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        
        # 1. Fetch resources
        chatbot = db.query(Chatbot).filter(
            Chatbot.id == chatbot_id, 
            Chatbot.org_id == org_id, 
            Chatbot.deleted_at == None
        ).first()
        if not chatbot:
            raise ValueError("Chatbot not found or inaccessible")

        persona = db.query(Persona).filter(
            Persona.id == chatbot.persona_id, 
            Persona.deleted_at == None
        ).first()
        if not persona:
            raise ValueError("Chatbot Persona not found")

        traits = [t.trait_name for t in db.query(PersonaTrait).filter(PersonaTrait.persona_id == persona.id).all()]

        # 2. Resolve credentials safely
        api_key = None
        active_config = db.query(AIModelConfig).filter(AIModelConfig.org_id == org_id).first()
        if active_config:
            try:
                api_key = model_config_service.decrypt_key(active_config.encrypted_api_key)
            except Exception:
                pass

        if not api_key:
            api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")

        # 3. Resolve session
        is_new_conv = False
        if conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == conversation_id, 
                Conversation.chatbot_id == chatbot_id, 
                Conversation.deleted_at == None
            ).first()
            if not conversation:
                raise ValueError("Conversation session not found")
            
            # If resolved, auto-resume bot
            if conversation.status == ConversationStatus.RESOLVED:
                conversation.status = ConversationStatus.ONGOING
                conversation.assigned_agent_id = None
                db.add(conversation)
                db.flush()
        else:
            conversation = Conversation(chatbot_id=chatbot_id, status=ConversationStatus.ONGOING, deployment_id=deployment_id)
            db.add(conversation)
            db.flush()
            is_new_conv = True

        # If already escalated, bypass RAG execution
        if conversation.status == ConversationStatus.ESCALATED:
            from app.services.escalation_router import EscalationRouter
            return EscalationRouter.handle_escalated_message(
                db=db,
                conversation=conversation,
                chatbot=chatbot,
                org_id=org_id,
                user_message=user_message,
                language=persona.language,
                active_config_id=active_config.id if active_config else None
            )

        start_date = conversation.started_at
        end_date = datetime.now(timezone.utc)
        history = cls.message_repo.fetch_history(db, conversation.id, start_date, end_date)

        # 4. Invoke graph execution without DB dependencies
        initial_state = {
            "user_message": user_message,
            "history": history,
            "api_key": api_key,
            "model_name": "gpt-4o",
            "persona": persona,
            "traits": traits,
            "chatbot_id": str(chatbot_id),
            "status": conversation.status,
            "sources": []
        }
        
        final_state = AgentGraphExecutor.execute(initial_state)

        # 5. Extract values and update database context
        response_text = final_state.get("response", "An error occurred during generation.")
        new_status = final_state.get("status", conversation.status)
        sources = final_state.get("sources", [])

        if new_status == ConversationStatus.ESCALATED:
            from app.services.escalation_router import EscalationRouter
            return EscalationRouter.escalate(
                db=db,
                conversation=conversation,
                chatbot=chatbot,
                org_id=org_id,
                user_message=user_message,
                response_text=response_text,
                language=persona.language,
                is_new_conv=is_new_conv,
                active_config_id=active_config.id if active_config else None,
                sources=sources
            )

        if new_status != conversation.status:
            conversation.status = new_status
            db.add(conversation)

        # Record messages
        db.add(DBMessage(
            conversation_id=conversation.id, 
            role=MessageRole.USER, 
            content=user_message, 
            config_id=active_config.id if active_config else None
        ))
        db.add(DBMessage(
            conversation_id=conversation.id, 
            role=MessageRole.BOT, 
            content=response_text, 
            config_id=active_config.id if active_config else None
        ))

        # Update chatbot statistics
        chatbot.total_messages += 2
        if is_new_conv:
            chatbot.total_conversations += 1
        db.add(chatbot)
        
        db.commit()

        return {
            "response": response_text,
            "conversation_id": conversation.id,
            "sources": sources,
            "status": new_status
        }
