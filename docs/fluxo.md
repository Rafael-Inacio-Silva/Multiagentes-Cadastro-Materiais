# Fluxo do MVP

1. A tela envia a imagem do desenho (ou pede o exemplo).
2. O **classificador** confere se é desenho técnico. Se não for, o fluxo termina como fora do escopo.
3. O agente de **estrutura** confere se é uma peça única. Conjuntos terminam como fora do escopo.
4. Cinco agentes rodam em paralelo: **nº do desenho**, **denominação**, **material**, **tipo de item**
   e **geometria** (cotas dos trechos ou massa declarada).
5. O **cadastro** é montado em Python: peso, dimensão principal, texto breve e pendências.
6. O cadastrista revisa as pendências e baixa o JSON.
