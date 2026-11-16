"""A API serve a tela, aceita só imagens e repete a execução gravada."""

import json

import pytest
from fastapi.testclient import TestClient

from backend import config, llm
from backend.main import app
from tests.conftest import ModeloFalso


@pytest.fixture
def cliente():
    app.state.perguntar = ModeloFalso()
    yield TestClient(app)
    app.state.perguntar = llm.perguntar


def eventos(resposta):
    return [json.loads(linha) for linha in resposta.text.splitlines() if linha]


def test_tela_e_estado(cliente):
    assert "Cadastro Técnico" in cliente.get("/").text
    assert cliente.get("/api/estado").json()["ao_vivo"] is True


def test_envio_de_desenho(cliente):
    png = (config.PASTA_EXEMPLO / "eixo-transmissao.png").read_bytes()
    resposta = cliente.post("/api/analisar", files={"arquivo": ("eixo.png", png, "image/png")})
    assert resposta.status_code == 200
    assert eventos(resposta)[-2]["cadastro"]["numero_desenho"] == "MT-2026-0117"


def test_recusa_o_que_nao_e_imagem(cliente):
    resposta = cliente.post("/api/analisar", files={"arquivo": ("a.pdf", b"%PDF-1.4", "application/pdf")})
    assert resposta.status_code == 415


def test_execucao_gravada_e_real_e_completa(cliente):
    resposta = cliente.get("/api/exemplo", params={"gravado": 1, "velocidade": 1000})
    lista = eventos(resposta)
    assert lista[0]["gravado"] is True
    cadastro = next(e["cadastro"] for e in lista if e["evento"] == "cadastro")
    assert cadastro["peso_kg"] == pytest.approx(4.39)
    assert lista[-1]["evento"] == "fim"


def test_sem_chave_o_envio_e_recusado(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    resposta = TestClient(app).post("/api/analisar", files={"arquivo": ("e.png", b"x", "image/png")})
    assert resposta.status_code == 503
