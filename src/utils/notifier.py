import logging
import json
import requests
from typing import Dict, Any

class Notifier:
    """
    Handles notifications to external services (e.g., Microsoft Teams).
    """

    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)

    def send_teams_notification(self, stats: Dict[str, int], run_info: Dict[str, str]) -> bool:
        """
        Sends a test execution summary to Microsoft Teams.

        Args:
            stats (Dict[str, int]): Test statistics (total, passed, failed, skipped).
            run_info (Dict[str, str]): Run information (run_id, environment, etc).

        Returns:
            bool: True if successful or skipped (due to missing URL), False on failure.
        """
        if not self.webhook_url:
            self.logger.warning("Teams webhook URL is not set. Notification skipped.")
            # For testing purposes without URL, we consider this "handled"
            return True

        title = f"Test Execution Report: {run_info.get('run_id', 'Unknown')}"
        color = "00FF00" if stats.get("failed", 0) == 0 else "FF0000"

        # Adaptive Card payload
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": title,
            "sections": [{
                "activityTitle": title,
                "activitySubtitle": f"Environment: {run_info.get('env', 'Unknown')}",
                "facts": [
                    {"name": "Total", "value": str(stats.get("total", 0))},
                    {"name": "Passed", "value": str(stats.get("passed", 0))},
                    {"name": "Failed", "value": str(stats.get("failed", 0))},
                    {"name": "Skipped", "value": str(stats.get("skipped", 0))}
                ],
                "markdown": True
            }]
        }

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            self.logger.info("Teams notification sent successfully.")
            return True
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Teams notification: {e}")
            return False
