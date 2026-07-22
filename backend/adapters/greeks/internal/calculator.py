from backend.domain.models import OptionChain


class InternalGreeksCalculator:
    """Internal Greeks calculator scaffold.

    Real Greeks calculation with Black-Scholes/QuantLib is intentionally deferred.
    """

    def calculate(self, chain: OptionChain) -> OptionChain:
        raise NotImplementedError
