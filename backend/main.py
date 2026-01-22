
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.router import users, tipos_documentos, plantillas, control_consecutivos, documentos, tareas_pendientes, observaciones, firmas_digitales, roles, cargos
from app.api import auth

app = FastAPI()

# Incluir en el objeto app los routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(roles.router, prefix="/roles", tags=["roles"])
app.include_router(cargos.router, prefix="/cargos", tags=["cargos"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(tipos_documentos.router, prefix="/tipos-documentos", tags=["tipos-documentos"])
app.include_router(plantillas.router, prefix="/plantillas", tags=["plantillas"])
app.include_router(control_consecutivos.router, prefix="/control-consecutivos", tags=["control-consecutivos"])
app.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
app.include_router(tareas_pendientes.router, prefix="/tareas-pendientes", tags=["tareas-pendientes"])
app.include_router(observaciones.router, prefix="/observaciones", tags=["observaciones"])
app.include_router(firmas_digitales.router, prefix="/firmas-digitales", tags=["firmas-digitales"])

# Servir archivos estáticos (firmas, etc.)
static_dir = Path(__file__).parent / "media"
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Configuración de CORS para permitir todas las solicitudes desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir solicitudes desde cualquier origen
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Permitir estos métodos HTTP
    allow_headers=["*"],  # Permitir cualquier encabezado en las solicitudes
)

@app.get("/")
def read_root():
    return {
                "message": "Funcionando correctamente",
                "autor": "Santiago Arismendi"
            }