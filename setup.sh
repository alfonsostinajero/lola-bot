#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════════════════
# setup.sh — Instalador completo de Lola AI para Termux
# Motorola Edge 20 (Snapdragon 778G) — TODO GRATUITO
# ══════════════════════════════════════════════════════════════

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_step() { echo -e "${CYAN}[$1/$TOTAL_STEPS]${NC} $2"; }
print_ok()   { echo -e "  ${GREEN}✓${NC} $1"; }
print_warn() { echo -e "  ${YELLOW}⚠${NC} $1"; }
print_err()  { echo -e "  ${RED}✗${NC} $1"; }

TOTAL_STEPS=10

echo -e "${BLUE}"
cat << 'BANNER'
╔══════════════════════════════════════════════╗
║                                              ║
║     ██╗      ██████╗ ██╗      █████╗         ║
║     ██║     ██╔═══██╗██║     ██╔══██╗        ║
║     ██║     ██║   ██║██║     ███████║        ║
║     ██║     ██║   ██║██║     ██╔══██║        ║
║     ███████╗╚██████╔╝███████╗██║  ██║        ║
║     ╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝        ║
║                                              ║
║        INSTALADOR DE LOLA AI v1.0.0          ║
║        Motorola Edge 20 · Termux             ║
║                                              ║
╚══════════════════════════════════════════════╝
BANNER
echo -e "${NC}"

echo -e "${YELLOW}Este script instalará todo lo necesario para Lola AI."
echo -e "Tiempo estimado: 30-60 minutos (dependiendo del WiFi).${NC}"
echo ""
read -p "¿Continuar con la instalación? [S/n] " confirm
[[ "$confirm" == "n" || "$confirm" == "N" ]] && exit 0
echo ""

# ── PASO 1: Actualizar sistema ───────────────────────────────
print_step 1 "Actualizando paquetes de Termux..."
pkg update -y && pkg upgrade -y
print_ok "Paquetes actualizados"

# ── PASO 2: Instalar paquetes base ───────────────────────────
print_step 2 "Instalando paquetes del sistema..."
pkg install -y \
    python python-pip \
    git cmake make clang \
    pkg-config libffi openssl openssl-tool \
    rust binutils \
    sox wget curl jq
print_ok "Paquetes base instalados"

# ── PASO 3: Instalar audio y Termux:API ─────────────────────
print_step 3 "Instalando paquetes de audio..."
pkg install -y pulseaudio portaudio termux-api
print_ok "Audio y Termux:API instalados"
echo ""
print_warn "IMPORTANTE: Asegúrate de tener instalada la app Termux:API desde F-Droid"
echo ""

# ── PASO 4: Configurar almacenamiento ───────────────────────
print_step 4 "Configurando acceso al almacenamiento..."
if [ ! -d "$HOME/storage" ]; then
    termux-setup-storage
    print_ok "Almacenamiento configurado"
else
    print_ok "Almacenamiento ya estaba configurado"
fi

# ── PASO 5: Instalar dependencias Python ─────────────────────
print_step 5 "Instalando dependencias Python (pip)..."

# IMPORTANTE: Instalar cryptography desde Termux (precompilado)
# pip NO puede compilar cryptography en Android porque Rust no soporta
# el target aarch64-unknown-linux-android
echo "  Instalando cryptography y dependencias nativas desde Termux..."
pkg install -y python-cryptography rust binutils 2>/dev/null || true

# Actualizar pip/setuptools
pip install --upgrade pip setuptools wheel

# Instalar cffi desde Termux si está disponible
pkg install -y python-cffi 2>/dev/null || true

# Instalar dependencias Python (cryptography ya está instalada vía pkg)
pip install \
    requests \
    python-dateutil \
    cachetools \
    pyasn1-modules \
    rsa \
    google-auth \
    google-auth-oauthlib \
    google-api-python-client

# Si google-auth falla por cryptography, intentar sin dependencias binarias
if [ $? -ne 0 ]; then
    print_warn "Reintentando instalación sin compilar cryptography..."
    # Forzar que pip use la cryptography ya instalada por pkg
    CRYPTOGRAPHY_DONT_BUILD_RUST=1 pip install \
        --no-build-isolation \
        google-auth \
        google-auth-oauthlib \
        google-api-python-client
fi

print_ok "Dependencias Python instaladas"
print_ok "STT/TTS: Usamos termux-speech-to-text y termux-tts-speak (ya incluidos en Termux:API)"

# ── PASO 6: Crear estructura de directorios ──────────────────
print_step 6 "Creando estructura de directorios..."
mkdir -p ~/.lola/{backups,logs,data,models,piper}
print_ok "Directorios creados en ~/.lola/"

# ── PASO 7: Reconocimiento de voz ─────────────────────────────
print_step 7 "Configurando reconocimiento de voz..."
print_ok "Usando termux-speech-to-text (reconocimiento nativo de Android)"
print_ok "No se necesita descargar modelos de voz — Android ya lo tiene"

# ── PASO 8: Instalar Piper TTS (voz natural GRATIS) ─────────
print_step 8 "Instalando Piper TTS (voz natural, gratuita)..."
PIPER_DIR="$HOME/.lola/piper"
if [ ! -f "$PIPER_DIR/piper" ]; then
    cd ~/.lola/piper

    # Detectar arquitectura ARM
    ARCH=$(uname -m)
    echo "  Arquitectura detectada: $ARCH"

    # Descargar Piper para ARM (aarch64)
    PIPER_VERSION="2023.11.14-2"
    PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_aarch64.tar.gz"

    wget -q --show-progress "$PIPER_URL" -O piper.tar.gz
    tar xzf piper.tar.gz
    rm piper.tar.gz

    # Mover binario si está en subdirectorio
    # Renombrar carpeta primero para evitar conflicto de nombres
    if [ -d "piper" ] && [ -f "piper/piper" ]; then
        mv piper piper_tmp
        mv piper_tmp/piper .
        cp -f piper_tmp/*.so* . 2>/dev/null || true
        cp -rf piper_tmp/espeak-ng-data . 2>/dev/null || true
        rm -rf piper_tmp
    fi

    chmod +x piper || true
    cd ~
    print_ok "Piper TTS instalado"
else
    print_ok "Piper TTS ya existe"
fi

# Descargar voz en español (México) — GRATUITA
VOICE_DIR="$HOME/.lola/models"
if [ ! -f "$VOICE_DIR/es_MX-claude-high.onnx" ]; then
    echo "  Descargando voz natural en español (México)..."
    cd $VOICE_DIR
    wget -q --show-progress \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx"
    wget -q --show-progress \
        "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/high/es_MX-claude-high.onnx.json"
    cd ~
    print_ok "Voz natural en español descargada"
else
    print_ok "Voz natural ya existe"
fi

# ── PASO 9: Compilar llama.cpp y descargar Gemma 4 ──────────
print_step 9 "Compilando llama.cpp y descargando modelo IA..."

# Compilar llama.cpp
if [ ! -f "$HOME/llama.cpp/build/bin/llama-server" ]; then
    cd ~
    if [ ! -d "llama.cpp" ]; then
        echo "  Clonando llama.cpp..."
        git clone --depth 1 https://github.com/ggerganov/llama.cpp.git
    fi
    cd llama.cpp
    echo "  Compilando (optimizado para ARM Snapdragon 778G)..."
    cmake -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DGGML_CPU_ARM_ARCH="armv8.2-a+dotprod+fp16"
    cmake --build build --config Release -j4
    cd ~
    print_ok "llama.cpp compilado"
else
    print_ok "llama.cpp ya compilado"
fi

# Descargar modelo Gemma 4
MODEL_PATH="$HOME/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf"
if [ ! -f "$MODEL_PATH" ]; then
    echo ""
    echo -e "  ${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "  ${YELLOW}  DESCARGA DEL MODELO GEMMA 4 (E2B)${NC}"
    echo -e "  ${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "  ${YELLOW}  El modelo pesa ~1.5 GB. Opciones:${NC}"
    echo ""
    echo -e "  ${CYAN}  Opción 1: Desde la PC y copiar al teléfono${NC}"
    echo -e "    Descarga desde: https://huggingface.co/google/gemma-4-e2b-it-GGUF"
    echo -e "    Busca el archivo: gemma-4-e2b-it-Q4_K_M.gguf"
    echo -e "    Cópialo a: ~/.lola/models/"
    echo ""
    echo -e "  ${CYAN}  Opción 2: Directo en Termux${NC}"
    echo -e "    pip install huggingface-hub"
    echo -e "    huggingface-cli download google/gemma-4-e2b-it-GGUF \\"
    echo -e "      gemma-4-e2b-it-Q4_K_M.gguf --local-dir ~/.lola/models/"
    echo ""
    echo -e "  ${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo ""

    read -p "  ¿Intentar descarga directa con huggingface-cli? [s/N] " download_choice
    if [[ "$download_choice" == "s" || "$download_choice" == "S" ]]; then
        pip install huggingface-hub
        echo "  Descargando modelo (esto puede tardar 30-60 min)..."
        huggingface-cli download google/gemma-4-e2b-it-GGUF \
            gemma-4-e2b-it-Q4_K_M.gguf \
            --local-dir ~/.lola/models/ || {
            print_warn "Descarga falló. Descárgalo manualmente."
        }
    else
        print_warn "Modelo no descargado. Descárgalo manualmente antes de usar Lola."
    fi
else
    print_ok "Modelo Gemma 4 ya existe"
fi

# ── PASO 10: Configurar auto-inicio ─────────────────────────
print_step 10 "Configurando inicio automático..."

# Copiar proyecto a home de Termux
if [ ! -d "$HOME/lola-bot" ]; then
    if [ -d "/sdcard/lola-bot" ]; then
        cp -r /sdcard/lola-bot $HOME/lola-bot
        print_ok "Proyecto copiado a ~/lola-bot"
    else
        print_warn "Copia el proyecto manualmente a ~/lola-bot"
    fi
fi

# Crear script de auto-inicio
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-lola.sh << 'BOOT_SCRIPT'
#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════
# Auto-inicio de Lola AI al encender Android
# ══════════════════════════════════════════
termux-wake-lock

# Esperar a que la red esté disponible
sleep 10

# Iniciar servidor llama.cpp en segundo plano
cd ~/llama.cpp
./build/bin/llama-server \
    -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf \
    --host 127.0.0.1 \
    --port 8080 \
    -c 2048 \
    -t 4 \
    --mlock \
    > ~/.lola/logs/llama-server.log 2>&1 &

LLAMA_PID=$!
echo "llama.cpp iniciado (PID: $LLAMA_PID)"

# Esperar a que el modelo cargue
echo "Esperando a que el modelo cargue..."
for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:8080/health > /dev/null 2>&1; then
        echo "Modelo listo."
        break
    fi
    sleep 2
done

# Iniciar Lola
cd ~/lola-bot
python lola_core.py --mode full >> ~/.lola/logs/lola.log 2>&1 &

LOLA_PID=$!
echo "Lola iniciada (PID: $LOLA_PID)"

# Notificar al usuario
termux-notification \
    --title "Lola AI Activa" \
    --content "Asistente de voz listo. Di 'Lola' para activar." \
    --ongoing \
    --id lola_active

BOOT_SCRIPT
chmod +x ~/.termux/boot/start-lola.sh
print_ok "Auto-inicio configurado (se activa al reiniciar el teléfono)"

# Instalar termux-services si no existe
pkg install -y termux-services 2>/dev/null && print_ok "termux-services instalado" || true

# Wake Lock permanente
termux-wake-lock
print_ok "Wake lock activado"

# ── Resumen Final ────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ INSTALACIÓN COMPLETADA EXITOSAMENTE     ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}📁 Estructura creada:${NC}"
echo "   ~/.lola/"
echo "   ├── models/     → Modelos de IA y voz"
echo "   ├── data/       → Base de datos y contactos"
echo "   ├── logs/       → Registros del sistema"
echo "   ├── backups/    → Backups de auto-modificación"
echo "   └── piper/      → Motor de voz natural"
echo ""
echo -e "${CYAN}🚀 Para iniciar Lola:${NC}"
echo ""
echo -e "   ${GREEN}# 1. Iniciar el servidor de IA:${NC}"
echo "   cd ~/llama.cpp"
echo "   ./build/bin/llama-server \\"
echo "       -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf \\"
echo "       --host 127.0.0.1 --port 8080 -c 2048 -t 4 &"
echo ""
echo -e "   ${GREEN}# 2. Iniciar Lola:${NC}"
echo "   cd ~/lola-bot"
echo "   python lola_core.py               # Modo completo"
echo "   python lola_core.py --mode text-only  # Modo texto (testing)"
echo ""
echo -e "   ${GREEN}# O simplemente reinicia el teléfono para auto-inicio${NC}"
echo ""
echo -e "${YELLOW}⚠️  Pendiente:${NC}"
echo "   - Descarga el modelo Gemma 4 si no lo hiciste arriba"
echo "   - Configura Google Calendar (credentials.json)"
echo "   - Agrega tus contactos de WhatsApp en ~/.lola/data/contacts.json"
echo ""
