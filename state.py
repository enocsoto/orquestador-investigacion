from typing import Literal

from langgraph.graph import MessagesState


class OrchestratorState(MessagesState):
    """Historial compartido más el aporte de cada especialista.

    messages acumula con add_messages. El resto lo pisa el nodo que escribe,
    así el supervisor lee el último hallazgo y el último análisis, no una mezcla.
    """

    next_agent: Literal["research", "analyst", "finish"]
    task_completed: bool
    steps: int
    findings: str
    analysis: str
