from typing import TypedDict, Optional


class GraphState(TypedDict):
    input: str
    task: Optional[str]
    response: str