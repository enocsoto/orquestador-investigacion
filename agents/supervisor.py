import os
from typing import Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from state import OrchestratorState

MAX_STEPS = 6
RouteName = Literal["research", "analyst", "finish"]


class Decision(BaseModel):
    next_agent: RouteName = Field(
        description="research si falta el dato crudo, analyst si falta el cálculo, finish si ya están los dos"
    )
    reason: str = Field(description="Una frase: por qué ese nodo")


def apply_stop(choice: RouteName, findings: str, analysis: str, steps: int) -> RouteName:
    """Tope de pasos y rúbrica de suficiencia. El modelo propone; esto impide el bucle."""
    if steps >= MAX_STEPS:
        return "finish"
    if choice == "finish" and not findings.strip():
        return "research"
    if choice == "finish" and not analysis.strip():
        return "analyst"
    return choice


def route(state: OrchestratorState) -> RouteName:
    return state["next_agent"]


async def supervisor_node(state: OrchestratorState) -> dict:
    steps = int(state.get("steps", 0)) + 1
    findings = state.get("findings", "")
    analysis = state.get("analysis", "")
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.environ["OPENAI_API_KEY"])
    structured = model.with_structured_output(Decision)
    decision = await structured.ainvoke(
        [
            SystemMessage(
                content=(
                    "Sos el supervisor. No respondas al usuario. Elegí un solo nodo. "
                    "Rúbrica: finish solo si hay un hallazgo con pedidos y total, y un análisis "
                    "con el ticket promedio. Si falta el dato crudo, research. "
                    "Si el dato está y falta el cálculo, o el análisis dice que faltan números, analyst. "
                    "Si el análisis dice que la investigación vino vacía, research una vez más. "
                    "No mandes al mismo especialista si su campo ya está completo."
                )
            ),
            SystemMessage(
                content=(
                    f"pasos={steps}\n"
                    f"hallazgo={findings or '(vacío)'}\n"
                    f"analisis={analysis or '(vacío)'}"
                )
            ),
        ]
    )
    nxt = apply_stop(decision.next_agent, findings, analysis, steps)
    return {
        "next_agent": nxt,
        "steps": steps,
        "task_completed": nxt == "finish",
        "messages": [AIMessage(content=f"{decision.reason} -> {nxt}", name="supervisor")],
    }
