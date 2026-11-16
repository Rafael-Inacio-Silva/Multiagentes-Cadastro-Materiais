"""A parte sem IA: volume, peso e texto breve."""

import pytest

from backend.agent_drawing.agent_drawing_weight import Geometria, Trecho
from backend.cadastro import calcular_peso, dimensao_principal, texto_breve
from tests.conftest import RESPOSTAS_DO_EXEMPLO


def trecho(**cotas):
    base = dict(cotas_lidas="", comprimento_mm=100, diametro_mm=None, diametro_interno_mm=None,
                largura_mm=None, altura_mm=None)
    return Trecho(**{**base, **cotas})


def test_peso_do_eixo_de_exemplo():
    peso = calcular_peso(RESPOSTAS_DO_EXEMPLO[Geometria], "aco_carbono")
    assert peso["peso_kg"] == pytest.approx(4.39)
    assert peso["volume_cm3"] == pytest.approx(559.2)


def test_massa_declarada_no_desenho_tem_prioridade():
    geometria = Geometria(massa_declarada_kg=4.441, trechos=[trecho(forma="cilindro", diametro_mm=80)])
    assert calcular_peso(geometria, "aco_carbono") == {"peso_kg": 4.441, "origem": "declarado no desenho"}


def test_tubo_e_prisma_e_densidade_por_familia():
    tubo = Geometria(massa_declarada_kg=None,
                     trechos=[trecho(forma="tubo", diametro_mm=100, diametro_interno_mm=80)])
    assert calcular_peso(tubo, "aco_carbono")["peso_kg"] == pytest.approx(2.22, abs=0.01)
    chapa = Geometria(massa_declarada_kg=None,
                      trechos=[trecho(forma="prisma", comprimento_mm=1000, largura_mm=500, altura_mm=10)])
    assert calcular_peso(chapa, "aluminio")["peso_kg"] == pytest.approx(13.5)


def test_cota_faltando_nao_inventa_peso():
    geometria = Geometria(massa_declarada_kg=None, trechos=[trecho(forma="cilindro")])
    assert calcular_peso(geometria, "aco_carbono") is None


def test_texto_breve_respeita_40_caracteres():
    texto = texto_breve("FLANGE DE ACOPLAMENTO DA BOMBA CENTRÍFUGA", "AÇO INOX AISI 316L", "Ø320 × 45 mm")
    assert len(texto) <= 40
    assert texto.startswith("FLANGE ACOPLAMENTO BOMBA CENTRIFUGA")


def test_dimensao_principal_de_eixo():
    assert dimensao_principal(RESPOSTAS_DO_EXEMPLO[Geometria]) == "Ø60 × 250 mm"
