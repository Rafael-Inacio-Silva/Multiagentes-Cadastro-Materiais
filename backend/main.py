"""API do MVP e servidor da tela.

    GET  /api/estado     modo de execução (ao vivo com chave da OpenAI, ou só gravado)
    POST /api/analisar   envia um desenho (PNG/JPG/WEBP) e recebe os eventos dos agentes (NDJSON)
    GET  /api/exemplo    roda o desenho de exemplo; ?gravado=1 repete a execução gravada
    /                    a tela (frontend/)
"""

from __future__ import annotations

import io
import json
import time
from typing import Iterable, Iterator

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from backend import config, llm
from backend.pipeline import analisar

app = FastAPI(title="Multiagentes · Cadastro Técnico de Materiais")
app.state.perguntar = llm.perguntar  # os testes trocam por respostas fixas

TIPOS_ACEITOS = {"image/png", "image/jpeg", "image/webp"}
DESENHO_EXEMPLO = config.PASTA_EXEMPLO / "eixo-transmissao.png"


def _ndjson(eventos: Iterable[dict]) -> StreamingResponse:
    linhas = (json.dumps(e, ensure_ascii=False) + "\n" for e in eventos)
    return StreamingResponse(linhas, media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-cache"})


def _ao_vivo() -> bool:
    return config.tem_chave() or app.state.perguntar is not llm.perguntar


@app.get("/api/estado")
def estado() -> dict:
    return {"ao_vivo": _ao_vivo(), "modelo": config.MODELO,
            "exemplo_gravado": config.EXECUCAO_GRAVADA.exists()}


@app.post("/api/analisar")
async def analisar_desenho(arquivo: UploadFile) -> StreamingResponse:
    if not _ao_vivo():
        raise HTTPException(503, "Sem OPENAI_API_KEY no .env: use o exemplo gravado.")
    if arquivo.content_type not in TIPOS_ACEITOS:
        raise HTTPException(415, "Envie o desenho como imagem PNG, JPG ou WEBP.")
    dados = await arquivo.read(config.TAMANHO_MAXIMO_BYTES + 1)
    if len(dados) > config.TAMANHO_MAXIMO_BYTES:
        raise HTTPException(413, "Imagem acima de 8 MB.")
    try:
        imagem = Image.open(io.BytesIO(dados))
        imagem.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(422, "Não foi possível abrir a imagem.") from None
    return _ndjson(analisar(imagem, app.state.perguntar))


@app.get("/api/exemplo")
def exemplo(gravado: bool = False, velocidade: float = 1.0) -> StreamingResponse:
    if gravado or not _ao_vivo():
        if not config.EXECUCAO_GRAVADA.exists():
            raise HTTPException(404, "Execução gravada não encontrada.")
        return _ndjson(_repetir_gravacao(max(velocidade, 0.1)))
    return _ndjson(analisar(Image.open(DESENHO_EXEMPLO), app.state.perguntar))


def _repetir_gravacao(velocidade: float) -> Iterator[dict]:
    """Devolve os eventos de uma execução real gravada, no mesmo ritmo em que aconteceram."""
    gravacao = json.loads(config.EXECUCAO_GRAVADA.read_text(encoding="utf-8"))
    anterior = 0
    for item in gravacao["eventos"]:
        espera = (item["t_ms"] - anterior) / 1000 / velocidade
        if espera > 0:
            time.sleep(min(espera, 5))
        anterior = item["t_ms"]
        evento = dict(item["evento"])
        if evento["evento"] == "inicio":
            evento.update(gravado=True, gravado_em=gravacao["gravado_em"], modelo=gravacao["modelo"])
        yield evento


app.mount("/exemplo", StaticFiles(directory=config.PASTA_EXEMPLO), name="exemplo")
app.mount("/", StaticFiles(directory=config.PASTA_FRONTEND, html=True), name="frontend")
