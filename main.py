import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from graph import build_graph

ROOT = Path(__file__).resolve().parent
TRACE = ROOT / "traces" / "delegacion.json"
QUESTION = (
    "Investigá cuántos pedidos tuvo el cliente 102 y el total, "
    "y decime si el ticket promedio supera 4000."
)


def _brief(message) -> dict:
    payload = {"type": message.type, "name": getattr(message, "name", None), "content": message.content}
    return payload


async def main() -> None:
    load_dotenv(ROOT / ".env")
    app = build_graph()
    result = await app.ainvoke(
        {
            "messages": [HumanMessage(content=QUESTION)],
            "next_agent": "research",
            "task_completed": False,
            "steps": 0,
            "findings": "",
            "analysis": "",
        },
        config={"recursion_limit": 12},
    )
    for message in result["messages"]:
        who = getattr(message, "name", None) or message.type
        print(f"[{who}] {message.content}")
        print("-" * 40)
    TRACE.parent.mkdir(parents=True, exist_ok=True)
    TRACE.write_text(
        json.dumps(
            {
                "pregunta": QUESTION,
                "task_completed": result["task_completed"],
                "steps": result["steps"],
                "findings": result["findings"],
                "analysis": result["analysis"],
                "mensajes": [_brief(message) for message in result["messages"]],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Traza escrita en {TRACE}")


if __name__ == "__main__":
    asyncio.run(main())
