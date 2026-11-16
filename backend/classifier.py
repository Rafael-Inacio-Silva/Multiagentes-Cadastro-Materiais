"""Agente 1 · Classificador: decide se a entrada é um desenho técnico.

No MVP só o caminho "desenho técnico" segue adiante; catálogo e outros documentos param aqui.
"""

from typing import Literal

from pydantic import BaseModel, Field

from backend.llm import Perguntar


class Classificacao(BaseModel):
    tipo_documento: Literal["desenho_tecnico", "catalogo", "outro"]
    motivo: str = Field(description="Uma frase curta com a evidência visual usada")


INSTRUCAO = """Você classifica documentos de engenharia recebidos pelo setor de cadastro de materiais.

Responda "desenho_tecnico" quando houver vistas ortogonais ou cortes, linhas de cota, símbolos
de diâmetro (Ø), tolerâncias, rugosidade ou um carimbo/legenda com denominação e número do desenho.
Responda "catalogo" quando for página de catálogo de fornecedor: tabelas de modelos, códigos e
especificações. Responda "outro" para qualquer outra coisa (foto, texto, planilha, imagem sem relação).

Em "motivo", cite em uma frase o elemento visual que decidiu a classificação."""


def classificar(imagem, perguntar: Perguntar) -> Classificacao:
    return perguntar(INSTRUCAO, imagem, Classificacao)
