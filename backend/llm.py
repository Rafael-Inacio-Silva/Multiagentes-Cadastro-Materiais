"""Uma única porta para o modelo de visão.

Todo agente faz a mesma coisa: manda a imagem do desenho + uma instrução curta e recebe
um objeto Pydantic já validado (Structured Outputs da OpenAI). Os agentes recebem esta
função por parâmetro, então os testes trocam o modelo por respostas fixas.
"""

from __future__ import annotations

import base64
import io
from typing import Callable, TypeVar

from PIL import Image
from pydantic import BaseModel

from backend import config

T = TypeVar("T", bound=BaseModel)

# assinatura que todo agente espera: (instrução, imagem, esquema) -> objeto validado
Perguntar = Callable[[str, Image.Image, type[T]], T]

LADO_MAXIMO_PX = 2000

_cliente = None


def _openai():
    global _cliente
    if _cliente is None:
        from openai import OpenAI

        _cliente = OpenAI(timeout=120, max_retries=2)
    return _cliente


def preparar_imagem(imagem: Image.Image) -> Image.Image:
    """RGB e no máximo 2000 px no lado maior: o carimbo continua legível e o custo cai."""
    imagem = imagem.convert("RGB")
    if max(imagem.size) > LADO_MAXIMO_PX:
        imagem.thumbnail((LADO_MAXIMO_PX, LADO_MAXIMO_PX))
    return imagem


def _como_data_url(imagem: Image.Image) -> str:
    buffer = io.BytesIO()
    imagem.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def perguntar(instrucao: str, imagem: Image.Image, esquema: type[T]) -> T:
    extras = {"reasoning": {"effort": config.ESFORCO}} if config.ESFORCO else {}
    resposta = _openai().responses.parse(
        model=config.MODELO,
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": instrucao},
                    {"type": "input_image", "image_url": _como_data_url(imagem), "detail": "high"},
                ],
            }
        ],
        text_format=esquema,
        **extras,
    )
    if resposta.output_parsed is None:
        raise RuntimeError("o modelo não devolveu uma resposta no formato esperado")
    return resposta.output_parsed
