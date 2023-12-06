import pinecone


def init_pinecone(environment, api_key):
    pinecone.init(environment=environment, api_key=api_key)


def upsert_document(index_name, vector_id, document_title_embedding, document_content, variables):
    index = pinecone.Index(index_name)
    metadata = {
        "data": document_content,
    }
    for variable in variables:
        metadata[variable["name"]] = variable["value"]
    try:
        index.upsert(
            vectors=[
                (
                    vector_id,
                    document_title_embedding,
                    metadata
                )
            ]
        )
    except Exception as e:
        print(e)


def similarity_search(index_name, query_embedding, ids):
    index = pinecone.Index(index_name)
    response = index.query(
        top_k=1,
        include_values=False,
        include_metadata=True,
        vector=query_embedding
    )
    matches = response["matches"]
    print(matches)
    score = matches[0]["score"]
    if score < 0.7:
        return None
    return matches[0]["metadata"]
