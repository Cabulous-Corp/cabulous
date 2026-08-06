import subprocess
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "service" / "docker-compose.yaml"
BASE_URL = "http://localhost:3001"
BOOTSTRAP_PASSWORD = "Bootstrap!2026"
ONBOARDING_PASSWORD = "Cabulous!2026"
IMAGE_PATH = Path(
    r"C:\Users\clebm\AppData\Local\Temp\codex-clipboard-e33a4fe5-68d6-4b77-b077-d51f31c12f30.png"
)


def manage_shell(code: str) -> None:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            "exec",
            "-T",
            "web",
            "python",
            "manage.py",
            "shell",
            "-c",
            code,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Django setup failed: {result.stderr[-1000:]}")


def create_users(usernames: list[str]) -> None:
    values = ",".join(f"('{username}', '{username}@example.com')" for username in usernames)
    code = (
        "from users.models import User; "
        "[(User.objects.filter(username=u).delete(), "
        f"User.objects.create_user(username=u, email=e, "
        f"password='{BOOTSTRAP_PASSWORD}', first_name='E2E', last_name='User', "
        f"onboarding_completed_at=None)) for u,e in [{values}]]"
    )
    manage_shell(code)


def delete_users(usernames: list[str]) -> None:
    values = ",".join(repr(username) for username in usernames)
    code = (
        "from django.core.files.storage import default_storage; "
        "from users.models import User; "
        f"users=list(User.objects.filter(username__in=[{values}])); "
        "[default_storage.delete(getattr(user, field).name) "
        "for user in users for field in ('avatar', 'banner') if getattr(user, field).name]; "
        "User.objects.filter(username__in=["
        f"{values}]).delete()"
    )
    manage_shell(code)


def login(page: Page, username: str) -> None:
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")
    page.locator('input[name="identifier"]').fill(f"{username}@example.com")
    page.locator('input[name="password"]').fill(BOOTSTRAP_PASSWORD)
    page.get_by_role("button", name="Entrar").click()
    page.wait_for_url(f"{BASE_URL}/onboarding", timeout=20_000)
    page.wait_for_load_state("networkidle")


def fill_profile(page: Page, username: str, *, phone: str | None = None) -> None:
    page.locator('input[name="first_name"]').fill("E2E")
    page.locator('input[name="last_name"]').fill("User")
    page.locator('input[name="username"]').fill(username)
    page.get_by_role("button", name="Continuar").click()

    page.get_by_role("button", name="Continuar").click()

    page.locator('input[name="email"]').fill(f"{username}@example.com")
    if phone is not None:
        page.locator('input[name="phone_number"]').fill(phone)
    page.get_by_role("button", name="Continuar").click()


def go_to_preview(page: Page, password: str) -> None:
    page.locator('input[name="new_password"]').fill(password)
    page.get_by_role("button", name="Continuar").click()
    page.get_by_role("button", name="Concluir!").wait_for()


def complete(page: Page) -> None:
    page.get_by_role("button", name="Concluir!").click()
    page.wait_for_url(f"{BASE_URL}/", timeout=30_000)
    page.wait_for_load_state("networkidle")


def run_password_variations(page: Page, username: str) -> None:
    login(page, username)
    fill_profile(page, username)

    page.locator('input[name="new_password"]').fill("short")
    page.get_by_role("button", name="Continuar").click()
    page.locator("p.text-destructive").filter(has_text="Senha").wait_for()

    go_to_preview(page, "12345678")
    page.get_by_role("button", name="Concluir!").click()
    error = page.locator("p.text-destructive").filter(has_text="Senha:").last
    error.wait_for(timeout=20_000)
    assert "Senha:" in error.inner_text()

    page.get_by_role("button", name="Voltar").click()
    go_to_preview(page, ONBOARDING_PASSWORD)
    complete(page)


def run_phone_variation(page: Page, username: str) -> None:
    login(page, username)
    fill_profile(page, username, phone="000")
    go_to_preview(page, ONBOARDING_PASSWORD)
    page.get_by_role("button", name="Concluir!").click()
    error = page.locator("p.text-destructive").filter(has_text="Telefone:").last
    error.wait_for(timeout=20_000)
    assert "Telefone:" in error.inner_text()


def run_success_with_media(page: Page, username: str) -> None:
    assert IMAGE_PATH.exists()
    login(page, username)
    page.locator('input[type="file"]').nth(0).set_input_files(str(IMAGE_PATH))
    page.wait_for_timeout(1000)
    page.locator('input[type="file"]').nth(1).set_input_files(str(IMAGE_PATH))
    page.wait_for_timeout(1500)
    fill_profile(page, username)
    go_to_preview(page, ONBOARDING_PASSWORD)
    complete(page)


def main() -> None:
    suffix = str(int(time.time()))
    users = [f"e2e_password_{suffix}", f"e2e_phone_{suffix}", f"e2e_media_{suffix}"]
    create_users(users)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                run_password_variations(browser.new_page(), users[0])
                print(
                    "PASS password variations: client-side, numeric backend error, retry, success"
                )
                run_phone_variation(browser.new_page(), users[1])
                print("PASS phone validation: structured backend error shown in onboarding")
                run_success_with_media(browser.new_page(), users[2])
                print("PASS complete onboarding with avatar and banner uploads")
            finally:
                browser.close()
    finally:
        delete_users(users)


if __name__ == "__main__":
    main()
