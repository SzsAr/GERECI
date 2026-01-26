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
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(30) NOT NULL,
  `documento` varchar(30) NOT NULL,
  `username` varchar(255) DEFAULT NULL,
  `pass_hash` varchar(255) NOT NULL,
  `id_rol` tinyint NOT NULL,
  `id_cargo` int DEFAULT NULL,
  `firma` varchar(500) DEFAULT NULL,
  `estado` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`),
  KEY `id_rol` (`id_rol`),
  KEY `usuarios_ibfk_cargo` (`id_cargo`),
  CONSTRAINT `usuarios_ibfk_1` FOREIGN KEY (`id_rol`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `usuarios_ibfk_cargo` FOREIGN KEY (`id_cargo`) REFERENCES `cargos` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Develop','123456789','dev','$2b$12$dqHqOjmV3VJKqnvcsFd4aOc/t4LpECbs8T5UJBk47sFUr9PwRsmkS',1,6,'/static/firmas/db55cb1c-476d-480b-9d69-74e0a348eed8.png',1),(2,'Santiago','123456789','san','$2b$12$dqHqOjmV3VJKqnvcsFd4aOc/t4LpECbs8T5UJBk47sFUr9PwRsmkS',4,1,'string',1),(4,'Martin','987456123','ger','$2b$12$LVboPouN.q9w3NR54cwOQu.Q0QwZUYZ6kH/k/XsFo2MtZzkNOeCPK',2,2,NULL,1),(6,'Luisa','123645789','jur','$2b$12$bGIeW5rvfdj8BXRJI8pn8O6A0XAWGraf3Qgg6QjHgrKCGeavscyZK',3,3,NULL,1);
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
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
