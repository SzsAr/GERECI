-- Crear tabla de cargos
CREATE TABLE `cargos` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `nombre` VARCHAR(100) NOT NULL,
  `descripcion` VARCHAR(200) DEFAULT NULL,
  `estado` TINYINT(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Insertar cargos de ejemplo
INSERT INTO `cargos` (`id`, `nombre`, `descripcion`, `estado`) VALUES
(1, 'Coordinador de Sistemas de Informacion', 'Coordinador del área de sistemas', 1),
(2, 'Gerente General', 'Gerente de la institución', 1),
(3, 'Jefe de Juridica', 'Responsable del área jurídica', 1),
(4, 'Coordinador Administrativo', 'Coordinador del área administrativa', 1);

-- Agregar columna id_cargo a usuarios
ALTER TABLE `usuarios` 
ADD COLUMN `id_cargo` INT DEFAULT NULL AFTER `id_rol`,
ADD CONSTRAINT `usuarios_ibfk_cargo` 
FOREIGN KEY (`id_cargo`) REFERENCES `cargos` (`id`) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- Primero eliminar la foreign key constraint si existe
ALTER TABLE `firmas_digitales` 
DROP FOREIGN KEY `firmas_digitales_ibfk_1`;

-- Eliminar el constraint UNIQUE de id_documento en firmas_digitales
ALTER TABLE `firmas_digitales` 
DROP INDEX `unico_documento_firmado`;

-- Recrear la foreign key sin UNIQUE constraint
ALTER TABLE `firmas_digitales`
ADD CONSTRAINT `firmas_digitales_ibfk_1` 
FOREIGN KEY (`id_documento`) REFERENCES `documentos` (`id`) 
ON DELETE CASCADE ON UPDATE CASCADE;

-- Agregar índice compuesto para evitar que un mismo usuario firme dos veces el mismo documento
ALTER TABLE `firmas_digitales`
ADD UNIQUE KEY `unico_usuario_documento` (`id_usuario`, `id_documento`);
