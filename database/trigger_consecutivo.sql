-- Trigger: asigna consecutivo al finalizar documento
-- Aplícalo en la base de datos GERECI

DELIMITER $$
DROP TRIGGER IF EXISTS trg_doc_set_consecutivo $$
CREATE TRIGGER trg_doc_set_consecutivo
BEFORE UPDATE ON documentos
FOR EACH ROW
BEGIN
    DECLARE v_consecutivo INT;

    -- Solo cuando pasa a FINALIZADO y no tiene consecutivo
    IF NEW.estado = 'FINALIZADO' AND (NEW.consecutivo IS NULL OR NEW.consecutivo = '') THEN
        -- Leer y bloquear el consecutivo actual
        SELECT ultimo_numero
          INTO v_consecutivo
          FROM control_consecutivos
          WHERE id_tipo_documento = NEW.id_tipo
          FOR UPDATE;

        -- Si no existe registro, crear uno con 0
        IF v_consecutivo IS NULL THEN
            SET v_consecutivo = 0;
            INSERT INTO control_consecutivos (id_tipo_documento, ultimo_numero)
            VALUES (NEW.id_tipo, 0)
            ON DUPLICATE KEY UPDATE ultimo_numero = ultimo_numero;
        END IF;

        -- Asignar siguiente número
        SET v_consecutivo = v_consecutivo + 1;
        SET NEW.consecutivo = v_consecutivo;

        -- Persistir el nuevo último número
        UPDATE control_consecutivos
           SET ultimo_numero = v_consecutivo
         WHERE id_tipo_documento = NEW.id_tipo;
    END IF;
END $$
DELIMITER ;
