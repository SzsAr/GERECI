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
-- Table structure for table `permisos`
--

DROP TABLE IF EXISTS `permisos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permisos` (
  `id_modulo` int NOT NULL,
  `id_rol` tinyint NOT NULL,
  `insertar` tinyint(1) NOT NULL DEFAULT '0',
  `actualizar` tinyint(1) NOT NULL DEFAULT '0',
  `seleccionar` tinyint(1) NOT NULL DEFAULT '0',
  `borrar` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id_modulo`,`id_rol`),
  KEY `id_rol` (`id_rol`),
  CONSTRAINT `permisos_ibfk_1` FOREIGN KEY (`id_modulo`) REFERENCES `modulos` (`id_modulo`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `permisos_ibfk_2` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permisos`
--

LOCK TABLES `permisos` WRITE;
/*!40000 ALTER TABLE `permisos` DISABLE KEYS */;
INSERT INTO `permisos` VALUES (1,1,1,1,1,1),(1,2,0,0,0,0),(1,3,0,0,0,0),(1,4,0,0,0,0),(2,1,1,1,1,1),(2,2,1,0,1,0),(2,3,0,0,0,0),(2,4,0,0,0,0),(3,1,1,1,1,1),(3,2,0,0,0,0),(3,3,0,0,0,0),(3,4,0,0,0,0),(4,1,1,1,1,1),(4,2,0,0,0,0),(4,3,0,0,0,0),(4,4,0,0,0,0),(5,1,1,1,1,1),(5,2,0,0,0,0),(5,3,0,0,0,0),(5,4,0,0,0,0),(6,1,1,1,1,1),(6,2,1,1,1,0),(6,3,1,1,1,0),(6,4,1,1,1,0),(7,1,1,1,1,1),(7,2,0,0,0,0),(7,3,0,0,0,0),(7,4,0,0,0,0),(8,1,1,1,1,1),(8,2,1,1,1,0),(8,3,1,1,1,0),(8,4,1,1,1,0),(9,1,1,1,1,1),(9,2,0,0,1,0),(9,3,0,0,1,0),(9,4,0,0,1,0),(10,1,1,1,1,1),(10,2,1,1,1,0),(10,3,1,1,1,0),(10,4,1,1,1,0),(11,1,1,1,1,1),(11,2,0,0,0,0),(11,3,0,0,0,0),(11,4,0,0,0,0);
/*!40000 ALTER TABLE `permisos` ENABLE KEYS */;
UNLOCK TABLES;
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
