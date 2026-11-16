"""Agente 4 · Nome (denominação) da peça, lido do carimbo."""

from pydantic import BaseModel, Field

from backend.llm import Perguntar


class NomePeca(BaseModel):
    nome_peca: str | None = Field(description="Denominação da peça em maiúsculas, ou null")


INSTRUCAO = """Leia o CARIMBO (legenda) deste desenho técnico e devolva a DENOMINAÇÃO da peça.

Procure os campos "DENOMINAÇÃO", "DESCRIÇÃO", "NOME", "PEÇA", "TÍTULO", "TITLE" ou "PART NAME".
A denominação é uma expressão como "EIXO DE TRANSMISSÃO", "FLANGE CEGO" ou "SUPORTE", nunca um
código. Devolva em MAIÚSCULAS, mantendo acentos. Se não houver com segurança, devolva null."""


def extrair_nome(imagem, perguntar: Perguntar) -> NomePeca:
    return perguntar(INSTRUCAO, imagem, NomePeca)
