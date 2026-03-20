from typing import TypedDict, Optional, List


class GraphState(TypedDict):
    input: str
    task: Optional[str]
    query_embedding: Optional[List[float]]
    raw_docs: Optional[List[str]]
    chunks: Optional[List[str]]
    context: Optional[str]
    prompt: Optional[str]
    response: str
    attempts: int
    is_valid: bool
