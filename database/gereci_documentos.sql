-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: gereci
-- ------------------------------------------------------
-- Server version	9.5.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '06568d03-f233-11f0-8a7e-bcfce7e55e31:1-226';

--
-- Table structure for table `documentos`
--

DROP TABLE IF EXISTS `documentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `documentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `id_tipo` tinyint NOT NULL,
  `id_plantilla` int NOT NULL,
  `usuario_genera` int NOT NULL,
  `Asunto` varchar(255) NOT NULL,
  `consecutivo` varchar(255) DEFAULT NULL,
  `fecha_creacion` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `fecha_emision` date DEFAULT NULL,
  `ruta_word_generado` varchar(500) DEFAULT NULL,
  `ruta_pdf_final` varchar(500) DEFAULT NULL,
  `estado` enum('BORRADOR','EN_REVISION_JURIDICA','EN_REVISION_GERENCIAL','APROBADO_JURIDICA','FIRMADO','DEVUELTO_JURIDICA','DEVUELTO_GERENCIA','PENDIENTE_FINALIZACION','FINALIZADO') NOT NULL DEFAULT 'BORRADOR',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  UNIQUE KEY `uq_documentos_tipo_consecutivo` (`id_tipo`,`consecutivo`),
  KEY `id_plantilla` (`id_plantilla`),
  KEY `id_tipo` (`id_tipo`),
  KEY `usuario_genera` (`usuario_genera`),
  CONSTRAINT `documentos_ibfk_1` FOREIGN KEY (`id_plantilla`) REFERENCES `plantillas` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `documentos_ibfk_2` FOREIGN KEY (`id_tipo`) REFERENCES `tipos_documentos` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `documentos_ibfk_3` FOREIGN KEY (`usuario_genera`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documentos`
--

LOCK TABLES `documentos` WRITE;
/*!40000 ALTER TABLE `documentos` DISABLE KEYS */;
INSERT INTO `documentos` VALUES (5,1,5,1,'Semana Santa',NULL,'2026-01-26 09:24:14',NULL,NULL,NULL,'BORRADOR');
/*!40000 ALTER TABLE `documentos` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `trg_doc_set_consecutivo` BEFORE UPDATE ON `documentos` FOR EACH ROW BEGIN
    DECLARE v_consecutivo INT;

    -- Solo al pasar a FINALIZADO y si aún no tiene consecutivo
    IF NEW.estado = 'FINALIZADO' AND (NEW.consecutivo IS NULL OR NEW.consecutivo = '') THEN
        SELECT ultimo_numero
          INTO v_consecutivo
          FROM control_consecutivos
          WHERE id_tipo_documento = NEW.id_tipo
          FOR UPDATE;

        SET v_consecutivo = IFNULL(v_consecutivo, 0) + 1;
        SET NEW.consecutivo = LPAD(v_consecutivo, 4, '0');

        UPDATE control_consecutivos
           SET ultimo_numero = v_consecutivo
         WHERE id_tipo_documento = NEW.id_tipo;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-26  9:40:54
