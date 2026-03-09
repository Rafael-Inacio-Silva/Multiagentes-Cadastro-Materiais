# Sistema Multiagente para Cadastro Técnico de Materiais

Projeto em desenvolvimento voltado à automação do cadastro técnico de materiais na área de suprimentos.

A proposta é utilizar uma arquitetura multiagente para interpretar desenhos técnicos e extrair informações relevantes para o processo de cadastro.

## Informações que o sistema pretende extrair

- nome do item
- número do desenho
- material
- peso
- tipo do item
- estrutura do item

## Estrutura do projeto

- `backend`: lógica principal do sistema
- `docs`: documentação da arquitetura e fluxo
- `data`: arquivos de exemplo e saídas
- `frontend`: interface futura do sistema

## Próximos passos

- implementar primeiro agente de extração
- criar fluxo principal no `main.py`
- integrar múltiplos agentes
- iniciar frontend