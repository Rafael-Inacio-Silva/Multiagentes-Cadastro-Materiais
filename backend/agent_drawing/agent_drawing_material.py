"""Agente 5 · Material (matéria-prima) e família do material."""

from typing import Literal

from pydantic import BaseModel, Field

from backend.llm import Perguntar

Familia = Literal[
    "aco_carbono", "aco_inox", "ferro_fundido", "aluminio", "bronze_latao", "polimero", "outro"
]


class Material(BaseModel):
    material: str | None = Field(
        description="Especificação do material, sem forma do bruto. Ex.: 'AÇO SAE 1045'. Ou null"
    )
    familia: Familia | None = Field(description="Família usada para escolher a densidade")


INSTRUCAO = """Leia o campo MATERIAL / MATÉRIA-PRIMA do carimbo deste desenho técnico.

material: só a especificação do material, em maiúsculas (ex.: "AÇO SAE 1045", "AÇO INOX AISI 304",
"FERRO FUNDIDO GG25", "ALUMÍNIO 6061-T6"). Tire a forma do bruto e a bitola, como "BARRA REDONDA Ø65"
ou "CHAPA #10".
familia: aco_carbono (SAE/ABNT/AISI 10xx, 41xx, 86xx, ASTM A36), aco_inox (AISI 3xx/4xx, inox),
ferro_fundido (GG, GGG, nodular, cinzento), aluminio, bronze_latao, polimero (nylon, PTFE, PU,
borracha) ou outro.

Se o material não estiver no desenho, devolva null nos dois campos."""


def extrair_material(imagem, perguntar: Perguntar) -> Material:
    return perguntar(INSTRUCAO, imagem, Material)
