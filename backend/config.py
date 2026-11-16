"""Configuração lida do ambiente (.env na raiz do projeto)."""

import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

MODELO = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
# Esforço de raciocínio dos modelos gpt-5.x/gpt-6.x. Vazio = não enviar o parâmetro.
ESFORCO = os.getenv("OPENAI_REASONING_EFFORT", "low").strip()

PASTA_EXEMPLO = RAIZ / "data" / "exemplo"
PASTA_FRONTEND = RAIZ / "frontend"
EXECUCAO_GRAVADA = PASTA_EXEMPLO / "execucao.json"

TAMANHO_MAXIMO_BYTES = 8 * 1024 * 1024


def tem_chave() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))
