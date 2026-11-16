"""Orquestração: o único caminho do MVP (desenho técnico de peça única).

    classificador → estrutura → [nº do desenho | denominação | material | tipo | geometria] → cadastro
                                 └──────────── cinco agentes em paralelo ────────────┘

O pipeline é um gerador de eventos: a API repassa cada evento ao navegador assim que ele
acontece, e a tela acende o cartão de cada agente em tempo real.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterator

from backend import config, llm
from backend.agent_drawing import (
    analisar_estrutura,
    classificar_tipo,
    extrair_geometria,
    extrair_material,
    extrair_nome,
    extrair_numero,
)
from backend.cadastro import ROTULO_TIPO, montar_cadastro
from backend.classifier import classificar

AGENTES = [
    {"id": "classificador", "nome": "Classificador", "papel": "É um desenho técnico?", "ia": True},
    {"id": "estrutura", "nome": "Estrutura", "papel": "Peça única ou conjunto", "ia": True},
    {"id": "numero", "nome": "Nº do desenho", "papel": "Código e revisão do carimbo", "ia": True},
    {"id": "nome", "nome": "Denominação", "papel": "Nome da peça no carimbo", "ia": True},
    {"id": "material", "nome": "Material", "papel": "Especificação e família", "ia": True},
    {"id": "tipo", "nome": "Tipo de item", "papel": "Processo de fabricação", "ia": True},
    {"id": "geometria", "nome": "Geometria", "papel": "Trechos e cotas para o peso", "ia": True},
    {"id": "cadastro", "nome": "Cadastro", "papel": "Peso, texto breve e pendências", "ia": False},
]

PARALELOS = {
    "numero": extrair_numero,
    "nome": extrair_nome,
    "material": extrair_material,
    "tipo": classificar_tipo,
    "geometria": extrair_geometria,
}

_DOCUMENTO = {"desenho_tecnico": "Desenho técnico", "catalogo": "Catálogo", "outro": "Outro documento"}

RESUMO: dict[str, Callable] = {
    "classificador": lambda r: _DOCUMENTO[r.tipo_documento],
    "estrutura": lambda r: "Peça única" if r.estrutura == "peca_unica" else "Conjunto",
    "numero": lambda r: " · rev ".join(v for v in (r.numero_desenho, r.revisao) if v) or "não encontrado",
    "nome": lambda r: r.nome_peca or "não encontrado",
    "material": lambda r: r.material or "não encontrado",
    "tipo": lambda r: ROTULO_TIPO[r.tipo_item],
    "geometria": lambda r: (
        f"massa declarada: {r.massa_declarada_kg:g} kg" if r.massa_declarada_kg
        else f"{len(r.trechos)} trecho{'s' if len(r.trechos) != 1 else ''} lido{'s' if len(r.trechos) != 1 else ''}"
    ),
}


class _Interrompido(Exception):
    pass


def _ms(inicio: float) -> int:
    return round((time.perf_counter() - inicio) * 1000)


def _ok(agente: str, resultado, inicio: float) -> dict:
    return {
        "evento": "agente", "id": agente, "estado": "ok", "ms": _ms(inicio),
        "resumo": RESUMO[agente](resultado), "resultado": resultado.model_dump(),
    }


def _erro(agente: str, erro: Exception, inicio: float) -> dict:
    return {"evento": "agente", "id": agente, "estado": "erro", "ms": _ms(inicio), "erro": str(erro)}


def _sequencial(agente: str, funcao: Callable, imagem, perguntar) -> Iterator[dict]:
    yield {"evento": "agente", "id": agente, "estado": "rodando"}
    inicio = time.perf_counter()
    try:
        resultado = funcao(imagem, perguntar)
    except Exception as erro:  # noqa: BLE001 - qualquer falha do agente vira evento na tela
        yield _erro(agente, erro, inicio)
        raise _Interrompido from erro
    yield _ok(agente, resultado, inicio)
    return resultado


def analisar(imagem, perguntar: llm.Perguntar = llm.perguntar) -> Iterator[dict]:
    inicio_total = time.perf_counter()
    imagem = llm.preparar_imagem(imagem)
    yield {"evento": "inicio", "agentes": AGENTES, "modelo": config.MODELO}

    try:
        classificacao = yield from _sequencial("classificador", classificar, imagem, perguntar)
        if classificacao.tipo_documento != "desenho_tecnico":
            yield {"evento": "fora_do_escopo", "motivo":
                   f"O classificador identificou {_DOCUMENTO[classificacao.tipo_documento].lower()}. "
                   "Este MVP cadastra apenas desenhos técnicos."}
            yield {"evento": "fim", "ms": _ms(inicio_total)}
            return

        estrutura = yield from _sequencial("estrutura", analisar_estrutura, imagem, perguntar)
        if estrutura.estrutura != "peca_unica":
            yield {"evento": "fora_do_escopo", "motivo":
                   "O desenho é um conjunto com várias peças. Este MVP cadastra uma peça por desenho."}
            yield {"evento": "fim", "ms": _ms(inicio_total)}
            return
    except _Interrompido:
        yield {"evento": "fim", "ms": _ms(inicio_total)}
        return

    resultados: dict[str, object] = {}
    with ThreadPoolExecutor(max_workers=len(PARALELOS)) as executor:
        inicio = time.perf_counter()
        futuros = {executor.submit(f, imagem, perguntar): agente for agente, f in PARALELOS.items()}
        for agente in PARALELOS:
            yield {"evento": "agente", "id": agente, "estado": "rodando"}
        for futuro in as_completed(futuros):
            agente = futuros[futuro]
            try:
                resultados[agente] = futuro.result()
                yield _ok(agente, resultados[agente], inicio)
            except Exception as erro:  # noqa: BLE001 - o campo vira pendência no cadastro
                resultados[agente] = None
                yield _erro(agente, erro, inicio)

    yield {"evento": "agente", "id": "cadastro", "estado": "rodando"}
    inicio = time.perf_counter()
    cadastro = montar_cadastro(
        resultados["numero"], resultados["nome"], resultados["material"],
        resultados["tipo"], resultados["geometria"],
    )
    resumo = f"{cadastro['peso_kg']:g} kg".replace(".", ",") if cadastro["peso_kg"] else "sem peso"
    yield {"evento": "agente", "id": "cadastro", "estado": "ok", "ms": _ms(inicio), "resumo": resumo}
    yield {"evento": "cadastro", "cadastro": cadastro}
    yield {"evento": "fim", "ms": _ms(inicio_total)}
