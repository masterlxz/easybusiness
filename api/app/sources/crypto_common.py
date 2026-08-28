"""Shared error type for the crypto sources (cripto_defillama.py,
cripto_ultrasound.py, cripto_feargreed.py, cripto_coingecko.py).

Unlike bcb_sgs.py/acoes_yahoo.py/cvm_dfp.py (each mapping 1:1 to its own
router), these 4 small sources all feed the same 2 endpoints
(/v1/crypto/eth-indicators/{code}, /v1/crypto/{symbol}/...) — one shared
error type keeps the router's exception handling simple instead of needing
to catch 4 different classes.
"""


class CryptoDataError(RuntimeError):
    """Raised when any crypto source's HTTP request or response parsing fails."""
