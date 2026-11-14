import os

import redis
from redis.backoff import NoBackoff
from redis.retry import Retry

TIMEOUT_SEGUNDOS = 2

_cliente = None


def conectar():
    """Devolve um cliente Redis, criado na primeira chamada e reutilizado depois."""
    global _cliente
    if _cliente is None:
        _cliente = redis.Redis(
            host=os.environ.get("REDIS_HOST", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            decode_responses=True,
            socket_connect_timeout=TIMEOUT_SEGUNDOS,
            socket_timeout=TIMEOUT_SEGUNDOS,
            retry=Retry(NoBackoff(), 0),
        )
    return _cliente


def salvar(chave, valor, ttl=None):
    """Grava valor em chave. Com ttl (segundos), a chave expira depois disso."""
    if not isinstance(chave, str) or not chave.strip():
        raise ValueError("chave não pode ser vazia")
    if ttl is not None and (isinstance(ttl, bool) or not isinstance(ttl, int) or ttl <= 0):
        raise ValueError("ttl deve ser um inteiro positivo (segundos) ou None")

    try:
        conectar().set(chave, valor, ex=ttl)
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        raise ConnectionError(
            f"não foi possível falar com o Redis em "
            f"{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', '6379')} "
            f"(timeout de {TIMEOUT_SEGUNDOS}s): {e}"
        ) from e
    return True
