import json
import os

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from state import OrchestratorState

PEDIDOS: dict[int, dict] = {
    102: {"pedidos": 3, "total": 14500, "ultimo": "P-102-3 teclado, 2026-03-18"},
}


@tool
def buscar_fuente(cliente_id: int) -> str:
    """Busca en la base interna cuántos pedidos tuvo un cliente y cuál fue el total.

    Usala solo para traer el dato crudo. No calcula promedios ni decide si el
    ticket es alto: eso lo hace el analista. Si el cliente no existe, devuelve
    un error para que no inventes el número.
    """
    fila = PEDIDOS.get(cliente_id)
    if fila is None:
        return json.dumps(
            {
                "error": "Cliente no encontrado",
                "cliente_id": cliente_id,
                "sugerencia": "Pedí que confirmen el id. No reintentes el mismo.",
            },
            ensure_ascii=False,
        )
    return json.dumps({"cliente_id": cliente_id, **fila}, ensure_ascii=False)


def _last_human(state: OrchestratorState) -> str:
    for message in reversed(state["messages"]):
        if message.type == "human":
            return str(message.content)
    return ""


async def research_node(state: OrchestratorState) -> dict:
    """Solo ve la pregunta del usuario. No recibe el análisis ni el prompt del supervisor."""
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.environ["OPENAI_API_KEY"])
    agent = create_react_agent(
        model,
        [buscar_fuente],
        prompt=(
            "Sos el investigador. Usá buscar_fuente para el cliente que pidan. "
            "No calcules promedios. Si la herramienta devuelve error, no inventes el dato: "
            "decilo en una frase."
        ),
    )
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=_last_human(state))]},
        config={"recursion_limit": 6},
    )
    text = str(result["messages"][-1].content)
    return {
        "findings": text,
        "messages": [AIMessage(content=text, name="research")],
    }
