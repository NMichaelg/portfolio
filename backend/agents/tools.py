from pathlib import Path


from langchain.tools import tool
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# RAG on resume Start

HEADER_TO_SPLIT = [
    ("#", "h1"),
    ("##", "h2"),
    ("###", "h3")
]
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHROMA_PERSIST_DIRECTORY = Path(__file__).parent.parent/'db'/'chroma_store'
TOP_K = 3
RESUME_PATH = Path(__file__).resolve().parent.parent.parent / \
    "local_info" / "resume-no-password.md"

_embedding: HuggingFaceEmbeddings | None = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding
    if _embedding is None:
        _embedding = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embedding


def read_and_format_resume(resume_path):
    docs = ''
    with open(resume_path, "r") as f:
        resume_text = f.read()

        text_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=HEADER_TO_SPLIT,
            strip_headers=False
        )
        docs = text_splitter.split_text(resume_text)
    return docs


def vector_store_embedding(force_rebuilt: bool = False) -> Chroma:
    embedding = get_embedding_model()

    # Store the embeddings in the vector store
    vector_store = Chroma(
        collection_name="resume",
        embedding_function=embedding,
        persist_directory=str(CHROMA_PERSIST_DIRECTORY)
    )

    existing_count = 0

    if existing_count == 0 and force_rebuilt:
        vector_store.delete_collection()
        vector_store = Chroma(
            collection_name="resume",
            embedding_function=embedding,
            persist_directory=str(CHROMA_PERSIST_DIRECTORY)
        )

    if existing_count == 0:
        docs = read_and_format_resume(RESUME_PATH)
        vector_store.add_documents(docs)

    return vector_store


_vector_store = vector_store_embedding(force_rebuilt=False)


@tool
def search_resume(query: str) -> str:
    """
    Search Michael (Ân Nguyễn)'s resume knowledge base for information,elevant to the user's question
    - experience, skills, education, certifications, projects, or contact info.

    Use this any time the user asks about Michael's background, work history, technical skills, 
    or qualifications that isn't already established in the conversation.

    Args:
        query: The user's question or topic, e.g. "What AI frameworks
               does he use?" or "Tell me about his homelab."

    Returns:
            The most relevant resume section(s) as plain text, or a message
            indicating nothing relevant was found.

    """

    results = _vector_store.similarity_search(query, k=TOP_K)

    if not results:
        return (
            "NOT_FOUND: nothing relevant in the knowledge base. "
            "Tell the user you're not sure and offer to connect them via email."
        )

    chunks = []
    for doc in results:
        header_path = " > ".join(
            v for k, v in doc.metadata.items() if k in ("h1", "h2", "h3")
        )
        text = doc.page_content.strip()
        chunks.append(f"{header_path}\n{text}" if header_path else text)

    return "\n\n---\n\n".join(chunks)


# RAG on resume End
