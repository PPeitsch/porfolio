"""Takes the README screenshots of the four views with the example content.

    pip install playwright && playwright install chromium
    python scripts/screenshots.py [--out docs/images] [--theme catppuccin]
                                  [--example-images]

It starts the app on a free local port with the bundled data/ (Alex Example),
so the screenshots never show anyone's real data, and saves selector-view.png,
cli-view.png, recruiter-view.png and visual-view.png. The chat's answer is a
fixed text served by the script, so no model or API key is needed.

The example projects in data/ are the views themselves: --example-images also
copies the CLI, chat and visual screenshots to data/images, so the visual view
shows the current look (run it twice: the second visual screenshot shows the
first one's images).
"""

import argparse
import os
import shutil
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VIEWPORT = {"width": 1280, "height": 800}
ACCESS_CODE = "screenshots"
CLI_COMMANDS = ["neofetch", "ls projects"]
CHAT_QUESTION = "Which projects use Flask?"
CHAT_REPLY = (
    "Two of Alex's projects are built with Flask:\n\n"
    "- **CLI view**: the terminal of this portfolio, with commands to browse "
    "the CV and the projects.\n"
    "- **Visual view**: the project gallery, one card per project.\n\n"
    "Type `show <id>` in the terminal for the details of each one."
)


def start_app(theme: str):
    """Runs the app with the example content in a thread; returns its URL."""
    # Before importing the app: config.py reads the environment on import.
    os.environ.update(
        {
            "PORTFOLIO_DATA_DIR": str(ROOT / "data"),
            "PORTFOLIO_LANGUAGES": "en",
            "PORTFOLIO_DEFAULT_THEME": theme,
            "RECRUITER_ACCESS_CODE": ACCESS_CODE,
            "SECRET_KEY": "screenshots-only-secret-key-0123456789",
            "BANNER_ENABLED": "false",
        }
    )
    sys.path.insert(0, str(ROOT))
    from werkzeug.serving import make_server

    from app.shell import create_app

    server = make_server("127.0.0.1", 0, create_app())
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_port}"


def take_screenshots(base_url: str, out: Path) -> None:
    from playwright.sync_api import sync_playwright

    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=2)

        def fixed_chat_reply(route):
            route.fulfill(json={"reply": CHAT_REPLY})

        page.route("**/recruiter/api/chat", fixed_chat_reply)

        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        page.mouse.move(0, 0)
        page.screenshot(path=out / "selector-view.png")

        page.click("#select-cli")
        page.wait_for_selector("#prompt >> text=password:")
        page.fill("#input", ACCESS_CODE)
        page.press("#input", "Enter")
        page.wait_for_selector("#prompt:not(:text('password:'))")
        page.evaluate("document.getElementById('output').innerHTML = ''")
        for command in CLI_COMMANDS:
            page.fill("#input", command)
            page.press("#input", "Enter")
            page.wait_for_timeout(400)
        page.mouse.move(0, 0)
        page.screenshot(path=out / "cli-view.png")

        page.click("#dock-recruiter")
        page.wait_for_selector("#chat-input:not([disabled])")
        page.fill("#chat-input", ACCESS_CODE)
        page.press("#chat-input", "Enter")
        page.wait_for_function("!document.getElementById('chat-input').disabled")
        page.wait_for_timeout(400)
        page.fill("#chat-input", CHAT_QUESTION)
        page.press("#chat-input", "Enter")
        page.wait_for_selector(f"#chat-messages >> text={CHAT_REPLY.split(':')[0]}")
        page.wait_for_timeout(400)
        page.mouse.move(0, 0)
        page.screenshot(path=out / "recruiter-view.png")

        page.click("#dock-visual")
        page.wait_for_selector(".project-card-visual")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)  # The cards fade in
        page.mouse.move(0, 0)
        page.screenshot(path=out / "visual-view.png")

        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=str(ROOT / "docs" / "images"))
    parser.add_argument("--theme", default="catppuccin")
    parser.add_argument(
        "--example-images",
        action="store_true",
        help="also copy the view screenshots to data/images",
    )
    args = parser.parse_args()

    out = Path(args.out)
    server, base_url = start_app(args.theme)
    try:
        take_screenshots(base_url, out)
    finally:
        server.shutdown()
    print(f"Screenshots saved in {out}")
    if args.example_images:
        for name in ("cli-view.png", "recruiter-view.png", "visual-view.png"):
            shutil.copyfile(out / name, ROOT / "data" / "images" / name)
        print("Example project images updated in data/images")


if __name__ == "__main__":
    main()
