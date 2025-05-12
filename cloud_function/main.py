import os

import functions_framework
import vertexai
from cloudevents.http import CloudEvent
from google import auth
from vertexai import rag

_, project_id = auth.default()

rag_corpus_name = os.getenv("RAG_CORPUS_NAME")
region = "europe-west3"
EMBEDDING_MODEL = "text-embedding-005"

vertexai.init(project=project_id, location=region)


# This function processes Audit Log event for storage.object.create
@functions_framework.cloud_event
def main(cloud_event: CloudEvent) -> None:
    data = cloud_event.data
    bucket = data["bucket"]
    file_name = data["name"]
    file_path = f"gs://{bucket}/{file_name}"
    embedding_model_config = rag.RagEmbeddingModelConfig(
        vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
            publisher_model=f"publishers/google/models/{EMBEDDING_MODEL}"
        )
    )

    backend_config = rag.RagVectorDbConfig(
        rag_embedding_model_config=embedding_model_config
    )

    corpus_exists = False
    for corpus in rag.list_corpora():
        if corpus.display_name == rag_corpus_name:
            corpus_exists = True
            rag_corpus = corpus
    if not corpus_exists:
        rag_corpus = rag.create_corpus(
            display_name=rag_corpus_name,
            backend_config=backend_config,
        )

    transformation_config = rag.TransformationConfig(
        chunking_config=rag.ChunkingConfig(
            chunk_size=1024,
            chunk_overlap=100,
        ),
    )

    print(
        rag.import_files(
            rag_corpus.name,
            paths=[file_path],
            transformation_config=transformation_config,
        )
    )
