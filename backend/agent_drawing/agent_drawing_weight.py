"""Agente 7 · Geometria para o peso.

A IA só LÊ o desenho: decompõe a peça em trechos simples com as cotas em mm e informa a massa
se o desenho a declarar. A conta (volume × densidade) é feita em Python, em backend/cadastro.py,
porque aritmética não é tarefa para o modelo.
"""

from typing import Literal

from pydantic import BaseModel, Field

from backend.llm import Perguntar


class Trecho(BaseModel):
    cotas_lidas: str = Field(
        description="Cotas deste trecho copiadas como aparecem no desenho, ex.: 'Ø40 k6 · 50'"
    )
    forma: Literal["cilindro", "tubo", "prisma"]
    comprimento_mm: float = Field(description="Comprimento axial do trecho, em mm")
    diametro_mm: float | None = Field(description="Diâmetro externo (cilindro e tubo), em mm")
    diametro_interno_mm: float | None = Field(description="Diâmetro interno (só tubo), em mm")
    largura_mm: float | None = Field(description="Largura (só prisma), em mm")
    altura_mm: float | None = Field(description="Altura (só prisma), em mm")


class Geometria(BaseModel):
    massa_declarada_kg: float | None = Field(
        description="Massa escrita no desenho (MASSA, PESO), em kg, ou null se não houver"
    )
    trechos: list[Trecho] = Field(description="Trechos que, somados, formam a peça")


INSTRUCAO = """Você lê as COTAS de um desenho técnico para estimar o volume da peça.

1. Se o desenho declarar a massa ("MASSA", "PESO", "kg"), copie em massa_declarada_kg. Senão, null.
2. Decomponha a peça em trechos simples, na ordem em que aparecem:
   - cilindro: diametro_mm e comprimento_mm (eixos escalonados: um cilindro por diâmetro).
   - tubo: diametro_mm, diametro_interno_mm e comprimento_mm (buchas, anéis).
   - prisma: largura_mm, altura_mm e comprimento_mm (blocos, chapas).
   Antes de preencher os números, copie em cotas_lidas o texto das cotas do trecho exatamente
   como está escrito (cotas de diâmetro podem estar na vertical, giradas 90°).
   Use as cotas parciais de comprimento de cada trecho; confira se a soma bate com a cota total.
   Ignore chanfros, raios, rasgos de chaveta e furos pequenos: são detalhes de pouco volume.
   Ignore a classe de tolerância (k6, h7, g6) e use só o valor nominal: "Ø40 k6" é 40 mm.
3. Campos que não se aplicam à forma ficam null. Não faça contas de volume nem de peso."""


def extrair_geometria(imagem, perguntar: Perguntar) -> Geometria:
    return perguntar(INSTRUCAO, imagem, Geometria)
