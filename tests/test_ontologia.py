"""Testes da ontologia (docs/ontologia/dengue_sp.yaml): estrutura e consistência com código e dados.

Mudar um limiar, nível, coluna ou tool no código sem mudar a ontologia (ou o contrário) deve
quebrar estes testes. O teste de validade obriga a revisar os achados no PR que atualizar o
snapshot.
"""

import inspect
import re
from collections import Counter
from pathlib import Path
from typing import Any, get_args

import pandas as pd
import pytest
import yaml

from smart_hospitals.data import indicators
from smart_hospitals.data.indicators import (
    LEVEL_MAP,
    P_RT1_ALTA,
    RT_ALTA,
    RT_QUEDA,
    Trend,
    calcular_tendencia,
)
from smart_hospitals.data.loader import REQUIRED_COLUMNS, load_snapshot
from tests.mcp_helpers import TOOLS

RAIZ = Path(__file__).resolve().parents[1]
ONTOLOGIA_PATH = RAIZ / "docs" / "ontologia" / "dengue_sp.yaml"
TAMANHO_MAXIMO = 20 * 1024  # RNF05: cabe com folga no contexto de um agente

SECOES = ["metadados", "conceitos", "relacoes", "regras", "achados", "orientacoes_agente"]
CAMPOS_METADADOS = {
    "nome",
    "versao",
    "fonte",
    "municipio",
    "geocodigo",
    "origem",
    "data_referencia",
    "valido_ate_se",
}
CAMPOS_ITENS = {
    "conceitos": {"id", "rotulo", "definicao"},
    "relacoes": {"de", "tipo", "para"},
    "regras": {"id", "descricao"},
    "achados": {
        "id",
        "afirmacao",
        "evidencia",
        "metodo",
        "origem",
        "valido_ate_se",
        "limitacoes",
        "implicacao",
    },
}
# IDs são únicos dentro de cada seção (decisão da task 13); conceito e regra podem ter o mesmo id.
SECOES_COM_ID = ["conceitos", "regras", "achados"]


@pytest.fixture(scope="module")
def ontologia() -> dict[str, Any]:
    with ONTOLOGIA_PATH.open(encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f)
    return data


@pytest.fixture(scope="module")
def snapshot() -> pd.DataFrame:
    return load_snapshot()


def _por_id(itens: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in itens}


def _cita_limiar(expressao: str, termo: str, limiar: float) -> bool:
    """O termo aparece com exatamente esse número (1.1 não aceita 1.15 nem 1.10)."""
    padrao = rf"{re.escape(termo)} {re.escape(str(limiar))}(?![\d.])"
    return re.search(padrao, expressao) is not None


# Estrutura


def test_ontologia_carrega_yaml_valido(ontologia: dict[str, Any]) -> None:
    assert isinstance(ontologia, dict)


def test_ontologia_secoes_obrigatorias(ontologia: dict[str, Any]) -> None:
    ausentes = [secao for secao in SECOES if secao not in ontologia]
    assert not ausentes, f"Seções ausentes: {ausentes}"


def test_metadados_campos_obrigatorios(ontologia: dict[str, Any]) -> None:
    ausentes = CAMPOS_METADADOS - ontologia["metadados"].keys()
    assert not ausentes, f"Metadados ausentes: {sorted(ausentes)}"


def test_metadados_origem_existe(ontologia: dict[str, Any]) -> None:
    origem = ontologia["metadados"]["origem"]
    inexistentes = [caminho for caminho in origem if not (RAIZ / caminho).exists()]
    assert not inexistentes, f"Arquivos de origem inexistentes: {inexistentes}"


@pytest.mark.parametrize("secao", CAMPOS_ITENS)
def test_itens_campos_obrigatorios(ontologia: dict[str, Any], secao: str) -> None:
    itens = ontologia[secao]
    assert itens, f"Seção {secao} vazia"
    for item in itens:
        ausentes = CAMPOS_ITENS[secao] - item.keys()
        assert not ausentes, f"{secao}/{item.get('id')}: campos ausentes {sorted(ausentes)}"


@pytest.mark.parametrize("secao", SECOES_COM_ID)
def test_ids_unicos_na_secao(ontologia: dict[str, Any], secao: str) -> None:
    contagem = Counter(item["id"] for item in ontologia[secao])
    duplicados = sorted(i for i, n in contagem.items() if n > 1)
    assert not duplicados, f"IDs duplicados em {secao}: {duplicados}"


def test_orientacoes_agente_sao_textos(ontologia: dict[str, Any]) -> None:
    orientacoes = ontologia["orientacoes_agente"]
    assert orientacoes
    assert all(isinstance(o, str) and o.strip() for o in orientacoes)


# Relações


def test_relacoes_apontam_para_conceitos_definidos(ontologia: dict[str, Any]) -> None:
    conceitos = {c["id"] for c in ontologia["conceitos"]}
    invalidas = [
        f"{r['de']} -{r['tipo']}-> {r['para']}"
        for r in ontologia["relacoes"]
        if r["de"] not in conceitos or r["para"] not in conceitos
    ]
    assert not invalidas, f"Relações com conceito indefinido: {invalidas}"


# Consistência com o código


def test_limiares_batem_com_codigo(ontologia: dict[str, Any]) -> None:
    regras = _por_id(ontologia["regras"])
    alta = regras["tendencia_alta"]["parametros"]
    queda = regras["tendencia_queda"]["parametros"]

    assert alta["rt_alta"] == RT_ALTA
    assert alta["p_rt1_alta"] == P_RT1_ALTA
    assert queda["rt_queda"] == RT_QUEDA


def test_expressoes_citam_limiares_do_codigo(ontologia: dict[str, Any]) -> None:
    """O texto da expressão é o que o agente lê; não pode ficar com número antigo."""
    regras = _por_id(ontologia["regras"])

    alta = regras["tendencia_alta"]["expressao"]
    queda = regras["tendencia_queda"]["expressao"]

    assert _cita_limiar(alta, "media(Rt, N) >", RT_ALTA), alta
    assert _cita_limiar(alta, "media(p_rt1, N) >", P_RT1_ALTA), alta
    assert _cita_limiar(queda, "media(Rt, N) <", RT_QUEDA), queda


def test_semanas_padrao_bate_com_codigo(ontologia: dict[str, Any]) -> None:
    padrao = inspect.signature(calcular_tendencia).parameters["semanas"].default
    regras = _por_id(ontologia["regras"])

    assert regras["tendencia_alta"]["parametros"]["semanas_padrao"] == padrao
    assert regras["tendencia_queda"]["parametros"]["semanas_padrao"] == padrao


def test_mapeamento_niveis_bate_com_level_map(ontologia: dict[str, Any]) -> None:
    regras = _por_id(ontologia["regras"])
    conceitos = _por_id(ontologia["conceitos"])

    assert regras["nivel_alerta_mapeamento"]["mapeamento"] == LEVEL_MAP
    assert conceitos["nivel_de_alerta"]["faixa"] == list(LEVEL_MAP.values())


def test_faixa_tendencia_bate_com_codigo(ontologia: dict[str, Any]) -> None:
    conceitos = _por_id(ontologia["conceitos"])
    assert set(conceitos["tendencia"]["faixa"]) == set(get_args(Trend))


def test_referencias_de_codigo_existem(ontologia: dict[str, Any]) -> None:
    referencias = [
        nome
        for regra in ontologia["regras"]
        if "referencia_codigo" in regra
        for nome in re.findall(r"\w+", regra["referencia_codigo"])
    ]
    assert referencias
    inexistentes = [nome for nome in referencias if not hasattr(indicators, nome)]
    assert not inexistentes, f"Nomes ausentes em indicators.py: {inexistentes}"


def test_colunas_existem_no_snapshot(ontologia: dict[str, Any]) -> None:
    colunas = {col for c in ontologia["conceitos"] for col in c.get("coluna", [])}
    assert colunas
    assert colunas <= set(REQUIRED_COLUMNS), sorted(colunas - set(REQUIRED_COLUMNS))


def test_tools_existem_no_mcp(ontologia: dict[str, Any]) -> None:
    tools = {t for c in ontologia["conceitos"] for t in c.get("tools", [])}
    assert tools
    assert tools <= TOOLS, sorted(tools - TOOLS)


# Validade e tamanho


def test_validade_frente_ao_snapshot(ontologia: dict[str, Any], snapshot: pd.DataFrame) -> None:
    se_mais_recente = int(snapshot["SE"].iloc[-1])
    valido_ate_se = ontologia["metadados"]["valido_ate_se"]
    assert se_mais_recente <= valido_ate_se, (
        f"SE mais recente ({se_mais_recente}) é posterior a valido_ate_se ({valido_ate_se}). "
        "Revise os achados da ontologia antes de atualizar o snapshot."
    )


def test_data_referencia_e_inicio_da_se_de_validade(
    ontologia: dict[str, Any], snapshot: pd.DataFrame
) -> None:
    metadados = ontologia["metadados"]
    semana = snapshot.loc[snapshot["SE"] == metadados["valido_ate_se"], "data_iniSE"]

    assert len(semana) == 1, f"SE {metadados['valido_ate_se']} ausente do snapshot"
    assert semana.iloc[0].date().isoformat() == str(metadados["data_referencia"])


def test_achados_validos_ate_a_se_dos_metadados(ontologia: dict[str, Any]) -> None:
    valido_ate_se = ontologia["metadados"]["valido_ate_se"]
    divergentes = [a["id"] for a in ontologia["achados"] if a["valido_ate_se"] != valido_ate_se]
    assert not divergentes, f"Achados com valido_ate_se diferente dos metadados: {divergentes}"


def test_orientacoes_citam_a_se_de_validade(ontologia: dict[str, Any]) -> None:
    """Uma SE escrita no texto das orientações não pode ficar para trás dos metadados."""
    valido_ate_se = ontologia["metadados"]["valido_ate_se"]
    textos = " ".join(ontologia["orientacoes_agente"])
    citadas = {int(se) for se in re.findall(r"SE (\d{6})", textos)}
    assert citadas <= {valido_ate_se}, f"SEs citadas: {sorted(citadas)}; esperado {valido_ate_se}"


def test_achado_cobertura_bate_com_snapshot(
    ontologia: dict[str, Any], snapshot: pd.DataFrame
) -> None:
    evidencia = _por_id(ontologia["achados"])["cobertura"]["evidencia"]

    assert evidencia["semanas"] == len(snapshot)
    assert evidencia["se_inicial"] == int(snapshot["SE"].iloc[0])
    assert evidencia["se_final"] == int(snapshot["SE"].iloc[-1])


def test_achado_atraso_notificacao_bate_com_ultima_semana(
    ontologia: dict[str, Any], snapshot: pd.DataFrame
) -> None:
    evidencia = _por_id(ontologia["achados"])["atraso_notificacao"]["evidencia"]
    ultima = snapshot.iloc[-1]

    assert evidencia["se"] == int(ultima["SE"])
    assert evidencia["notificados"] == ultima["casos"]
    assert evidencia["estimados"] == round(ultima["casos_est"])
    assert evidencia["intervalo"] == [ultima["casos_est_min"], ultima["casos_est_max"]]


def test_tamanho_maximo() -> None:
    assert ONTOLOGIA_PATH.stat().st_size <= TAMANHO_MAXIMO
