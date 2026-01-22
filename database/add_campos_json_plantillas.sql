-- Agregar campo JSON para definir campos dinámicos de cada plantilla
ALTER TABLE `plantillas`
ADD COLUMN `campos_json` JSON NULL AFTER `ruta_almacenamiento`;

-- Opcional: valor por defecto vacío
-- ALTER TABLE `plantillas` ALTER `campos_json` SET DEFAULT NULL;
