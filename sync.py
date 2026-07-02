import logging

from app.collector.blizzard_client import BlizzardClient
from app.database.session import init_db
from app.collector.realms import sync_realms

logging.basicConfig(level=logging.INFO)


def main() -> None:
    init_db()  # crea la tabla realms si no existe
    client = BlizzardClient()
    try:
        sync_realms(client)
    finally:
        client.close()


if __name__ == "__main__":
    main()