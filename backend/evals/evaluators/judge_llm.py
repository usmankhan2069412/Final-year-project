"""
LLM-as-a-Judge Evaluator for RAG Faithfulness, Answer Relevance, and Persona Tone Adherence.
Outputs numerical scores (0.0 - 1.0) with reasoning.
"""

import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings, resolve_openrouter_key

logger = logging.getLogger(__name__)


class LLMJudge:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        effective_key, base_url = resolve_openrouter_key(api_key or settings.OPENROUTER_API_KEY)
        if not effective_key:
            raise ValueError("API key required for LLM Judge. Provide api_key or set OPENROUTER_API_KEY in .env")

        target_model = model_name or settings.EVAL_JUDGE_MODEL
        target_temp = temperature if temperature is not None else settings.EVAL_JUDGE_TEMPERATURE
        model_to_use = target_model if base_url else (target_model.split("/")[-1] if "/" in target_model else target_model)
        
        llm_kwargs = {
            "api_key": effective_key,
            "model": model_to_use,
            "temperature": target_temp,
            "streaming": False,
        }
        if base_url:
            llm_kwargs["base_url"] = base_url

        self.llm = ChatOpenAI(**llm_kwargs)

    async def evaluate_faithfulness(
        self,
        question: str,
        context: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Grades whether the answer is 100% grounded in the context without hallucinations.
        Score: 0.0 to 1.0
        """
        system_prompt = (
            "You are an impartial, strict evaluation judge for a RAG system.\n"
            "Your task is to evaluate FAITHFULNESS (groundedness).\n"
            "An answer is faithful if EVERY factual claim in the answer is directly supported by the context.\n"
            "If the answer invents facts not mentioned in the context, penalize the score.\n"
            "Respond ONLY with valid JSON in this format:\n"
            "{\n"
            '  "score": <float between 0.0 and 1.0>,\n'
            '  "hallucinated_claims": [<list of unsupported claims, or empty>],\n'
            '  "reasoning": "<short explanation>"\n'
            "}"
        )

        user_content = (
            f"[CONTEXT]:\n{context}\n\n"
            f"[QUESTION]:\n{question}\n\n"
            f"[GENERATED ANSWER]:\n{answer}"
        )

        try:
            res = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content)
            ])
            text = res.content.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error in evaluate_faithfulness: {e}")
            return {"score": 0.0, "hallucinated_claims": [], "reasoning": f"Evaluation error: {str(e)}"}

    async def evaluate_answer_relevance(
        self,
        question: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        Grades whether the answer directly and completely answers the user's question.
        Score: 0.0 to 1.0
        """
        system_prompt = (
            "You are an impartial evaluation judge for a conversational AI system.\n"
            "Your task is to evaluate ANSWER RELEVANCE.\n"
            "Evaluate if the answer directly addresses the user's question concisely and clearly.\n"
            "Penalize if the answer is vague, repetitive, evasive, or answers a different question.\n"
            "Respond ONLY with valid JSON in this format:\n"
            "{\n"
            '  "score": <float between 0.0 and 1.0>,\n'
            '  "reasoning": "<short explanation>"\n'
            "}"
        )

        user_content = (
            f"[QUESTION]:\n{question}\n\n"
            f"[GENERATED ANSWER]:\n{answer}"
        )

        try:
            res = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content)
            ])
            text = res.content.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error in evaluate_answer_relevance: {e}")
            return {"score": 0.0, "reasoning": f"Evaluation error: {str(e)}"}

    async def evaluate_persona_adherence(
        self,
        persona_name: str,
        persona_traits: list,
        answer: str
    ) -> Dict[str, Any]:
        """
        Grades whether the answer adheres to the persona's tone, name, and style,
        and avoids AI meta-talk ('As an AI language model', 'According to my database').
        Score: 0.0 to 1.0
        """
        system_prompt = (
            "You are an evaluator assessing AI Persona Adherence.\n"
            "Check if the answer:\n"
            "1. Matches the given persona name and traits.\n"
            "2. Never breaks character (NEVER mentions being an AI model, reading from a database, or OpenAI).\n"
            "Respond ONLY with valid JSON in this format:\n"
            "{\n"
            '  "score": <float between 0.0 and 1.0>,\n'
            '  "broke_character": <true/false>,\n'
            '  "reasoning": "<short explanation>"\n'
            "}"
        )

        user_content = (
            f"[PERSONA NAME]: {persona_name}\n"
            f"[PERSONA TRAITS]: {', '.join(persona_traits)}\n\n"
            f"[BOT ANSWER]:\n{answer}"
        )

        try:
            res = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content)
            ])
            text = res.content.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error in evaluate_persona_adherence: {e}")
            return {"score": 0.0, "broke_character": False, "reasoning": f"Evaluation error: {str(e)}"}

    async def evaluate_query_rewriter(
        self,
        chat_history: str,
        user_message: str,
        rewritten_query: str,
        expected_query: str
    ) -> Dict[str, Any]:
        """
        Evaluates whether a query rewriter correctly resolved pronouns, preserved intent,
        and produced a clean standalone search query.
        Score: 0.0 to 1.0
        """
        system_prompt = (
            "You are an evaluator assessing a Contextual Search Query Rewriter in a RAG pipeline.\n"
            "The rewriter takes chat history and a latest user message, and produces a standalone search query.\n"
            "Evaluate:\n"
            "1. Did it resolve ambiguous pronouns/references using the history?\n"
            "2. Did it preserve the user's intent without hallucinating unrelated topics?\n"
            "3. If the user message was already standalone or a new topic, did it avoid polluting it?\n"
            "Respond ONLY with valid JSON in this format:\n"
            "{\n"
            '  "score": <float between 0.0 and 1.0>,\n'
            '  "coreference_resolved": <true/false>,\n'
            '  "hallucination_detected": <true/false>,\n'
            '  "reasoning": "<short explanation>"\n'
            "}"
        )

        user_content = (
            f"[CHAT HISTORY]:\n{chat_history}\n\n"
            f"[ORIGINAL USER MESSAGE]: {user_message}\n\n"
            f"[REWRITTEN QUERY PRODUCED]: {rewritten_query}\n\n"
            f"[EXPECTED IDEAL QUERY]: {expected_query}"
        )

        try:
            res = await self.llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_content)
            ])
            text = res.content.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Error in evaluate_query_rewriter: {e}")
            return {
                "score": 0.0,
                "coreference_resolved": False,
                "hallucination_detected": False,
                "reasoning": f"Evaluation error: {str(e)}"
            }
