
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.router import users, tipos_documentos, plantillas, control_consecutivos
from app.api import auth

app = FastAPI()

# Incluir en el objeto app los routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(tipos_documentos.router, prefix="/tipos-documentos", tags=["tipos-documentos"])
app.include_router(plantillas.router, prefix="/plantillas", tags=["plantillas"])
app.include_router(control_consecutivos.router, prefix="/control-consecutivos", tags=["control-consecutivos"])

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