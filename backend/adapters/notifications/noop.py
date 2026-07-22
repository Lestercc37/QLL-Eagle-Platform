from backend.domain.models import FlowEvent, GammaAggregate


class NoopNotificationService:
    def notify(self, event: FlowEvent | GammaAggregate) -> None:
        return None
