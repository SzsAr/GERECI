"""
Utilidades para generar y manipular documentos Word y PDF
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from docxtpl import DocxTemplate
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

# Rutas base para documentos
MEDIA_DIR = Path(__file__).parent.parent.parent / "media"
DOCUMENTOS_DIR = MEDIA_DIR / "documentos"
FIRMAS_DIR = MEDIA_DIR / "firmas"

# Crear directorios si no existen
DOCUMENTOS_DIR.mkdir(parents=True, exist_ok=True)
FIRMAS_DIR.mkdir(parents=True, exist_ok=True)


def generar_word_desde_plantilla(
    plantilla_path: str,
    documento_id: int,
    valores_campos: Optional[Dict[str, Any]] = None,
    output_filename: Optional[str] = None
) -> str:
    """
    Generar un documento Word desde una plantilla usando docxtpl.
    Reemplaza los placeholders {{campo}} con los valores proporcionados.
    
    Args:
        plantilla_path: Ruta a la plantilla .docx
        documento_id: ID del documento (para nombrar el archivo generado)
        valores_campos: Dict con pares {nombre_campo: valor}
    
    Returns:
        Ruta relativa del documento generado (/static/documentos/...)
    """
    try:
        # Usar valores vacíos si no se proporcionan
        if not valores_campos:
            valores_campos = {}
        
        # Cargar plantilla con docxtpl
        doc_template = DocxTemplate(plantilla_path)
        
        # Renderizar con los valores
        doc_template.render(valores_campos)

        # Reemplazar placeholders en cuadros de texto, parrafos y tablas
        if valores_campos:
            _reemplazar_en_container(doc_template.docx, valores_campos)
            for section in doc_template.docx.sections:
                _reemplazar_en_container(section.header, valores_campos)
                _reemplazar_en_container(section.footer, valores_campos)
        
        # Guardar documento generado
        if not output_filename:
            output_filename = f"{documento_id}_borrador.docx"
        output_path = DOCUMENTOS_DIR / output_filename
        doc_template.save(str(output_path))
        
        # Retornar ruta relativa para servir desde /static
        relative_path = f"/static/documentos/{output_filename}"
        logger.info(f"Documento Word generado: {relative_path}")
        return relative_path
    
    except Exception as e:
        logger.error(f"Error al generar documento Word: {e}")
        raise Exception(f"Error al generar documento: {str(e)}")


def _reemplazar_en_container(container: Any, valores: Dict[str, Any]) -> None:
    """
    Reemplaza placeholders {{campo}} dentro de parrafos, tablas y cuadros de texto.
    """
    try:
        _reemplazar_en_parrafos(container, valores)
        _reemplazar_en_tablas(container, valores)
        _reemplazar_en_textboxes(container, valores)
    except Exception as e:
        logger.warning(f"No se pudo reemplazar texto en el documento: {e}")


def _reemplazar_en_parrafos(container: Any, valores: Dict[str, Any]) -> None:
    for p in getattr(container, "paragraphs", []):
        _reemplazar_en_runs(p, valores)


def _reemplazar_en_tablas(container: Any, valores: Dict[str, Any]) -> None:
    for table in getattr(container, "tables", []):
        for row in table.rows:
            for cell in row.cells:
                _reemplazar_en_parrafos(cell, valores)
                _reemplazar_en_tablas(cell, valores)


def _reemplazar_en_runs(paragraph: Any, valores: Dict[str, Any]) -> None:
    runs = getattr(paragraph, "runs", [])
    if not runs:
        return

    combined = "".join([r.text or "" for r in runs])
    for key, value in valores.items():
        placeholder = f"{{{{{key}}}}}"
        replacement = "" if value is None else str(value)
        if placeholder in combined:
            combined = combined.replace(placeholder, replacement)

    runs[0].text = combined
    for r in runs[1:]:
        r.text = ""


def _reemplazar_en_textboxes(container: Any, valores: Dict[str, Any]) -> None:
    try:
        element = container._element
    except Exception:
        return

    try:
        for txbx in element.xpath(".//w:txbxContent"):
            texts = txbx.xpath(".//w:t")
            if not texts:
                continue

            combined = "".join([t.text or "" for t in texts])

            for key, value in valores.items():
                placeholder = f"{{{{{key}}}}}"
                replacement = "" if value is None else str(value)
                if placeholder in combined:
                    combined = combined.replace(placeholder, replacement)

            # Reescribir el contenido consolidado en el primer nodo y vaciar el resto
            texts[0].text = combined
            for t in texts[1:]:
                t.text = ""
    except Exception as e:
        logger.warning(f"No se pudo reemplazar texto en cuadros: {e}")


def incrustar_firma(
    documento_path: str,
    documento_id: int,
    usuario_nombre: str,
    usuario_cargo: str,
    firma_imagen_path: Optional[str] = None
) -> str:
    """
    Incrustar firma (imagen + nombre + cargo) en el documento Word.
    
    Args:
        documento_path: Ruta al documento Word
        documento_id: ID del documento
        usuario_nombre: Nombre del usuario que firma
        usuario_cargo: Cargo del usuario
        firma_imagen_path: Ruta a la imagen de firma (opcional)
    
    Returns:
        Ruta relativa del documento con firma incrustrada
    """
    try:
        # Cargar documento
        doc = Document(documento_path)
        
        # Agregar párrafo de firma
        doc.add_paragraph()  # Espacio
        p_firma = doc.add_paragraph()
        p_firma.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Agregar imagen de firma si existe
        if firma_imagen_path and os.path.exists(firma_imagen_path):
            try:
                # Redimensionar imagen de firma a 1 inch de ancho
                p_firma.add_run().add_picture(firma_imagen_path, width=Inches(1.5))
                doc.add_paragraph()  # Espacio entre imagen y nombre
            except Exception as e:
                logger.warning(f"No se pudo agregar imagen de firma: {e}")
        
        # Agregar nombre y cargo
        p_nombre = doc.add_paragraph()
        p_nombre.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_nombre = p_nombre.add_run(usuario_nombre)
        run_nombre.bold = True
        run_nombre.font.size = Pt(11)
        
        p_cargo = doc.add_paragraph()
        p_cargo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_cargo = p_cargo.add_run(usuario_cargo)
        run_cargo.font.size = Pt(10)
        run_cargo.font.color.rgb = RGBColor(128, 128, 128)
        
        # Guardar documento con firma
        output_filename = f"{documento_id}_firmado.docx"
        output_path = DOCUMENTOS_DIR / output_filename
        doc.save(str(output_path))
        
        relative_path = f"/static/documentos/{output_filename}"
        logger.info(f"Firma incrustranda en documento: {relative_path}")
        return relative_path
    
    except Exception as e:
        logger.error(f"Error al incrustar firma: {e}")
        raise Exception(f"Error al incrustar firma: {str(e)}")


def convertir_word_a_pdf(
    documento_word_path: str,
    documento_id: int,
    tipo_documento: Optional[str] = None,
    consecutivo: Optional[str] = None
) -> Optional[str]:
    """
    Convertir documento Word a PDF usando LibreOffice.
    
    Args:
        documento_word_path: Ruta al documento Word (.docx)
        documento_id: ID del documento
        tipo_documento: Nombre del tipo de documento (ej: "RESOLUCION", "CIRCULAR")
        consecutivo: Consecutivo asignado (ej: "0220")
    
    Returns:
        Ruta relativa del PDF generado, o None si falla la conversión
    """
    try:
        # Obtener ruta de LibreOffice
        libreoffice_path = _obtener_ruta_libreoffice()
        if not libreoffice_path:
            logger.warning("LibreOffice no encontrado. PDF no será generado.")
            return None
        
        # Comando para convertir a PDF
        output_dir = str(DOCUMENTOS_DIR)
        cmd = [
            libreoffice_path,
            "--headless",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            documento_word_path
        ]
        
        # Ejecutar conversión
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"Error en conversión a PDF: {result.stderr}")
            return None
        
        # Obtener nombre del PDF generado
        word_filename = Path(documento_word_path).stem
        pdf_filename = f"{word_filename}.pdf"
        pdf_path = DOCUMENTOS_DIR / pdf_filename
        
        if not pdf_path.exists():
            logger.warning(f"PDF no generado: {pdf_path}")
            return None
        
        # Renombrar a formato estándar: TIPO_DOCUMENTO_N°_CONSECUTIVO.pdf
        if tipo_documento and consecutivo:
            # Limpiar nombre del tipo para archivo
            tipo_limpio = tipo_documento.upper().replace(" ", "_")
            final_pdf_name = f"{tipo_limpio}_N°_{consecutivo}.pdf"
        else:
            final_pdf_name = f"{documento_id}_final.pdf"
        
        final_pdf_path = DOCUMENTOS_DIR / final_pdf_name
        pdf_path.rename(final_pdf_path)
        
        relative_path = f"/static/documentos/{final_pdf_name}"
        logger.info(f"PDF generado: {relative_path}")
        return relative_path
    
    except subprocess.TimeoutExpired:
        logger.error("Timeout en conversión a PDF")
        return None
    except Exception as e:
        logger.error(f"Error al convertir Word a PDF: {e}")
        return None


def _obtener_ruta_libreoffice() -> Optional[str]:
    """
    Obtener ruta del ejecutable de LibreOffice según el SO.
    """
    import sys
    import os

    # Permitir sobreescribir la ruta por variable de entorno
    env_path = os.getenv("LIBREOFFICE_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    if sys.platform == "win32":
        # Rutas comunes en Windows
        rutas_posibles = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
    elif sys.platform == "darwin":
        # macOS
        rutas_posibles = [
            "/Applications/LibreOffice.app/Contents/MacOS/soffice"
        ]
    else:
        # Linux
        rutas_posibles = [
            "/usr/bin/libreoffice",
            "/usr/bin/soffice"
        ]
    
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta
    
    # Intentar encontrar en PATH
    try:
        result = subprocess.run(
            ["which", "soffice"] if sys.platform != "win32" else ["where", "soffice.exe"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    return None


def guardar_firma_usuario(usuario_id: int, imagen_bytes: bytes) -> str:
    """
    Guardar imagen de firma de usuario.
    
    Args:
        usuario_id: ID del usuario
        imagen_bytes: Bytes de la imagen
    
    Returns:
        Ruta relativa de la firma guardada
    """
    try:
        # Guardar imagen
        filename = f"firma_usuario_{usuario_id}.png"
        filepath = FIRMAS_DIR / filename
        
        with open(filepath, 'wb') as f:
            f.write(imagen_bytes)
        
        relative_path = f"/static/firmas/{filename}"
        logger.info(f"Firma guardada: {relative_path}")
        return relative_path
    
    except Exception as e:
        logger.error(f"Error al guardar firma: {e}")
        raise Exception(f"Error al guardar firma: {str(e)}")
