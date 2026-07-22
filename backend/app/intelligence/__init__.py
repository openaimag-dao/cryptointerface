"""Intelligence Layer (Sprint 4): macro/sentiment/LLM-explanation modules
that sit alongside the Sprint 1-3 Data Engine and AI Decision Engine.

Analysis only, same as the rest of the app — nothing in here ever places
an order. `llm/` in particular only explains an already-computed
`AIDecision` from `app.ai_engine`; it never scores or decides anything
itself. See `backend/README.md`'s "Intelligence Layer" section for the
full architecture.
"""
