"""O caminho de teste do MVP: o desenho de exemplo vira um cadastro completo."""

import pytest

from backend.agent_drawing.agent_drawing_structure import Estrutura
from backend.agent_drawing.agent_drawing_weight import Geometria
from backend.classifier import Classificacao
from backend.pipeline import analisar
from tests.conftest import ModeloFalso


def cadastro_de(eventos):
    return next(e["cadastro"] for e in eventos if e["evento"] == "cadastro")


def test_desenho_de_exemplo_vira_cadastro(desenho):
    eventos = list(analisar(desenho, ModeloFalso()))
    cadastro = cadastro_de(eventos)

    assert cadastro["numero_desenho"] == "MT-2026-0117"
    assert cadastro["revisao"] == "0"
    assert cadastro["denominacao"] == "EIXO DE TRANSMISSÃO"
    assert cadastro["material"] == "AÇO SAE 1045"
    assert cadastro["tipo_item"] == "usinagem"
    assert cadastro["dimensao_principal"] == "Ø60 × 250 mm"
    # π/4 · (40²·50 + 60²·120 + 50²·80) mm³ × 7850 kg/m³ = 4,39 kg
    assert cadastro["peso_kg"] == pytest.approx(4.39)
    assert cadastro["texto_breve"] == "EIXO TRANSMISSAO;ACO SAE 1045;D60X250MM"
    assert cadastro["pendencias"] == ["Conferir peso estimado (sem massa no desenho)"]
    assert eventos[-1]["evento"] == "fim"


def test_cada_agente_acende_e_conclui(desenho):
    eventos = list(analisar(desenho, ModeloFalso()))
    agentes = [a["id"] for a in eventos[0]["agentes"]]
    concluidos = [e["id"] for e in eventos if e["evento"] == "agente" and e["estado"] == "ok"]
    assert sorted(concluidos) == sorted(agentes)
    # classificador e estrutura vêm antes dos cinco agentes paralelos
    assert concluidos[:2] == ["classificador", "estrutura"]


def test_catalogo_fica_fora_do_escopo(desenho):
    modelo = ModeloFalso({Classificacao: Classificacao(tipo_documento="catalogo", motivo="tabela")})
    eventos = list(analisar(desenho, modelo))
    assert any(e["evento"] == "fora_do_escopo" for e in eventos)
    assert not any(e["evento"] == "cadastro" for e in eventos)
    assert modelo.chamadas == [Classificacao]


def test_conjunto_fica_fora_do_escopo(desenho):
    modelo = ModeloFalso({Estrutura: Estrutura(estrutura="conjunto", motivo="BOM com 6 itens")})
    eventos = list(analisar(desenho, modelo))
    assert "conjunto" in next(e["motivo"] for e in eventos if e["evento"] == "fora_do_escopo")
    assert not any(e["evento"] == "cadastro" for e in eventos)


def test_agente_que_falha_vira_pendencia(desenho):
    eventos = list(analisar(desenho, ModeloFalso(falhar=[Geometria])))
    erro = next(e for e in eventos if e.get("id") == "geometria" and e.get("estado") == "erro")
    assert "demorou" in erro["erro"]
    cadastro = cadastro_de(eventos)
    assert cadastro["peso_kg"] is None
    assert "Peso" in cadastro["pendencias"]
    assert cadastro["material"] == "AÇO SAE 1045"  # os outros agentes seguem valendo


def test_classificador_que_falha_encerra_sem_cadastro(desenho):
    eventos = list(analisar(desenho, ModeloFalso(falhar=[Classificacao])))
    assert eventos[-1]["evento"] == "fim"
    assert not any(e["evento"] == "cadastro" for e in eventos)
