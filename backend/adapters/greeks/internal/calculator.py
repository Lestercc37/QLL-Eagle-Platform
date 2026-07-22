from backend.domain.models import Greeks, MarketSnapshot, OptionContract


class InternalGreeksCalculator:
    """Internal Greeks calculator scaffold.

    Real Greeks calculation with py_vollib/QuantLib is intentionally deferred.
    """

    def calculate(self, contract: OptionContract, market: MarketSnapshot) -> Greeks:
        raise NotImplementedError
