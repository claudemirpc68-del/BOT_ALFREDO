"""
Módulo de fila de tarefas para comunicação entre o BOT_ALFREDO (nuvem/Coolify)
e o agente local (PC Windows).
"""

import time
import asyncio
import logging

logger = logging.getLogger(__name__)

PENDING_TASKS: dict[str, dict] = {}
COMPLETED_RESULTS: dict[str, str] = {}


def criar_tarefa(command: str, args: list[str] = None) -> str:
    """Cria uma tarefa pendente para o agente local executar."""
    task_id = f"task_{int(time.time() * 1000)}"
    PENDING_TASKS[task_id] = {
        "id": task_id,
        "command": command,
        "args": args or [],
        "created_at": time.time(),
        "status": "pending",
    }
    logger.info(f"Tarefa criada na fila: {task_id} ({command})")
    return task_id


def obter_proxima_tarefa() -> dict | None:
    """Retorna a próxima tarefa pendente para o agente local (se houver)."""
    agora = time.time()
    for task_id, task in list(PENDING_TASKS.items()):
        # Expira tarefas com mais de 60 segundos
        if agora - task["created_at"] > 60:
            PENDING_TASKS.pop(task_id, None)
            continue
        if task["status"] == "pending":
            task["status"] = "assigned"
            return task
    return None


def registrar_resultado(task_id: str, output: str) -> bool:
    """Registra o resultado retornado pelo agente local."""
    if task_id in PENDING_TASKS:
        COMPLETED_RESULTS[task_id] = output
        PENDING_TASKS.pop(task_id, None)
        logger.info(f"Resultado registrado para tarefa: {task_id}")
        return True
    return False


async def aguardar_resultado(task_id: str, timeout_segundos: float = 25.0) -> str | None:
    """Aguarda assincronamente até que o resultado da tarefa seja preenchido ou expire."""
    inicio = time.time()
    while time.time() - inicio < timeout_segundos:
        if task_id in COMPLETED_RESULTS:
            return COMPLETED_RESULTS.pop(task_id)
        await asyncio.sleep(0.5)
    # Se expirou
    PENDING_TASKS.pop(task_id, None)
    return None
