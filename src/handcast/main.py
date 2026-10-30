import traceback

from handcast.core.app import Application


def main() -> None:
    try:
        app = Application()
        app.run()
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
