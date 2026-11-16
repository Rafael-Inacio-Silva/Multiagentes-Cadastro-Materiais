# Arquitetura

Um orquestrador (`backend/pipeline.py`) chama agentes especialistas. Cada agente é um módulo com
três peças: uma instrução curta, um esquema Pydantic de saída e uma função que recebe a imagem e a
porta para o modelo (`backend/llm.py`).

```
API (FastAPI) ──► pipeline.analisar(imagem) ──► eventos NDJSON ──► tela
                     │
                     ├─ classifier.classificar            (sequencial, porta de entrada)
                     ├─ agent_drawing_structure            (sequencial, porta de entrada)
                     ├─ 5 agentes de atributo              (ThreadPoolExecutor, em paralelo)
                     └─ cadastro.montar_cadastro           (Python puro)
```

- **Porta única para o modelo.** `llm.perguntar(instrucao, imagem, esquema)` usa a Responses API
  com Structured Outputs. Os agentes recebem essa função por parâmetro, e os testes a substituem
  por respostas fixas.
- **Eventos em tempo real.** O pipeline é um gerador: cada agente emite `rodando` e depois `ok` ou
  `erro`. A API repassa os eventos como NDJSON, e a tela acende o cartão de cada agente.
- **Determinístico onde dá.** Peso (volume × densidade por família de material), dimensão principal,
  texto breve de 40 caracteres e pendências são calculados em `backend/cadastro.py`.
