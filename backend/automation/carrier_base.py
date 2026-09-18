from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class TrackingResult:
    tracking_number: str
    status: str
    location: str
    updated_at: datetime


class CarrierTracker(ABC):
    @abstractmethod
    def track(self, tracking_number: str) -> TrackingResult:
        raise NotImplementedError
