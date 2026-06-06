"""
ai/test_policy_rag.py

Quick test script to verify policy ingestion and RAG retrieval.
Run via: python manage.py shell < ai/test_policy_rag.py
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "room_booking_system.settings")
django.setup()


# Test 1: Check vector store
try:
    from ai.vector_store import get_vector_store

    vs = get_vector_store()
    stats = vs.get_collection_stats()
except Exception:
    sys.exit(1)

# Test 2: Check document loader
try:
    from ai.document_ingestion_langchain import LangChainDocumentLoader

    loader = LangChainDocumentLoader()
except Exception:
    sys.exit(1)

# Test 3: Check policy file exists
policy_path = os.path.join(os.path.dirname(__file__), "..", "policy.md")
if os.path.exists(policy_path):
    file_size = os.path.getsize(policy_path)
else:
    sys.exit(1)

# Test 4: Ingest policies
try:
    from ai.ingest_policies import ingest_policy_document

    success = ingest_policy_document()
    if success:
        stats = vs.get_collection_stats()
    else:
        sys.exit(1)
except Exception:
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 5: Search policies
test_queries = [
    "maximum booking duration",
    "late cancellation policy",
    "how many active bookings",
]

for query in test_queries:
    try:
        results = vs.search_policies(query, n_results=2)
        if results and results.get("documents") and len(results["documents"]) > 0:
            doc_count = len(results["documents"][0])
        else:
            pass
    except Exception:
        pass

# Test 6: Test hybrid retriever
try:
    from ai.hybrid_retriever import HybridRetriever

    retriever = HybridRetriever(vector_store=vs)
    results = retriever.retrieve(
        query="Can I cancel a booking with less than 3 hours notice?", intent="information", top_k=3
    )
    if results:
        pass
except Exception:
    pass
