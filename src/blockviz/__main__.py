"""Command line entry-point for BlockViz."""

from .app import BlockVizApplication


def main() -> int:
    """Launch the Qt event loop."""
    app = BlockVizApplication()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
