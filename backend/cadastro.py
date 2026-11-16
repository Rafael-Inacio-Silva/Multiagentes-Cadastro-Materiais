"""Montagem do cadastro: a parte determinística, sem IA.

Recebe o que os agentes leram e calcula o que é conta (volume, peso), padroniza o texto breve
no formato de cadastro (até 40 caracteres, como o texto breve do SAP) e lista as pendências que
um cadastrista precisa revisar antes de criar o material.
"""

from __future__ import annotations

import math
import re
import unicodedata

from backend.agent_drawing.agent_drawing_weight import Geometria, Trecho

DENSIDADE_KG_M3 = {
    "aco_carbono": 7850,
    "aco_inox": 7930,
    "ferro_fundido": 7200,
    "aluminio": 2700,
    "bronze_latao": 8600,
    "polimero": 1200,
}
DENSIDADE_PADRAO = 7850  # aço, quando a família não é conhecida

ROTULO_TIPO = {
    "usinagem": "Usinagem",
    "caldeiraria": "Caldeiraria",
    "fundido_ferroso": "Fundido ferroso",
    "fundido_nao_ferroso": "Fundido não ferroso",
    "nao_metalico": "Não metálico",
    "metalico_com_revestimento_nao_metalico": "Metálico com revestimento",
}

LIMITE_TEXTO_BREVE = 40
_PALAVRAS_VAZIAS = {"DE", "DA", "DO", "DAS", "DOS", "E", "PARA"}


def volume_mm3(trecho: Trecho) -> float | None:
    """Volume de um trecho em mm³, ou None se faltar uma cota."""
    comprimento = trecho.comprimento_mm
    if trecho.forma == "cilindro" and trecho.diametro_mm:
        return math.pi / 4 * trecho.diametro_mm**2 * comprimento
    if trecho.forma == "tubo" and trecho.diametro_mm and trecho.diametro_interno_mm is not None:
        return math.pi / 4 * (trecho.diametro_mm**2 - trecho.diametro_interno_mm**2) * comprimento
    if trecho.forma == "prisma" and trecho.largura_mm and trecho.altura_mm:
        return trecho.largura_mm * trecho.altura_mm * comprimento
    return None


def calcular_peso(geometria: Geometria | None, familia: str | None) -> dict | None:
    if geometria is None:
        return None
    if geometria.massa_declarada_kg:
        return {"peso_kg": round(geometria.massa_declarada_kg, 3), "origem": "declarado no desenho"}

    volumes = [volume_mm3(t) for t in geometria.trechos]
    if not volumes or any(v is None or v <= 0 for v in volumes):
        return None
    volume = sum(volumes)
    densidade = DENSIDADE_KG_M3.get(familia or "", DENSIDADE_PADRAO)
    return {
        "peso_kg": round(volume * 1e-9 * densidade, 2),
        "origem": "calculado pela geometria",
        "volume_cm3": round(volume / 1000, 1),
        "densidade_kg_m3": densidade,
    }


def dimensao_principal(geometria: Geometria | None) -> str | None:
    """Ø maior × comprimento total para peças de revolução; C × L × A para prismas."""
    if geometria is None or not geometria.trechos:
        return None
    trechos = geometria.trechos
    comprimento = sum(t.comprimento_mm for t in trechos)
    diametros = [t.diametro_mm for t in trechos if t.forma in ("cilindro", "tubo") and t.diametro_mm]
    if len(diametros) == len(trechos):
        return f"Ø{_numero(max(diametros))} × {_numero(comprimento)} mm"
    if len(trechos) == 1 and trechos[0].forma == "prisma":
        t = trechos[0]
        if t.largura_mm and t.altura_mm:
            return f"{_numero(comprimento)} × {_numero(t.largura_mm)} × {_numero(t.altura_mm)} mm"
    return None


def texto_breve(nome: str | None, material: str | None, dimensao: str | None) -> str | None:
    """Ex.: 'EIXO TRANSMISSAO;ACO SAE 1045;D60X250MM' (sem acento, até 40 caracteres)."""
    if not nome:
        return None
    partes = [" ".join(p for p in _ascii(nome).split() if p not in _PALAVRAS_VAZIAS)]
    if material:
        partes.append(_ascii(material))
    if dimensao:
        partes.append(_ascii(dimensao.replace("Ø", "D").replace("×", "X")).replace(" ", ""))
    texto = ";".join(partes)
    while len(texto) > LIMITE_TEXTO_BREVE and len(partes) > 1:
        partes.pop()  # corta do fim: a dimensão sai antes do material
        texto = ";".join(partes)
    return texto[:LIMITE_TEXTO_BREVE]


def montar_cadastro(numero, nome, material, tipo, geometria) -> dict:
    """Cada argumento é a saída de um agente, ou None se o agente falhou."""
    peso = calcular_peso(geometria, material.familia if material else None)
    dimensao = dimensao_principal(geometria)
    cadastro = {
        "numero_desenho": numero.numero_desenho if numero else None,
        "revisao": numero.revisao if numero else None,
        "denominacao": nome.nome_peca if nome else None,
        "material": material.material if material else None,
        "tipo_item": tipo.tipo_item if tipo else None,
        "tipo_item_rotulo": ROTULO_TIPO.get(tipo.tipo_item) if tipo else None,
        "dimensao_principal": dimensao,
        "peso_kg": peso["peso_kg"] if peso else None,
        "peso": peso,
        "texto_breve": texto_breve(nome.nome_peca if nome else None,
                                   material.material if material else None, dimensao),
    }
    obrigatorios = {
        "numero_desenho": "Nº do desenho",
        "denominacao": "Denominação",
        "material": "Material",
        "tipo_item": "Tipo de item",
        "peso_kg": "Peso",
    }
    cadastro["pendencias"] = [rotulo for campo, rotulo in obrigatorios.items() if not cadastro[campo]]
    if peso and peso["origem"] == "calculado pela geometria":
        cadastro["pendencias"].append("Conferir peso estimado (sem massa no desenho)")
    if material and material.material and not material.familia:
        cadastro["pendencias"].append("Família do material desconhecida: densidade de aço usada")
    return cadastro


def _ascii(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sem_acento.upper()).strip()


def _numero(valor: float) -> str:
    return f"{valor:g}".replace(".", ",")
