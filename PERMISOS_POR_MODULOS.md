# Sistema de Permisos por Módulos - GERECI

## Módulos Disponibles

| ID | Nombre | Descripción |
|----|--------|-------------|
| 1  | Usuarios | Gestión de usuarios del sistema |
| 2  | Roles | Gestión de roles y sus propiedades |
| 3  | Módulos | Gestión de módulos del sistema |
| 4  | Permisos | Gestión de permisos por rol y módulo |

## Acciones de Permiso

Los permisos que se pueden asignar son:

- **insertar**: Crear nuevos registros
- **actualizar**: Modificar registros existentes
- **seleccionar**: Ver/consultar registros
- **borrar**: Eliminar registros

## Estructura de la Tabla Permisos

```sql
CREATE TABLE permisos (
    id_modulo INTEGER NOT NULL,
    id_rol TINYINT NOT NULL,
    insertar BOOLEAN NOT NULL DEFAULT FALSE,
    actualizar BOOLEAN NOT NULL DEFAULT FALSE,
    seleccionar BOOLEAN NOT NULL DEFAULT FALSE,
    borrar BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY(id_modulo, id_rol)
);
```

## Implementación en FastAPI

### 1. Importar función de verificación de permisos

```python
from app.crud.permisos import verify_permissions
```

### 2. Usar en endpoints

```python
from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_user

router = APIRouter()
modulo = 1  # ID del módulo

@router.post("/create")
def create_item(
    item: ItemCreate,
    db: Session = Depends(get_db),
    user_token: UserOut = Depends(get_current_user)
):
    # Verificar permiso de insertar
    if not verify_permissions(db, user_token.id_rol, modulo, 'insertar'):
        raise HTTPException(
            status_code=403, 
            detail='Usuario no autorizado'
        )
    # ... resto del código
```

### 3. Acciones y permisos requeridos

| Acción | Permiso |
|--------|---------|
| POST (Crear) | insertar |
| GET (Consultar) | seleccionar |
| PUT (Actualizar) | actualizar |
| DELETE (Eliminar) | borrar |

## Ejemplo: Gestión de Usuarios

El módulo de usuarios ya implementa este sistema:

### Crear usuario
- **Endpoint**: `POST /users/create`
- **Permiso requerido**: Módulo 1, acción `insertar`

### Ver usuario
- **Endpoint**: `GET /users/?username=...`
- **Permiso requerido**: Módulo 1, acción `seleccionar` (solo si no es el mismo usuario)

### Ver todos los usuarios
- **Endpoint**: `GET /users/all`
- **Permiso requerido**: Módulo 1, acción `seleccionar`

### Actualizar usuario
- **Endpoint**: `PUT /users/{user_id}`
- **Permiso requerido**: Módulo 1, acción `actualizar`

### Subir firma
- **Endpoint**: `POST /users/{user_id}/firma`
- **Permiso requerido**: Módulo 1, acción `actualizar`

### Eliminar usuario
- **Endpoint**: `DELETE /users/{user_id}`
- **Permiso requerido**: Módulo 1, acción `borrar`

## Flujo de Verificación

1. Usuario realiza request autenticado
2. Se extrae el `id_rol` del token
3. Se verifica el permiso llamando a `verify_permissions(db, id_rol, modulo, accion)`
4. Si no tiene permiso → HTTPException 403
5. Si tiene permiso → continúa con la lógica del endpoint

## Configurar permisos en BD

Para otorgar permisos a un rol para un módulo:

```sql
INSERT INTO permisos (id_modulo, id_rol, insertar, actualizar, seleccionar, borrar)
VALUES (1, 2, TRUE, TRUE, TRUE, FALSE);
-- Rol 2 puede crear, actualizar y ver usuarios, pero NO puede eliminarlos
```

Para actualizar permisos:

```sql
UPDATE permisos 
SET actualizar = FALSE 
WHERE id_modulo = 1 AND id_rol = 3;
-- Rol 3 ya no puede actualizar usuarios del módulo 1
```

## Función de Verificación

**Ubicación**: `app/crud/permisos.py`

```python
def verify_permissions(db: Session, id_rol: int, id_modulo: int, accion: str) -> bool:
    """
    Verificar si un rol tiene permiso para realizar una acción en un módulo.
    
    Args:
        db: Sesión de base de datos
        id_rol: ID del rol del usuario
        id_modulo: ID del módulo
        accion: Tipo de acción ('insertar', 'actualizar', 'seleccionar', 'borrar')
    
    Returns:
        bool: True si tiene permiso, False si no
    """
```

## Casos de Uso Avanzados

### Permisos condicionales

Si un permiso depende de la relación entre usuarios:

```python
# El usuario puede ver su propio perfil sin permiso especial
if user_id == user_token.id_usuario:
    return user
else:
    # Para ver otros usuarios necesita permiso
    if not verify_permissions(db, user_token.id_rol, modulo, 'seleccionar'):
        raise HTTPException(status_code=403, detail='No autorizado')
```

### Módulos dinámicos

Cambiar el módulo según contexto:

```python
id_rol = user_token.id_rol

# Módulo diferente según el rol del usuario a crear
if user.id_rol == 1:  # SuperAdmin
    modulo_requerido = 10  # Módulo especial
else:
    modulo_requerido = 1   # Módulo normal

if not verify_permissions(db, id_rol, modulo_requerido, 'insertar'):
    raise HTTPException(status_code=403, detail='No autorizado')
```
