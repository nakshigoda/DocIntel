import faiss
import numpy as np
import pickle
import os

dimension = 384

index = faiss.IndexFlatL2(dimension)

store = []

INDEX_PATH = "faiss.index"
STORE_PATH = "store.pkl"


def add_embeddings(
    embeddings,
    chunks,
    document_id=None
):
    global store

    vectors = np.array(
        embeddings
    ).astype("float32")

    index.add(vectors)

    for chunk in chunks:
        store.append(
            {
                "text": chunk,
                "document_id": document_id
            }
        )

    save()


def save():
    faiss.write_index(
        index,
        INDEX_PATH
    )

    with open(
        STORE_PATH,
        "wb"
    ) as f:
        pickle.dump(
            store,
            f
        )


def load_index():
    global index, store

    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(
            INDEX_PATH
        )

    if os.path.exists(STORE_PATH):
        with open(
            STORE_PATH,
            "rb"
        ) as f:
            store = pickle.load(f)


def search(
    query_vector,
    k=20,
    document_id="all"
):
    vector = np.array(
        [query_vector]
    ).astype("float32")

    distances, indices = index.search(
        vector,
        k
    )

    results = []

    for i in indices[0]:

        if i >= len(store):
            continue

        chunk = store[i]

        if (
            document_id != "all"
            and chunk.get("document_id")
            != document_id
        ):
            continue

        results.append(chunk)
    # print("\nReturned chunks:")
    # for chunk in results:
    #     print(chunk["document_id"])
    return results[:5]