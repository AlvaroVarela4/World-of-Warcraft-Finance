"""
Scheduler de capturas periódicas: la pieza que construye el histórico de mercado.

Cada intervalo (60 min por defecto, configurable con SCHEDULER_INTERVAL_MINUTES)
descarga las subastas de los reinos objetivo y las guarda como un snapshot
nuevo. Con snapshots acumulados a lo largo del tiempo, el endpoint de histórico
(/api/market/{realm}/history/{item}) puede dibujar curvas de precio (min/mediana/max)
y de volumen de stock por objeto.

Reinos objetivo:
  - SCHEDULER_REALMS="Sanguino,Zul'jin"  -> solo esos reinos
  - SCHEDULER_REALMS vacío               -> todos los reinos que ya tienen
                                            algún snapshot (los que has usado)

Deduplicación: Blizzard regenera los volcados ~1 vez por hora. Cada petición
envía If-Modified-Since con la fecha del último snapshot guardado; si Blizzard
responde 304 no se almacena nada, así que el histórico no acumula snapshots
duplicados aunque el scheduler corra más a menudo de lo que Blizzard publica.

Uso:
    docker compose up -d         # forma recomendada: corre junto a Postgres
                                 # y se reinicia solo con el PC (restart: unless-stopped)
    python scheduler.py          # proceso residente fuera de Docker
    python scheduler.py --once   # una sola captura y termina (pruebas, o cron
                                 # externo tipo Task Scheduler)

En el primer arranque contra una BD vacía puebla solo el registro de reinos;
las capturas empiezan cuando hay reinos objetivo (SCHEDULER_REALMS o algún
snapshot previo). Detener el modo residente con Ctrl+C.
"""
import logging
import sys
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import func, select

from app.collector.blizzard_client import BlizzardClient
from app.collector.collector import save_commodities, save_realm_auctions
from app.collector.items import item_ids_in_snapshot, resolve_items
from app.collector.realms import sync_realms
from app.config import settings
from app.database.models import Realm, Snapshot
from app.database.session import SessionLocal, init_db
from app.services.analysis import latest_realm_snapshot_id, latest_snapshot_id

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _tracked_connected_realm_ids() -> list[int]:
    """Connected realms a capturar en cada tick.

    Si SCHEDULER_REALMS trae nombres, se resuelven contra el registro local
    (tabla realms, poblada por sync.py). Si está vacío, se siguen todos los
    reinos con al menos un snapshot: capturar un reino una vez (p. ej. desde
    el botón "Actualizar datos" del front) lo incorpora al histórico.
    """
    names = [n.strip() for n in settings.scheduler_realms.split(",") if n.strip()]
    with SessionLocal() as session:
        if names:
            rows = session.execute(
                select(Realm.name, Realm.connected_realm_id).where(Realm.name.in_(names))
            ).all()
            found = {r.name: r.connected_realm_id for r in rows}
            missing = set(names) - set(found)
            if missing:
                logger.warning(
                    "Reinos de SCHEDULER_REALMS no encontrados en el registro: %s "
                    "(¿nombre exacto? ¿ejecutaste sync.py?)",
                    ", ".join(sorted(missing)),
                )
            return sorted(set(found.values()))

        rows = session.scalars(
            select(Snapshot.connected_realm_id)
            .where(Snapshot.source == "realm", Snapshot.connected_realm_id.isnot(None))
            .distinct()
        ).all()
    return sorted(rows)


def _last_fetched_at(connected_realm_id: int | None, source: str) -> datetime | None:
    """fetched_at del snapshot más reciente, como datetime UTC aware.

    Se usa como If-Modified-Since: si Blizzard no ha publicado un volcado
    posterior a nuestra última captura, no hay nada nuevo que guardar.
    """
    realm_filter = (
        Snapshot.connected_realm_id.is_(None)
        if connected_realm_id is None
        else Snapshot.connected_realm_id == connected_realm_id
    )
    with SessionLocal() as session:
        fetched = session.scalar(
            select(func.max(Snapshot.fetched_at)).where(Snapshot.source == source, realm_filter)
        )
    if fetched is not None and fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=timezone.utc)  # la columna guarda UTC sin tz
    return fetched


def _ensure_realm_registry(client: BlizzardClient) -> None:
    """Puebla la tabla realms si está vacía (primer arranque contra una BD nueva).

    Sin esto, en un despliegue limpio (BD cloud recién creada) SCHEDULER_REALMS
    no podría resolverse a connected_realm_ids y ningún tick capturaría nada.
    """
    with SessionLocal() as session:
        have = session.scalar(select(func.count()).select_from(Realm))
    if not have:
        logger.info("Registro de reinos vacío; sincronizándolo desde la API de Blizzard...")
        sync_realms(client)


def capture_market_snapshots() -> None:
    """Un tick del scheduler: snapshot nuevo por reino + metadatos de items nuevos."""
    client = BlizzardClient()
    try:
        _ensure_realm_registry(client)

        realm_ids = _tracked_connected_realm_ids()
        if not realm_ids and not settings.scheduler_include_commodities:
            logger.warning(
                "No hay reinos que capturar: sincroniza alguno primero (sync_realms_batch.py "
                "o el botón del dashboard) o define SCHEDULER_REALMS en el .env"
            )
            return

        logger.info("Tick de captura: %s reinos %s", len(realm_ids), realm_ids)
        saved = skipped = failed = 0
        for cr_id in realm_ids:
            try:
                count = save_realm_auctions(client, cr_id, since=_last_fetched_at(cr_id, "realm"))
                if count is None:
                    skipped += 1
                    continue
                saved += 1
                snap_id = latest_realm_snapshot_id(cr_id)
                if snap_id:
                    resolve_items(client, item_ids_in_snapshot(snap_id))
            except Exception:
                failed += 1
                logger.exception("Realm %s: fallo capturando el snapshot", cr_id)

        if settings.scheduler_include_commodities:
            try:
                count = save_commodities(client, since=_last_fetched_at(None, "commodities"))
                if count is not None:
                    snap_id = latest_snapshot_id("commodities")
                    if snap_id:
                        resolve_items(client, item_ids_in_snapshot(snap_id))
            except Exception:
                logger.exception("Commodities: fallo capturando el snapshot")
    finally:
        client.close()

    logger.info(
        "Tick completado: %s snapshots nuevos, %s sin cambios, %s fallos",
        saved, skipped, failed,
    )


def main() -> None:
    init_db()

    if "--once" in sys.argv[1:]:
        # Un tick y salir: el "cada cuánto" lo decide quien nos invoca
        # (GitHub Actions, cron, Task Scheduler...), no un proceso residente.
        capture_market_snapshots()
        return

    interval = settings.scheduler_interval_minutes

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        capture_market_snapshots,
        "interval",
        minutes=interval,
        next_run_time=datetime.now(timezone.utc),  # primera captura al arrancar
        coalesce=True,        # si se acumulan ejecuciones perdidas, solo una
        max_instances=1,      # nunca dos capturas solapadas
        misfire_grace_time=600,
    )
    logger.info(
        "Scheduler iniciado: captura cada %s min (reinos: %s, commodities: %s). Ctrl+C para parar.",
        interval,
        settings.scheduler_realms or "todos los que tengan histórico",
        "sí" if settings.scheduler_include_commodities else "no",
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler detenido")


if __name__ == "__main__":
    main()
