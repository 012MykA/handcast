from handcast.core.app import Application


def main() -> None:
    try:
        app = Application()
        app.run()
    except Exception as e:
        print(f"Error: {e}")
