#!/bin/bash
# ============================================================
#  deploy.sh  -  instalar Z1_Grid en Ableton Live 9
#  Detecta solo la version, la ruta de la app y la del Log.
#
#
#     ./deploy.sh            desplegar
#     ./deploy.sh backup     solo backup de los scripts de fabrica
#     ./deploy.sh log        seguir el Log.txt en vivo
#     ./deploy.sh info       mostrar lo detectado y salir
#
#  El backup va a $HOME/Z1_Grid_backups. Para cambiarlo:
#     Z1_BACKUP_DIR=/Volumes/MiDisco ./deploy.sh
#     ./deploy.sh --backup /Volumes/MiDisco
# ============================================================

set -e
NOMBRE="Z1_Grid"

# --backup RUTA (tiene que leerse antes de usar BACKUP_BASE)
ARGS=()
while [ $# -gt 0 ]; do
    case "$1" in
        --backup) shift; Z1_BACKUP_DIR="$1" ;;
        *) ARGS+=("$1") ;;
    esac
    shift
done
set -- "${ARGS[@]}"
# Donde guardar el backup de los scripts de fabrica.
# Por defecto en el home, que siempre existe. Se puede cambiar con la
# variable de entorno Z1_BACKUP_DIR o con --backup RUTA.
BACKUP_BASE="${Z1_BACKUP_DIR:-$HOME/Z1_Grid_backups}"

# ---------- detectar la app ----------
APP=""
for cand in /Applications/Ableton\ Live\ 9*.app; do
    if [ -d "$cand/Contents/App-Resources/MIDI Remote Scripts" ]; then
        APP="$cand"
    fi
done
if [ -z "$APP" ]; then
    echo "ERROR: no encuentro Ableton Live 9 en /Applications"
    echo "Estas corriendo esto desde Mavericks?"
    exit 1
fi
DEST="$APP/Contents/App-Resources/MIDI Remote Scripts"

# ---------- detectar el Log (la carpeta lleva la version) ----------
PREFS="$HOME/Library/Preferences/Ableton"
LOGDIR=""
for d in "$PREFS"/Live\ 9*; do
    if [ -f "$d/Log.txt" ]; then
        LOGDIR="$d"
    fi
done
LOG="$LOGDIR/Log.txt"
VER="$(basename "$LOGDIR" 2>/dev/null | tr ' ' '_')"
if [ -z "$VER" ]; then VER="desconocida"; fi
FUENTE="$(cd "$(dirname "$0")/.." && pwd)/$NOMBRE"
BACKUP="$BACKUP_BASE/backup_MIDI_Remote_Scripts_$VER"

if [ "$1" = "info" ]; then
    echo "app:     $APP"
    echo "destino: $DEST"
    echo "log:     $LOG"
    echo "backup:  $BACKUP"
    exit 0
fi

# ---------- seguir el log ----------
if [ "$1" = "log" ]; then
    if [ ! -f "$LOG" ]; then
        echo "No encuentro el Log. Abri Live una vez y volve a intentar."
        echo "Buscado en: $PREFS/Live 9*/Log.txt"
        exit 1
    fi
    echo "Siguiendo: $LOG    (Ctrl-C para salir)"
    tail -f "$LOG"
    exit 0
fi

if [ ! -d "$FUENTE" ]; then
    echo "ERROR: no encuentro la carpeta fuente $FUENTE"
    exit 1
fi

# ---------- backup por version ----------
# Cada instalacion de Live tiene su propio backup: un backup de 9.1
# no sirve para restaurar 9.7.
if [ ! -d "$BACKUP" ]; then
    echo "Creando backup de los scripts de fabrica ($VER)"
    echo "  -> $BACKUP"
    mkdir -p "$BACKUP_BASE" || {
        echo "ERROR: no pude crear $BACKUP_BASE"
        echo "Elegi otra ruta:  ./deploy.sh --backup /ruta/que/exista"
        exit 1
    }
    sudo cp -R "$DEST" "$BACKUP"
    echo "backup listo."
else
    echo "backup de $VER ya existe."
fi
[ "$1" = "backup" ] && exit 0

# ---------- no pisar scripts de fabrica ----------
if [ -d "$DEST/$NOMBRE" ]; then
    if [ ! -f "$DEST/$NOMBRE/.z1grid" ]; then
        echo "ERROR: existe $DEST/$NOMBRE y no lleva nuestra marca."
        echo "Revisalo a mano."
        exit 1
    fi
    sudo rm -rf "$DEST/$NOMBRE"
fi

sudo cp -R "$FUENTE" "$DEST/$NOMBRE"
sudo touch "$DEST/$NOMBRE/.z1grid"
# Live compila .py a .pyc al arrancar: un .pyc viejo hace depurar codigo muerto
sudo find "$DEST/$NOMBRE" -name "*.pyc" -delete
sudo chown -R root:wheel "$DEST/$NOMBRE"
sudo chmod -R 755 "$DEST/$NOMBRE"

echo ""
echo "Instalado en $DEST/$NOMBRE   (Live $VER)"
ls -la "$DEST/$NOMBRE"
echo ""
echo "1) Cerra Live.  2) En otra terminal: ./deploy.sh log  3) Abri Live."
echo "4) Preferences -> MIDI -> Control Surface -> $NOMBRE"
echo ""
echo "Si no aparece en el desplegable, el traceback esta en el Log."
