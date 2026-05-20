# Phase 4: Chat Interface & RAG Engine

## Goal
Implement the chat session schemas, FAISS similarity search, RAG prompt orchestration, fallback LLM responses, and `/chat` endpoints.

## Tasks
- [ ] Task 1: Add `openai>=1.0.0` to `backend/requirements.txt` → Verify: Run `pip install -r backend/requirements.txt` successfully
- [ ] Task 2: Implement `BaseRepository` in `backend/app/db/base_repository.py` → Verify: Test assertions verify date-range filters are enforced for partitioned queries
- [ ] Task 3: Create database models `Deployment`, `Conversation`, and `Message` in `backend/app/models/conversation.py` and register them in `backend/app/db/base.py` → Verify: Database tables are auto-created on application startup
- [ ] Task 4: Define Pydantic request/response schemas in `backend/app/schemas/chat.py` → Verify: Code builds and type checks successfully
- [ ] Task 5: Add vector query `search_vectors` to `VectorStoreService` in `backend/app/services/vector_store.py` → Verify: Search returns correct chunk matches and scores
- [ ] Task 6: Implement RAG orchestration in `backend/app/services/chat.py` with OpenAI API integration and fallback mock response logic → Verify: Calling the service returns grounded answers based on persona and documents
- [ ] Task 7: Implement endpoints `POST /api/v1/chat/message` and `GET /api/v1/chat/history/{session_id}` in `backend/app/api/v1/messaging.py` and register it in `backend/app/main.py` → Verify: Swagger docs at `/docs` reflect the new endpoints
- [ ] Task 8: Write and run integration test suite `backend/tests/test_chat.py` covering the complete chat and RAG flow → Verify: Run `python backend/tests/test_chat.py` and confirm all tests pass

## Done When
- [ ] DB tables `conversations`, `messages`, and `deployments` are successfully created.
- [ ] Similarity search query on FAISS retrieves valid chunks with relevance scoring.
- [ ] Interactive chat RAG service resolves LLM calls or falls back to mock responses.
- [ ] `/chat/message` and `/chat/history` REST APIs are verified with 200 responses.
- [ ] Integration tests pass in full.

## Notes
- Enforce strict tenant isolation using the database context's `app.current_org_id` in RLS policies.
- Ensure that the nightly counter synchronization rules can safely run over these tables in the future.
