"""Roda o desenho de exemplo com a OpenAI e grava os eventos em data/exemplo/execucao.json.

A tela usa essa gravação para mostrar uma execução real a quem abre o projeto sem chave.
Uso: python -m scripts.gravar_exemplo   (custa alguns centavos)
"""

import json
import time
from datetime import datetime

from PIL import Image

from backend import config
from backend.main import DESENHO_EXEMPLO
from backend.pipeline import analisar


def main() -> None:
    if not config.tem_chave():
        raise SystemExit("Defina OPENAI_API_KEY no .env antes de gravar.")
    inicio = time.perf_counter()
    eventos = []
    for evento in analisar(Image.open(DESENHO_EXEMPLO)):
        t_ms = round((time.perf_counter() - inicio) * 1000)
        eventos.append({"t_ms": t_ms, "evento": evento})
        print(f"{t_ms:>6} ms  {evento['evento']:<14} {evento.get('id', '')} {evento.get('estado', '')}"
              f" {evento.get('resumo', '')}")
    gravacao = {
        "gravado_em": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "modelo": config.MODELO,
        "desenho": DESENHO_EXEMPLO.name,
        "eventos": eventos,
    }
    config.EXECUCAO_GRAVADA.write_text(json.dumps(gravacao, ensure_ascii=False, indent=1) + "\n",
                                       encoding="utf-8")
    print(f"\ngravado em {config.EXECUCAO_GRAVADA.relative_to(config.RAIZ)}")


if __name__ == "__main__":
    main()
