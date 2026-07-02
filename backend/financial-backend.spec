# PyInstaller spec — genera dist/financial-backend/ (onedir: arranque rápido, sin
# extracción a temp en cada lanzamiento, requisito de <5s de la Fase 11).
# Build: uv run --group build pyinstaller financial-backend.spec --noconfirm
from PyInstaller.utils.hooks import collect_data_files

datas = [
    ("app/modules/market_intelligence/catalog/yaml", "app/modules/market_intelligence/catalog/yaml"),
    ("app/modules/financial_knowledge/rules", "app/modules/financial_knowledge/rules"),
]

a = Analysis(
    ["run_server.py"],
    pathex=["."],
    datas=datas,
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
    ],
    excludes=["pytest", "ruff"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="financial-backend",
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="financial-backend",
)
