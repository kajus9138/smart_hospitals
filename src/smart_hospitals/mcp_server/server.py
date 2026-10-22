"""MCP server com os indicadores de dengue de São Paulo capital (SDK mcp v2, transporte stdio).

O stdout é reservado ao protocolo MCP: nada de print. Os logs vão para stderr (o MCPServer configura
o logging raiz com um handler em stderr ao ser instanciado).
"""

import functools
import inspect
import logging
import time
from collections.abc import Callable
from dataclasses import asdict
from typing import Annotated, Any

import pandas as pd
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from smart_hospitals import data

logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "Indicadores semanais de dengue em São Paulo capital, do InfoDengue (snapshot local, somente "
    "leitura). Toda resposta traz data_referencia: a semana mais recente do snapshot. Não há "
    "previsão numérica de casos; use Rt, p_rt1, nível de alerta e casos_est (nowcast, com "
    "intervalo) para avaliar a tendência."
)

mcp = MCPServer("dengue-sp", instructions=INSTRUCTIONS)


@functools.cache
def get_data() -> pd.DataFrame:
    """Snapshot carregado uma única vez por processo (main() o carrega antes de aceitar chamadas).

    Depois de atualizar o CSV, reinicie o servidor para servir os dados novos.
    """
    return data.load_snapshot()


def _reference(df: pd.DataFrame) -> str:
    return data.get_reference_date(df).isoformat()


def logged[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Registra em stderr cada chamada executada (nome, parâmetros, duração, status) - RNF02.

    Chamadas barradas pelo schema (tipo ou intervalo) nem chegam aqui; o próprio SDK as registra
    em stderr ("Tool '<nome>' rejected arguments"). ParametroInvalido vira ToolError, cuja mensagem
    chega ao cliente; qualquer outra exceção é registrada com traceback e repassada, e o cliente
    recebe só um erro genérico.
    """
    signature = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        params = dict(bound.arguments)
        start = time.perf_counter()

        def log(status: str) -> None:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "tool=%s params=%s duracao_ms=%.1f status=%s",
                func.__name__,
                params,
                duration_ms,
                status,
            )

        try:
            result = func(*args, **kwargs)
        except data.ParametroInvalido as exc:
            log(f"erro: {exc}")
            raise ToolError(str(exc)) from exc
        except Exception:
            log("erro inesperado")
            logger.exception("Falha inesperada na tool %s", func.__name__)
            raise
        log("ok")
        return result

    return wrapper


@mcp.tool()
@logged
def situacao_atual() -> dict[str, Any]:
    """Situação da dengue em São Paulo na semana mais recente do snapshot.

    Retorna casos notificados, casos estimados (nowcast) com intervalo mín./máx. (None quando o
    InfoDengue não informa), incidência por 100 mil hab., nível de alerta, Rt, p_rt1 (probabilidade
    de Rt > 1) e variação semanal (%) dos casos estimados.
    """
    return asdict(data.calcular_situacao_atual(get_data()))


@mcp.tool()
@logged
def tendencia(
    semanas: Annotated[int, Field(ge=1, le=52, description="Semanas analisadas (1 a 52)")] = 4,
) -> dict[str, Any]:
    """Indicadores das últimas N semanas e o resumo da tendência: alta, estavel ou queda.

    alta: Rt médio > 1,1 e p_rt1 médio > 0,7; queda: Rt médio < 0,9; senão estavel.
    """
    df = get_data()
    return {"data_referencia": _reference(df), **asdict(data.calcular_tendencia(df, semanas))}


@mcp.tool()
@logged
def serie_historica(
    inicio: Annotated[
        str | int, Field(description="Início: SE (AAAASS, ex. 202401) ou data AAAA-MM-DD")
    ],
    fim: Annotated[str | int, Field(description="Fim: no mesmo formato de inicio")],
) -> dict[str, Any]:
    """Série semanal (casos, casos estimados com intervalo, Rt, nível) de inicio a fim, inclusive.

    Com datas, entram as semanas que contêm inicio e fim.
    """
    df = get_data()
    serie = data.serie_historica(df, inicio, fim)
    return {"data_referencia": _reference(df), "total_semanas": len(serie), "serie": serie}


@mcp.tool()
@logged
def comparativo_sazonal(
    semana: Annotated[
        int | None,
        Field(ge=1, le=53, description="Semana epidemiológica (1 a 53); padrão: a mais recente"),
    ] = None,
) -> dict[str, Any]:
    """Casos estimados de uma semana no ano de referência vs. a mesma semana nos anos anteriores.

    Média, mínimo e máximo usam só anos anteriores; ano_atual é None se a semana ainda não ocorreu.
    """
    df = get_data()
    return {"data_referencia": _reference(df), **data.comparativo_sazonal(df, semana)}


def main() -> None:
    """Inicia o servidor no transporte stdio."""
    df = get_data()
    logger.info("Iniciando o MCP server dengue-sp (stdio), data de referência %s", _reference(df))
    mcp.run("stdio")
