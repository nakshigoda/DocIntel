import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.database import documents_collection
from app.services.vector_service import total_chunk_count

docs = list(documents_collection.find({}, {
    '_id': 0, 'document_id': 1, 'filename': 1,
    'status': 1, 'page_count': 1, 'chunk_count': 1
}))
print(f"MongoDB docs: {len(docs)}")
for d in docs:
    st = d.get('status', '?')
    fn = d.get('filename', '?')
    pg = d.get('page_count', 0)
    ck = d.get('chunk_count', 0)
    did = d.get('document_id', '?')
    print(f"  [{st}] {fn}  pages={pg} chunks={ck}  id={did[:8]}...")

print(f"ChromaDB total chunks: {total_chunk_count()}")
