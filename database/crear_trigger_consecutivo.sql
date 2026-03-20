-- Trigger para asignar consecutivo automatico por tipo cuando un documento pasa a FINALIZADO
-- Formato del consecutivo: numerico con 4 digitos (0001, 0002, ...)
-- Unicidad: por (id_tipo, consecutivo)

DELIMITER //

-- Asegurar que el consecutivo pueda repetirse entre tipos distintos
ALTER TABLE documentos DROP INDEX consecutivo //
ALTER TABLE documentos ADD UNIQUE KEY uq_documentos_tipo_consecutivo (id_tipo, consecutivo) //

DROP TRIGGER IF EXISTS trg_doc_set_consecutivo //

CREATE TRIGGER trg_doc_set_consecutivo
BEFORE UPDATE ON documentos
FOR EACH ROW
BEGIN
    DECLARE v_consecutivo INT;
    
    -- Si el nuevo estado es FINALIZADO y no tiene consecutivo
    IF NEW.estado = 'FINALIZADO' AND (NEW.consecutivo IS NULL OR NEW.consecutivo = '') THEN
        -- Obtener y bloquear el contador del tipo de documento
        SELECT ultimo_numero
          INTO v_consecutivo
          FROM control_consecutivos
          WHERE id_tipo_documento = NEW.id_tipo
          FOR UPDATE;

        -- Incrementar y asignar con padding
        SET v_consecutivo = IFNULL(v_consecutivo, 0) + 1;
        SET NEW.consecutivo = LPAD(v_consecutivo, 4, '0');

        -- Persistir nuevo contador
        UPDATE control_consecutivos
           SET ultimo_numero = v_consecutivo
         WHERE id_tipo_documento = NEW.id_tipo;
    END IF;
    
END //

DELIMITER ;
