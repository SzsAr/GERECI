# Manejo de tokens expirados - Redirección a login

## 🔧 Implementación

**Archivo:** [frontend/js/api.js](frontend/js/api.js)

### Cambio realizado

Se agregó validación de **HTTP 401 (Unauthorized)** para redirigir automáticamente al login cuando:

1. **Token expirado**
2. **Token inválido**
3. **Token no válido para el recurso**

### Código implementado

```javascript
// Si token expirado o inválido (401)
if (res.status === 401) {
  localStorage.removeItem('token');
  window.location.href = './index.html';
  return;
}
```

## 🎯 Comportamiento

### Antes
```
Usuario hace request → Token expirado → 
API retorna 401 → Frontend muestra error: "Token inválido" ❌
```

### Después
```
Usuario hace request → Token expirado → 
API retorna 401 → Frontend limpia token → Redirecciona al login ✅
```

## ✨ Ventajas

✅ **Experiencia transparente** - Usuario no ve "Token inválido"  
✅ **Automático** - Redirección inmediata sin intervención  
✅ **Seguro** - Se limpia localStorage antes de redirigir  
✅ **Consistente** - Mismo comportamiento para todos los errores 401  

## 🔐 Flow de seguridad

1. Usuario hace login → Recibe token válido
2. Token se guarda en `localStorage`
3. Usuario navega y hace requests
4. **Token expira en el servidor**
5. Next request recibe **HTTP 401**
6. Frontend detecta → Limpia localStorage
7. Redirecciona a `./index.html` (login)
8. Usuario debe hacer login nuevamente

## 📝 Situaciones cubiertas

| Situación | Respuesta | Acción |
|-----------|----------|--------|
| Token válido | 2xx | Continuar normalmente |
| Token expirado | 401 | Redirigir a login |
| Token inválido | 401 | Redirigir a login |
| Credenciales inválidas | 401 | Mostrar error (en auth.js) |
| Usuario inactivo | 403 | Redirigir a login |
| Sin permisos | 403 | Mostrar error |
| Otros errores | 4xx/5xx | Mostrar error específico |

## 🧪 Testing

### Escenario 1: Token expirado
1. Login correctamente
2. Esperar a que token expire (o simular en BD)
3. Hacer cualquier acción (buscar documentos, cambiar estado, etc.)
4. ✅ Debería redirigir a login automáticamente

### Escenario 2: Token manipulado
1. Login correctamente
2. Abrir DevTools → Storage → localStorage
3. Cambiar token a valor inválido
4. Actualizar página o hacer acción
5. ✅ Debería redirigir a login

### Escenario 3: Token eliminado en servidor
1. Login correctamente
2. Eliminar token de BD (simular admin)
3. Hacer acción
4. ✅ Debería redirigir a login

## 🔗 Ubicación técnica

```
Frontend API Call → api.request()
                    ├─ Fetch con Authorization header
                    └─ Si res.status === 401
                       ├─ localStorage.removeItem('token')
                       ├─ window.location.href = './index.html'
                       └─ return (detiene ejecución)
```

## 📌 Notas importantes

- La redirección ocurre en **api.js** (capa de transporte)
- Todos los requests pasan por aquí
- No requiere cambios en componentes individuales
- Compatible con todos los endpoints
- Mensaje 401 puede venir de:
  - FastAPI security scheme (expired_token)
  - FastAPI dependencies (JWT validation)
  - Cualquier endpoint que requiera autenticación

