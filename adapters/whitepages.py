import re
from pathlib import Path

from cove.adapter import BrokerAdapter, OptOutResult, OptOutStatus, _now
from cove.browser.errors import CaptchaDetectedError, NavigationBlockedError
from cove.browser.session import BrowserSession
from cove.profile.models import Profile


class WhitepagesAdapter(BrokerAdapter):
    broker_slug = "whitepages"
    manual_url = "https://www.whitepages.com/suppression_requests"

    def __init__(
        self,
        allowed_hosts: frozenset[str],
        headless: bool = True,
        screenshot_dir: Path | None = None,
    ) -> None:
        self._allowed_hosts = allowed_hosts
        self._headless = headless
        self._screenshot_dir = screenshot_dir

    def submit_optout(self, profile: Profile) -> OptOutResult:
        if not profile.names or not profile.names[0].strip() or not profile.addresses:
            return OptOutResult(
                broker_slug=self.broker_slug,
                status=OptOutStatus.failed,
                timestamp=_now(),
                message="Profile missing required fields: names and addresses",  # static string — no profile data
            )

        name = profile.names[0]
        addr = profile.addresses[0]

        try:
            with BrowserSession(
                allowed_hosts=self._allowed_hosts,
                headless=self._headless,
                screenshot_dir=self._screenshot_dir,
            ) as session:
                return self._run_optout(session, name, addr)
        except CaptchaDetectedError:
            return OptOutResult(
                broker_slug=self.broker_slug,
                status=OptOutStatus.manual_required,
                timestamp=_now(),
                message="CAPTCHA detected",
                manual_url=self.manual_url,
            )
        except NavigationBlockedError as exc:
            return OptOutResult(
                broker_slug=self.broker_slug,
                status=OptOutStatus.failed,
                timestamp=_now(),
                message=f"Navigation blocked: {type(exc).__name__}",
            )
        except Exception as exc:  # NOT bare except: — KeyboardInterrupt/SystemExit must propagate
            return OptOutResult(
                broker_slug=self.broker_slug,
                status=OptOutStatus.failed,
                timestamp=_now(),
                message=f"Unexpected error: {type(exc).__name__}",
            )

    def _run_optout(self, session: BrowserSession, name: str, addr) -> OptOutResult:
        session.navigate(self.manual_url)
        session.check_for_captcha()

        page = session.page
        page.get_by_label(re.compile(r"name", re.I)).fill(name)
        page.get_by_label(re.compile(r"city|location", re.I)).fill(f"{addr.city}, {addr.state}")
        page.click('button[type="submit"], input[type="submit"]')
        page.wait_for_load_state("networkidle")
        session.check_for_captcha()

        # Check count() BEFORE .first — .first.count() is always 1
        optout_link = page.get_by_text("Remove me", exact=False)
        if optout_link.count() == 0:
            return OptOutResult(
                broker_slug=self.broker_slug,
                status=OptOutStatus.profile_not_visible_as_of_date,
                timestamp=_now(),
                message="No matching listing found",
            )

        optout_link.first.click()
        page.wait_for_load_state("networkidle")
        session.check_for_captcha()  # check on confirmation page too

        # Use a narrow regex to avoid matching unrelated "Remove X" buttons in headers/nav
        submit_btn = page.get_by_role("button", name=re.compile(r"^(submit|confirm)\s", re.I))
        if submit_btn.count() == 0:
            # Confirmation button not found — cannot verify submission; require manual check
            return OptOutResult(
                broker_slug=self.broker_slug,
                status=OptOutStatus.manual_required,
                timestamp=_now(),
                message="Confirmation button not found — please complete opt-out manually",
                manual_url=self.manual_url,
            )

        submit_btn.first.click()
        page.wait_for_load_state("networkidle")

        return OptOutResult(
            broker_slug=self.broker_slug,
            status=OptOutStatus.submitted,
            timestamp=_now(),
            message="Opt-out submitted",
        )
