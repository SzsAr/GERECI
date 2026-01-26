-- Agregar columna para almacenar valores de campos de plantilla
ALTER TABLE documentos 
ADD COLUMN valores_campos JSON DEFAULT NULL 
COMMENT 'JSON con los valores de los campos dinámicos de la plantilla';
