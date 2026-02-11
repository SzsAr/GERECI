-- Script para corregir el trigger de asignación de consecutivos
-- Problema: El campo consecutivo es VARCHAR pero se estaba asignando un INT

DELIMITER ;;

-- Eliminar el trigger existente
DROP TRIGGER IF EXISTS `trg_doc_set_consecutivo` ;;

-- Crear el trigger corregido
CREATE TRIGGER `trg_doc_set_consecutivo` BEFORE UPDATE ON `documentos` FOR EACH ROW
BEGIN
    DECLARE v_consecutivo INT;
    DECLARE v_consecutivo_str VARCHAR(255);

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
        
        -- Convertir a VARCHAR con formato de 4 dígitos (ej: 0001, 0002)
        SET v_consecutivo_str = LPAD(v_consecutivo, 4, '0');
        
        -- Asignar el consecutivo formateado al documento
        SET NEW.consecutivo = v_consecutivo_str;

        -- Actualizar el contador en la tabla de control
        UPDATE control_consecutivos
           SET ultimo_numero = v_consecutivo
         WHERE id_tipo_documento = NEW.id_tipo;
    END IF;
END ;;

DELIMITER ;

-- Verificar que el trigger se creó correctamente
SHOW TRIGGERS LIKE 'trg_doc_set_consecutivo';
