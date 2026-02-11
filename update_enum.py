from core.database import get_db
from sqlalchemy import text
import sys
sys.path.insert(0, 'backend')

db = next(get_db())
sql = """ALTER TABLE documentos MODIFY COLUMN estado ENUM(
    'BORRADOR',
    'EN_REVISION_JURIDICA',
    'EN_REVISION_GERENCIAL',
    'APROBADO_JURIDICA',
    'APROBADO_GERENCIA',
    'FIRMADO',
    'DEVUELTO_JURIDICA',
    'DEVUELTO_GERENCIA',
    'PENDIENTE_FINALIZACION',
    'FINALIZADO'
) DEFAULT 'BORRADOR'"""
db.execute(text(sql))
db.commit()
print('✓ ENUM actualizado con APROBADO_GERENCIA')
