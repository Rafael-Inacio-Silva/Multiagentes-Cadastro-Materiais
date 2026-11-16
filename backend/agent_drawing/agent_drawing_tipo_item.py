"""Agente 6 · Tipo de item: o processo de fabricação que define a classe de cadastro."""

from typing import Literal

from pydantic import BaseModel, Field

from backend.llm import Perguntar

TipoItem = Literal[
    "usinagem",
    "caldeiraria",
    "fundido_ferroso",
    "fundido_nao_ferroso",
    "nao_metalico",
    "metalico_com_revestimento_nao_metalico",
]


class Tipo(BaseModel):
    tipo_item: TipoItem
    motivo: str = Field(description="Uma frase curta com a evidência usada")


INSTRUCAO = """Classifique o TIPO DE ITEM deste desenho técnico em uma categoria:

- fundido_ferroso: peça fundida em ferro ou aço fundido (GG, GGG, nodular, "fundido").
- fundido_nao_ferroso: peça fundida em alumínio, bronze, latão ou zamac.
- caldeiraria: fabricada de chapas, perfis ou tubos cortados, dobrados e soldados.
- nao_metalico: material base não metálico (borracha, PU, nylon, PTFE, PEAD, cerâmica).
- metalico_com_revestimento_nao_metalico: base metálica com revestimento ou forração não metálica.
- usinagem: predominantemente usinada (torno, fresa, furos, roscas, tolerâncias, rugosidade).

Prioridade: usinagem é a última opção. Se houver evidência de fundição ou caldeiraria, prefira
essas. Em "motivo", cite a evidência em uma frase."""


def classificar_tipo(imagem, perguntar: Perguntar) -> Tipo:
    return perguntar(INSTRUCAO, imagem, Tipo)
