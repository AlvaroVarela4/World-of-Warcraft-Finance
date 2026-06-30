import logging

from app.collector.blizzard_client import BlizzardClient
from app.database.session import init_db
from app.collector.collector import save_commodities

logging.basicConfig(level=logging.INFO)


def main() -> None:
    init_db()  # crea las tablas si no existen
    client = BlizzardClient()
    try:
        save_commodities(client)
    finally:
        client.close()


if __name__ == "__main__":
    main()