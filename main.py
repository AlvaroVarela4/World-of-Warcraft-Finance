import logging

from app.collector.blizzard_client import BlizzardClient

logging.basicConfig(level=logging.INFO)


def main() -> None:import logging

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
    client = BlizzardClient()
    try:
        realms = client.get_connected_realms()
        print(f"Connected realms encontrados: {len(realms['connected_realms'])}")
        print("Ejemplo de href:", realms["connected_realms"][0]["href"])

        # El ID del connected realm va dentro del href de arriba.
        # Sustituye 1080 por uno válido de tu región y prueba:
        auctions = client.get_auctions(1080)
        print(f"Subastas descargadas: {len(auctions['auctions'])}")
    finally:
        client.close()


if __name__ == "__main__":
    main()