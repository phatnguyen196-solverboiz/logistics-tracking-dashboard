import logging
import os
from collections.abc import Callable
from datetime import datetime

from django.utils import timezone
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .carrier_base import CarrierTracker, TrackingResult
from .exceptions import (
    AutomationTimeoutError,
    CarrierUnavailableError,
    TrackingNotFoundError,
    TrackingParsingError,
)
from .selenium_client import create_chrome_driver

logger = logging.getLogger(__name__)


class DemoExpressTracker(CarrierTracker):
    def __init__(
        self,
        base_url: str | None = None,
        driver_factory: Callable = create_chrome_driver,
        timeout_seconds: int = 10,
    ) -> None:
        self.base_url = base_url or os.getenv("MOCK_CARRIER_URL", "http://localhost:8081")
        self.driver_factory = driver_factory
        self.timeout_seconds = timeout_seconds

    def track(self, tracking_number: str) -> TrackingResult:
        driver = None
        try:
            driver = self.driver_factory()
            wait = WebDriverWait(driver, self.timeout_seconds)
            driver.get(self.base_url)
            field = wait.until(EC.visibility_of_element_located((By.ID, "trackingNumber")))
            field.clear()
            field.send_keys(tracking_number)
            wait.until(EC.element_to_be_clickable((By.ID, "trackButton"))).click()
            result = wait.until(EC.visibility_of_element_located((By.ID, "trackingResult")))
            if result.get_attribute("data-found") != "true":
                raise TrackingNotFoundError(f"Tracking number {tracking_number} was not found")

            status = driver.find_element(By.ID, "resultStatus").text.strip()
            location = driver.find_element(By.ID, "resultLocation").text.strip()
            updated_raw = driver.find_element(By.ID, "resultUpdated").get_attribute("datetime")
            if not status or not updated_raw:
                raise TrackingParsingError("Carrier response is missing required fields")
            updated_at = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
            if timezone.is_naive(updated_at):
                updated_at = timezone.make_aware(updated_at)
            return TrackingResult(tracking_number, status, location, updated_at)
        except TrackingNotFoundError:
            raise
        except TimeoutException as exc:
            raise AutomationTimeoutError("Timed out waiting for Demo Express") from exc
        except NoSuchElementException as exc:
            raise TrackingParsingError("Demo Express response layout is invalid") from exc
        except WebDriverException as exc:
            raise CarrierUnavailableError("Unable to reach Demo Express") from exc
        except (TypeError, ValueError) as exc:
            raise TrackingParsingError("Demo Express returned an invalid update time") from exc
        finally:
            if driver is not None:
                try:
                    driver.quit()
                except WebDriverException:
                    logger.warning("Browser cleanup failed", exc_info=True)
