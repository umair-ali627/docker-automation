# app/services/agent_rag.py
import logging
from typing import List, Dict, Any, Optional, Union
import uuid

from livekit.agents import llm, JobContext
from livekit.agents import AgentSession

from ..services.vector_search import vector_search
from ..utils.db_utils import with_worker_db
from ..crud.crud_documents import document_service

logger = logging.getLogger("[agent-rag]")


class AgentRAGService:
    @staticmethod
    async def enrich_with_rag(
        agent: AgentSession,
        chat_ctx: llm.ChatContext,
        agent_id: Optional[Union[uuid.UUID, str]] = None
    ) -> llm.LLMStream:
        """
        Enrich the conversation context with RAG results before generating response
        """
        if not chat_ctx.messages:
            return agent.llm.chat(chat_ctx=chat_ctx)

        # Get the last user message for RAG query
        last_user_msg = None
        for msg in reversed(chat_ctx.messages):
            if msg.role == "user":
                last_user_msg = msg
                break

        if not last_user_msg or not last_user_msg.content:
            return agent.llm.chat(chat_ctx=chat_ctx)

        # Get knowledge bases associated with the agent
        knowledge_bases = await AgentRAGService._get_knowledge_bases(agent_id)
        if not knowledge_bases:
            return agent.llm.chat(chat_ctx=chat_ctx)

        # Query each knowledge base and collect results
        all_results = []
        for kb in knowledge_bases:
            try:
                # Query Qdrant directly without DB connection
                results = await vector_search.query(
                    query_text=last_user_msg.content,
                    collection_name=kb.get("qdrant_collection"),
                    limit=3
                )

                # Add source information to each result
                for result in results:
                    result["source"] = {
                        "knowledge_base_id": kb.get("id"),
                        "knowledge_base_name": kb.get("name")
                    }

                all_results.extend(results)
                logger.info(
                    f"Retrieved results from knowledge base {kb.get('id')}: {results}")
            except Exception as e:
                logger.error(
                    f"Error querying knowledge base {kb.get('id')}: {e}")

        # Sort by score (higher is better)
        all_results.sort(key=lambda x: x.get("score", 0.0), reverse=True)

        # Take top results
        top_results = all_results[:5]

        if not top_results:
            return agent.llm.chat(chat_ctx=chat_ctx)

        # Prepare context with retrieved information
        context_sections = []
        for result in top_results:
            kb_name = result.get("source", {}).get(
                "knowledge_base_name", "Unknown Source")
            context_sections.append(
                f"[Source: {kb_name}]\n{result['content']}"
            )

        context = "\n\n".join(context_sections)

        # Add retrieval context as a system message
        retrieval_message = llm.ChatMessage.create(
            role="system",
            text=(
                "Here is information from my knowledge base that may help answer the user's question:\n\n"
                f"{context}\n\n"
                "Use this information to inform your response, but don't mention that you're using a knowledge base unless explicitly asked."
            )
        )

        # Create a new chat context with the retrieval message right before the last user message
        new_ctx = llm.ChatContext()

        # Copy all messages before the last user message
        for i, msg in enumerate(chat_ctx.messages):
            if msg.id == last_user_msg.id:
                # Add retrieval message before user message
                new_ctx.messages.append(retrieval_message)
                new_ctx.messages.append(msg)
            else:
                new_ctx.messages.append(msg)

        # Call LLM with enhanced context
        return agent.llm.chat(chat_ctx=new_ctx)

    @staticmethod
    async def _get_knowledge_bases(agent_id: Optional[Union[uuid.UUID, str]]) -> List[Dict[str, Any]]:
        """Get knowledge bases associated with the agent profile"""
        if not agent_id:
            return []

        try:
            # Convert string to UUID if needed
            if isinstance(agent_id, str):
                try:
                    agent_id = uuid.UUID(agent_id)
                except ValueError:
                    logger.warning(f"Invalid agent ID format: {agent_id}")
                    return []

            # Query the database to get knowledge bases for this agent
            async def get_kb_data(db):
                knowledge_bases = await document_service.get_knowledge_bases_by_agent(
                    db=db, agent_id=agent_id
                )

                return [
                    {
                        "id": kb.get("id") if isinstance(kb, dict) else kb.id,
                        "name": kb.get("name") if isinstance(kb, dict) else kb.name,
                        "qdrant_collection": kb.get("qdrant_collection") if isinstance(kb, dict) else kb.qdrant_collection
                    }
                    for kb in knowledge_bases
                ]

            kb_data = await with_worker_db(get_kb_data)
            return kb_data or []

        except Exception as e:
            logger.error(
                f"Error getting knowledge bases for agent {agent_id}: {e}")
            return []


rag_service = AgentRAGService()
