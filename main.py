import logging

from rich.logging import RichHandler

from www69shuba import download

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

log = logging.getLogger(__name__)

if __name__ == "__main__":
    download("90175")
