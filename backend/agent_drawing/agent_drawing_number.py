"""Agente 3 · Número do desenho e revisão, lidos do carimbo."""

from pydantic import BaseModel, Field

from backend.llm import Perguntar


class NumeroDesenho(BaseModel):
    numero_desenho: str | None = Field(description="Código do desenho como está no carimbo, ou null")
    revisao: str | None = Field(description="Revisão (REV) como está no carimbo, ou null")


INSTRUCAO = """Leia o CARIMBO (legenda) deste desenho técnico, normalmente no canto inferior direito.

numero_desenho: o código do campo "Nº DO DESENHO", "DESENHO Nº", "DWG NO", "CÓDIGO" ou "PART NO".
Copie exatamente como está escrito, com hífens e barras. Não confunda com escala, folha, data,
quantidade ou norma de material.
revisao: o valor do campo "REV" / "REVISÃO".

Se um campo não estiver legível com segurança, devolva null. Não invente."""


def extrair_numero(imagem, perguntar: Perguntar) -> NumeroDesenho:
    return perguntar(INSTRUCAO, imagem, NumeroDesenho)
