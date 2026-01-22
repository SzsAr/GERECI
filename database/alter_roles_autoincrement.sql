-- Desactivar foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Modificar la columna para agregar AUTO_INCREMENT
ALTER TABLE `roles` MODIFY COLUMN `id` TINYINT NOT NULL AUTO_INCREMENT;

-- Reactivar foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

