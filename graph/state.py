from typing import TypedDict, Optional, List


class GraphState(TypedDict):
    input: str                                  # input para almacenar la entrada
    task: Optional[str]                         # task para almacenar la tarea
    query_embedding: Optional[List[float]]      # query_embedding para almacenar el embedding de la consulta
    raw_docs: Optional[List[str]]               # raw_docs para almacenar los documentos sin procesar
    chunks: Optional[List[str]]                 # chunks para almacenar los chunks
    context: Optional[str]                      # context para almacenar el contexto    
    prompt: Optional[str]                       # prompt para almacenar el prompt
    response: str                               # response para almacenar la respuesta
    attempts: int                               # attempts para controlar los intentos  
    is_valid: bool                              # is_valid para controlar la validez de la respuesta
