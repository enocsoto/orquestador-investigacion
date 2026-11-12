import json
import os

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from state import OrchestratorState

UMBRAL = 4000


@tool
def calcular_ticket_promedio(total: float, cantidad: int) -> str:
    """Calcula el ticket promedio (total / cantidad) y dice si supera 4000.

    Usala cuando ya tengas el total y la cantidad que trajo la investigación.
    No busques clientes: si falta un número, devolvé el error y pedí el dato.
    cantidad tiene que ser mayor que cero.
    """
    if cantidad < 1 or total < 0:
        return json.dumps(
            {
                "error": "Datos insuficientes",
                "sugerencia": "Hace falta un total >= 0 y una cantidad >= 1. Volvé a investigación.",
            },
            ensure_ascii=False,
        )
    promedio = round(total / cantidad, 2)
    return json.dumps(
        {
            "total": total,
            "cantidad": cantidad,
            "ticket_promedio": promedio,
            "supera_4000": promedio > UMBRAL,
        },
        ensure_ascii=False,
    )


async def analyst_node(state: OrchestratorState) -> dict:
    """Ve la pregunta y el hallazgo. No ve el historial completo del supervisor."""
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=os.environ["OPENAI_API_KEY"])
    agent = create_react_agent(
        model,
        [calcular_ticket_promedio],
        prompt=(
            "Sos el analista. Con el total y la cantidad del hallazgo, llamá "
            "calcular_ticket_promedio. No busques clientes. Si el hallazgo no trae "
            "números, devolvé que falta el dato y no inventes."
        ),
    )
    question = ""
    for message in reversed(state["messages"]):
        if message.type == "human":
            question = str(message.content)
            break
    brief = f"Pregunta: {question}\nHallazgo de investigación:\n{state.get('findings', '')}"
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=brief)]},
        config={"recursion_limit": 6},
    )
    text = str(result["messages"][-1].content)
    return {
        "analysis": text,
        "messages": [AIMessage(content=text, name="analyst")],
    }
