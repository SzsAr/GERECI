CREATE DATABASE IF NOT EXISTS `GERECI`;
USE `GERECI`;

-- 1. Primero crear TODAS las tablas SIN foreign keys
CREATE TABLE IF NOT EXISTS `roles` (
    `id` TINYINT NOT NULL AUTO_INCREMENT UNIQUE,
    `nombre` VARCHAR(30),
    `estado` TINYINT DEFAULT 1,
    PRIMARY KEY(`id`)
);

CREATE TABLE IF NOT EXISTS `modulos` (
    `id_modulo` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `nombre_modulo` VARCHAR(30),
    `estado` BOOLEAN,
    PRIMARY KEY(`id_modulo`)
);

CREATE TABLE IF NOT EXISTS `tipos_documentos` (
    `id` TINYINT NOT NULL AUTO_INCREMENT UNIQUE,
    `nombre` VARCHAR(30) NOT NULL,
    `codigo` CHAR(1) NOT NULL,
    `requiere_juridica` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY(`id`)
);

CREATE TABLE IF NOT EXISTS `usuarios` (
    `id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `nombre` VARCHAR(30) NOT NULL,
    `documento` VARCHAR(30) NOT NULL,
    `username` VARCHAR(255),
    `pass_hash` VARCHAR(255) NOT NULL,
    `id_rol` TINYINT NOT NULL,
    `firma` VARCHAR(500),
    PRIMARY KEY(`id`)
);

CREATE TABLE IF NOT EXISTS `permisos` (
    `id_modulo` INTEGER NOT NULL,
    `id_rol` TINYINT NOT NULL,
    `insertar` BOOLEAN NOT NULL DEFAULT FALSE,
    `actualizar` BOOLEAN NOT NULL DEFAULT FALSE,
    `seleccionar` BOOLEAN NOT NULL DEFAULT FALSE,
    `borrar` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY(`id_modulo`, `id_rol`)
);

CREATE TABLE IF NOT EXISTS `plantillas` (
    `id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `id_tipo` TINYINT NOT NULL,
    `nombre` VARCHAR(50) NOT NULL,
    `nombre_archivo` VARCHAR(255) NOT NULL,
    `ruta_almacenamiento` VARCHAR(500),
    PRIMARY KEY(`id`)
);

CREATE TABLE IF NOT EXISTS `documentos` (
    `id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `id_tipo` TINYINT NOT NULL,
    `id_plantilla` INTEGER NOT NULL,
    `usuario_genera` INTEGER NOT NULL,
    `Asunto` VARCHAR(255) NOT NULL,
    `consecutivo` VARCHAR(255) UNIQUE,
    `fecha_creacion` DATETIME NOT NULL DEFAULT NOW(),
    `fecha_emision` DATE,
    `ruta_word_generado` VARCHAR(500),
    `ruta_pdf_final` VARCHAR(500),
    `estado` ENUM('BORRADOR', 'EN_REVISION_JURIDICA', 'EN_REVISION_GERENCIAL', 'APROBADO_JURIDICA', 'FIRMADO', 'DEVUELTO_JURIDICA', 'DEVUELTO_GERENCIA', 'PENDIENTE_FINALIZACION', 'FINALIZADO') NOT NULL DEFAULT 'BORRADOR',
    PRIMARY KEY(`id`)
);

CREATE TABLE IF NOT EXISTS `tareas_pendientes` (
    `id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `id_documento` INTEGER NOT NULL,
    `id_usuario` INTEGER NOT NULL,
    `tipo_tarea` ENUM('REVISAR_JURIDICA', 'REVISAR_GERENCIA', 'FIRMAR', 'FINALIZAR') NOT NULL,
    `fecha_asignacion` DATETIME NOT NULL DEFAULT NOW(),
    `completada` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY(`id`)
);

CREATE TABLE IF NOT EXISTS `observaciones` (
    `id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `id_documento` INTEGER NOT NULL,
    `id_usuario` INTEGER NOT NULL,
    `fecha` DATETIME NOT NULL DEFAULT NOW(),
    `tipo` ENUM('JURIDICA', 'GERENCIA'),
    `descripcion` TEXT NOT NULL,
    PRIMARY KEY(`id`)
);

CREATE TABLE IF NOT EXISTS `control_consecutivos` (
    `id_tipo_documento` TINYINT NOT NULL UNIQUE,
    `ultimo_numero` INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(`id_tipo_documento`)
);

CREATE TABLE IF NOT EXISTS `firmas_digitales` (
    `id` INTEGER NOT NULL AUTO_INCREMENT UNIQUE,
    `id_usuario` INTEGER NOT NULL,
    `id_documento` INTEGER NOT NULL,
    `fecha_firma` DATETIME NOT NULL DEFAULT NOW(),
    PRIMARY KEY(`id`),
    UNIQUE KEY `unico_documento_firmado` (`id_documento`)
);

-- 2. AHORA agregar FOREIGN KEYS en orden correcto

-- Usuarios → Roles (CORREGIDO: estaba al revés)
ALTER TABLE `usuarios`
ADD FOREIGN KEY(`id_rol`) REFERENCES `roles`(`id`)
ON UPDATE CASCADE ON DELETE RESTRICT;

-- Permisos → Módulos
ALTER TABLE `permisos`
ADD FOREIGN KEY(`id_modulo`) REFERENCES `modulos`(`id_modulo`)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Permisos → Roles
ALTER TABLE `permisos`
ADD FOREIGN KEY(`id_rol`) REFERENCES `roles`(`id`)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Plantillas → Tipos Documentos
ALTER TABLE `plantillas`
ADD FOREIGN KEY(`id_tipo`) REFERENCES `tipos_documentos`(`id`)
ON UPDATE CASCADE ON DELETE RESTRICT;

-- Documentos → Plantillas
ALTER TABLE `documentos`
ADD FOREIGN KEY(`id_plantilla`) REFERENCES `plantillas`(`id`)
ON UPDATE CASCADE ON DELETE RESTRICT;

-- Documentos → Tipos Documentos (FALTABA)
ALTER TABLE `documentos`
ADD FOREIGN KEY(`id_tipo`) REFERENCES `tipos_documentos`(`id`)
ON UPDATE CASCADE ON DELETE RESTRICT;

-- Documentos → Usuarios (quien genera)
ALTER TABLE `documentos`
ADD FOREIGN KEY(`usuario_genera`) REFERENCES `usuarios`(`id`)
ON UPDATE CASCADE ON DELETE RESTRICT;

-- Tareas Pendientes → Documentos
ALTER TABLE `tareas_pendientes`
ADD FOREIGN KEY(`id_documento`) REFERENCES `documentos`(`id`)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Tareas Pendientes → Usuarios (a quien se asigna)
ALTER TABLE `tareas_pendientes`
ADD FOREIGN KEY(`id_usuario`) REFERENCES `usuarios`(`id`)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Observaciones → Documentos
ALTER TABLE `observaciones`
ADD FOREIGN KEY(`id_documento`) REFERENCES `documentos`(`id`)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Observaciones → Usuarios (quien observa)
ALTER TABLE `observaciones`
ADD FOREIGN KEY(`id_usuario`) REFERENCES `usuarios`(`id`)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Control Consecutivos → Tipos Documentos
ALTER TABLE `control_consecutivos`
ADD FOREIGN KEY(`id_tipo_documento`) REFERENCES `tipos_documentos`(`id`)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Firmas Digitales → Documentos
ALTER TABLE `firmas_digitales`
ADD FOREIGN KEY(`id_documento`) REFERENCES `documentos`(`id`)
ON UPDATE CASCADE ON DELETE CASCADE;

-- Firmas Digitales → Usuarios (quien firma)
ALTER TABLE `firmas_digitales`
ADD FOREIGN KEY(`id_usuario`) REFERENCES `usuarios`(`id`)
ON UPDATE CASCADE ON DELETE CASCADE;