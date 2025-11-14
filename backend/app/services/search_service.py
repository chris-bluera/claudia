"""
Semantic search service using pgvector
Provides similarity search over user prompts and assistant messages
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.db.models import UserPromptModel, AssistantMessageModel, SessionModel
from app.services.embedding_service import get_embedding_service


class SearchService:
    """
    Service for semantic search using pgvector cosine similarity
    """

    def __init__(self):
        """Initialize search service"""
        self.embedding_service = get_embedding_service()

    async def search_prompts(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search user prompts by semantic similarity

        Args:
            db: Database session
            query: Search query text
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score (0-1)
            session_id: Optional filter by session

        Returns:
            List of matching prompts with similarity scores
        """
        # Generate embedding for query
        query_embedding = await self.embedding_service.generate_embedding(query)

        if not query_embedding:
            logger.error("Could not generate embedding for search query")
            return []

        # Build similarity query using pgvector operators
        # cosine_distance = 1 - (embedding <=> query_embedding)
        # Returns results ordered by similarity (highest first)

        base_query = select(
            UserPromptModel,
            SessionModel,
            (1 - func.cosine_distance(UserPromptModel.embedding, query_embedding)).label('similarity')
        ).join(
            SessionModel,
            UserPromptModel.session_id == SessionModel.id
        ).where(
            UserPromptModel.embedding.isnot(None)
        )

        # Filter by session if provided
        if session_id:
            base_query = base_query.where(SessionModel.session_id == session_id)

        # Filter by similarity threshold and order
        query_stmt = base_query.having(
            (1 - func.cosine_distance(UserPromptModel.embedding, query_embedding)) >= similarity_threshold
        ).order_by(
            (1 - func.cosine_distance(UserPromptModel.embedding, query_embedding)).desc()
        ).limit(limit)

        result = await db.execute(query_stmt)
        rows = result.all()

        # Format results
        results = []
        for prompt, session, similarity in rows:
            results.append({
                'id': str(prompt.id),
                'prompt_text': prompt.prompt_text,
                'similarity': float(similarity),
                'created_at': prompt.created_at.isoformat(),
                'session': {
                    'session_id': session.session_id,
                    'project_name': session.project_name,
                    'project_path': session.project_path
                },
                'metadata': prompt.prompt_metadata
            })

        logger.info(f"Found {len(results)} similar prompts for query: '{query[:50]}...'")
        return results

    async def search_messages(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.5,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search assistant messages by semantic similarity

        Args:
            db: Database session
            query: Search query text
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score (0-1)
            session_id: Optional filter by session

        Returns:
            List of matching messages with similarity scores
        """
        # Generate embedding for query
        query_embedding = await self.embedding_service.generate_embedding(query)

        if not query_embedding:
            logger.error("Could not generate embedding for search query")
            return []

        base_query = select(
            AssistantMessageModel,
            SessionModel,
            (1 - func.cosine_distance(AssistantMessageModel.embedding, query_embedding)).label('similarity')
        ).join(
            SessionModel,
            AssistantMessageModel.session_id == SessionModel.id
        ).where(
            AssistantMessageModel.embedding.isnot(None)
        )

        # Filter by session if provided
        if session_id:
            base_query = base_query.where(SessionModel.session_id == session_id)

        # Filter by similarity threshold and order
        query_stmt = base_query.having(
            (1 - func.cosine_distance(AssistantMessageModel.embedding, query_embedding)) >= similarity_threshold
        ).order_by(
            (1 - func.cosine_distance(AssistantMessageModel.embedding, query_embedding)).desc()
        ).limit(limit)

        result = await db.execute(query_stmt)
        rows = result.all()

        # Format results
        results = []
        for message, session, similarity in rows:
            results.append({
                'id': str(message.id),
                'message_text': message.message_text,
                'conversation_turn': message.conversation_turn,
                'similarity': float(similarity),
                'created_at': message.created_at.isoformat(),
                'session': {
                    'session_id': session.session_id,
                    'project_name': session.project_name,
                    'project_path': session.project_path
                },
                'metadata': message.message_metadata
            })

        logger.info(f"Found {len(results)} similar messages for query: '{query[:50]}...'")
        return results

    async def search_conversations(
        self,
        db: AsyncSession,
        query: str,
        limit: int = 10,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search both prompts and messages, returning unified results

        Args:
            db: Database session
            query: Search query text
            limit: Maximum results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of matching content (prompts + messages) with similarity scores
        """
        # Search both in parallel
        prompts = await self.search_prompts(db, query, limit, similarity_threshold)
        messages = await self.search_messages(db, query, limit, similarity_threshold)

        # Combine and sort by similarity
        combined = []

        for prompt in prompts:
            combined.append({
                **prompt,
                'type': 'prompt'
            })

        for message in messages:
            combined.append({
                **message,
                'type': 'message',
                'text': message.pop('message_text')  # Normalize field name
            })

        # Rename prompt_text to text for prompts
        for item in combined:
            if item['type'] == 'prompt':
                item['text'] = item.pop('prompt_text')

        # Sort by similarity
        combined.sort(key=lambda x: x['similarity'], reverse=True)

        # Limit results
        results = combined[:limit]

        logger.info(f"Found {len(results)} total results ({len(prompts)} prompts, {len(messages)} messages)")
        return results


# Global service instance
search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """Get or create global search service instance"""
    global search_service
    if search_service is None:
        search_service = SearchService()
    return search_service
