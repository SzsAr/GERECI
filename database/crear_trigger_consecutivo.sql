-- Trigger para asignar consecutivo automáticamente cuando un documento es FINALIZADO

DELIMITER //

DROP TRIGGER IF EXISTS tr_asignar_consecutivo_finalizacion //

CREATE TRIGGER tr_asignar_consecutivo_finalizacion 
BEFORE UPDATE ON documentos
FOR EACH ROW
BEGIN
    DECLARE v_consecutivo VARCHAR(255);
    DECLARE v_contador INT;
    DECLARE v_id_tipo_str VARCHAR(2);
    
    -- Si el nuevo estado es FINALIZADO y no tiene consecutivo
    IF NEW.estado = 'FINALIZADO' AND (OLD.estado != 'FINALIZADO' OR OLD.consecutivo IS NULL) THEN
        
        -- Si el consecutivo aún no está asignado, generarlo
        IF NEW.consecutivo IS NULL THEN
            
            -- Formatear id_tipo a 2 dígitos
            SET v_id_tipo_str = LPAD(NEW.id_tipo, 2, '0');
            
            -- Obtener el contador de documentos finalizados del mismo tipo
            -- Contar documentos del mismo tipo que ya tienen consecutivo
            SELECT COUNT(*) + 1 INTO v_contador
            FROM documentos 
            WHERE id_tipo = NEW.id_tipo 
            AND estado = 'FINALIZADO' 
            AND consecutivo IS NOT NULL;
            
            -- Generar consecutivo en formato: TIPO-CONTADOR
            -- Ejemplo: 01-0001 para primera circular, 01-0002 para segunda
            SET v_consecutivo = CONCAT(v_id_tipo_str, '-', LPAD(v_contador, 4, '0'));
            
            -- Asignar el consecutivo generado
            SET NEW.consecutivo = v_consecutivo;
            
        END IF;
        
    END IF;
    
END //

DELIMITER ;
