-- Añade la columna icon a la tabla items si no existe.
-- Ejecutar una sola vez en la BD existente:
--   psql -d <nombre_bbdd> -f migrate_add_icon.sql

ALTER TABLE items ADD COLUMN IF NOT EXISTS icon TEXT;

-- preview_item crudo de la API (stats, daño de arma, descripción de
-- consumibles...) para el tooltip al pasar el ratón sobre el icono.
ALTER TABLE items ADD COLUMN IF NOT EXISTS tooltip_data JSONB;

-- Subclase (Tela/Cuero/Malla/Placas...) y ranura de equipo (Cabeza/Manos...)
-- para los filtros de la barra lateral.
ALTER TABLE items ADD COLUMN IF NOT EXISTS item_subclass TEXT;
ALTER TABLE items ADD COLUMN IF NOT EXISTS inventory_type TEXT;
CREATE INDEX IF NOT EXISTS ix_items_quality ON items (quality);
CREATE INDEX IF NOT EXISTS ix_items_item_subclass ON items (item_subclass);
CREATE INDEX IF NOT EXISTS ix_items_inventory_type ON items (inventory_type);
