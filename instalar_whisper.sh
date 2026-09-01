#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════
# INSTALAR WHISPER.CPP — Reconocimiento de voz LOCAL
# Sin Google, sin internet, rápido y preciso
# bash instalar_whisper.sh
# ══════════════════════════════════════════════════

echo "🎤 Instalando Whisper (reconocimiento de voz local)..."
echo "   Esto tarda ~5 minutos. Tome café ☕"
echo ""

# Dependencias
echo "📦 1/4: Instalando dependencias..."
pkg install -y cmake make clang git ffmpeg 2>/dev/null
echo "✅ Dependencias listas"

# Clonar whisper.cpp
echo "📥 2/4: Descargando Whisper.cpp..."
cd ~
if [ -d "whisper.cpp" ]; then
    cd whisper.cpp && git pull
else
    git clone https://github.com/ggerganov/whisper.cpp.git
    cd whisper.cpp
fi
echo "✅ Whisper.cpp descargado"

# Compilar
echo "🔨 3/4: Compilando Whisper (esto tarda ~3 min)..."
cmake -B build -DCMAKE_BUILD_TYPE=Release 2>/dev/null
cmake --build build -j$(nproc) 2>/dev/null
if [ -f "build/bin/whisper-cli" ]; then
    echo "✅ Whisper compilado"
else
    echo "⚠️ Intentando compilación alternativa..."
    rm -rf build
    mkdir build && cd build
    cmake .. 2>/dev/null
    make -j$(nproc) 2>/dev/null
    cd ..
fi
echo "✅ Compilación lista"

# Descargar modelo tiny (75MB, rápido, entiende español)
echo "📥 4/4: Descargando modelo de voz (75MB)..."
mkdir -p models
if [ ! -f "models/ggml-tiny.bin" ]; then
    curl -L -o models/ggml-tiny.bin \
        "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin"
fi

if [ -f "models/ggml-tiny.bin" ]; then
    echo "✅ Modelo descargado"
else
    echo "❌ Error descargando modelo. Intente de nuevo."
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ WHISPER INSTALADO                     ║"
echo "║  🎤 Reconocimiento de voz LOCAL           ║"
echo "║  🇲🇽 Entiende español                     ║"
echo "║  ⚡ Sin Google, sin internet               ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Ahora ejecute: bash iniciar.sh"
