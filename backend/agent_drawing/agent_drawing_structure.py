"""Agente 2 · Estrutura: peça única ou conjunto.

O MVP cadastra uma peça por desenho. Conjuntos (lista de materiais com vários itens)
ficam para a próxima fase e são devolvidos como fora do escopo.
"""

from typing import Literal

from pydantic import BaseModel, Field

from backend.llm import Perguntar


class Estrutura(BaseModel):
    estrutura: Literal["peca_unica", "conjunto"]
    motivo: str = Field(description="Uma frase curta com a evidência visual usada")


INSTRUCAO = """Você analisa a ESTRUTURA de um desenho técnico mecânico.

Responda "conjunto" se o desenho representar várias peças: lista de materiais (BOM) com mais de
uma linha, vários balões de posição numerados com peças diferentes, vista explodida ou montagem.
Responda "peca_unica" se o desenho detalhar uma só peça, mesmo que tenha várias vistas e cortes
ou um único balão de posição.

Em "motivo", cite em uma frase a evidência visual."""


def analisar_estrutura(imagem, perguntar: Perguntar) -> Estrutura:
    return perguntar(INSTRUCAO, imagem, Estrutura)
