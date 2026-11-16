"""Respostas fixas no lugar do modelo: os testes rodam sem rede e sem chave."""

import pytest
from PIL import Image

from backend import config
from backend.agent_drawing.agent_drawing_material import Material
from backend.agent_drawing.agent_drawing_name import NomePeca
from backend.agent_drawing.agent_drawing_number import NumeroDesenho
from backend.agent_drawing.agent_drawing_structure import Estrutura
from backend.agent_drawing.agent_drawing_tipo_item import Tipo
from backend.agent_drawing.agent_drawing_weight import Geometria, Trecho
from backend.classifier import Classificacao


def cilindro(cota: str, diametro: float, comprimento: float) -> Trecho:
    return Trecho(cotas_lidas=cota, forma="cilindro", comprimento_mm=comprimento, diametro_mm=diametro,
                  diametro_interno_mm=None, largura_mm=None, altura_mm=None)


# o que um modelo correto responde para data/exemplo/eixo-transmissao.png
RESPOSTAS_DO_EXEMPLO = {
    Classificacao: Classificacao(tipo_documento="desenho_tecnico", motivo="cotas e carimbo"),
    Estrutura: Estrutura(estrutura="peca_unica", motivo="um único balão"),
    NumeroDesenho: NumeroDesenho(numero_desenho="MT-2026-0117", revisao="0"),
    NomePeca: NomePeca(nome_peca="EIXO DE TRANSMISSÃO"),
    Material: Material(material="AÇO SAE 1045", familia="aco_carbono"),
    Tipo: Tipo(tipo_item="usinagem", motivo="peça usinada de barra"),
    Geometria: Geometria(massa_declarada_kg=None, trechos=[
        cilindro("Ø40 k6 · 50", 40, 50), cilindro("Ø60 · 120", 60, 120), cilindro("Ø50 h7 · 80", 50, 80),
    ]),
}


class ModeloFalso:
    def __init__(self, respostas=None, falhar=()):
        self.respostas = {**RESPOSTAS_DO_EXEMPLO, **(respostas or {})}
        self.falhar = set(falhar)
        self.chamadas = []

    def __call__(self, instrucao, imagem, esquema):
        self.chamadas.append(esquema)
        if esquema in self.falhar:
            raise TimeoutError("o modelo demorou demais")
        return self.respostas[esquema]


@pytest.fixture
def desenho():
    return Image.open(config.PASTA_EXEMPLO / "eixo-transmissao.png")
