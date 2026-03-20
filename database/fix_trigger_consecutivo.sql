-- Script para corregir consecutivos por tipo de documento
-- Objetivo:
-- 1) Consecutivo numerico con formato fijo de 4 digitos (0001, 0002, ...)
-- 2) Consecutivo independiente por tipo (id_tipo)

DELIMITER ;;

-- Ajustar restriccion de unicidad: por tipo + consecutivo
ALTER TABLE documentos DROP INDEX consecutivo ;;
ALTER TABLE documentos ADD UNIQUE KEY uq_documentos_tipo_consecutivo (id_tipo, consecutivo) ;;

-- Eliminar el trigger existente
DROP TRIGGER IF EXISTS `trg_doc_set_consecutivo` ;;

-- Crear el trigger corregido
CREATE TRIGGER `trg_doc_set_consecutivo` BEFORE UPDATE ON `documentos` FOR EACH ROW
BEGIN
    DECLARE v_consecutivo INT;

    -- Solo al pasar a FINALIZADO y si aún no tiene consecutivo
    IF NEW.estado = 'FINALIZADO' AND (NEW.consecutivo IS NULL OR NEW.consecutivo = '') THEN
        -- Obtener y bloquear el registro en control_consecutivos
        SELECT ultimo_numero
          INTO v_consecutivo
          FROM control_consecutivos
          WHERE id_tipo_documento = NEW.id_tipo
          FOR UPDATE;

        -- Incrementar el contador
        SET v_consecutivo = IFNULL(v_consecutivo, 0) + 1;

        -- Asignar consecutivo con padding a 4 digitos (ej: 0001, 0002)
        SET NEW.consecutivo = LPAD(v_consecutivo, 4, '0');

        -- Actualizar el contador en la tabla de control
        UPDATE control_consecutivos
           SET ultimo_numero = v_consecutivo
         WHERE id_tipo_documento = NEW.id_tipo;
    END IF;
END ;;

DELIMITER ;

-- Verificar que el trigger se creó correctamente
SHOW TRIGGERS LIKE 'trg_doc_set_consecutivo';
