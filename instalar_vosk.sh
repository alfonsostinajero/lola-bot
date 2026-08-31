#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════════════════
# INSTALAR VOSK — Micrófono siempre activo como Alexa
# Instala PRoot + Ubuntu + Vosk + PulseAudio
# Solo escribe: bash instalar_vosk.sh
# ══════════════════════════════════════════════════════════════

echo ""
echo "🎤 Instalando sistema de voz continua (Vosk)..."
echo "   Esto tarda ~10-15 minutos. No cierre Termux."
echo ""

# 1. Instalar PRoot y PulseAudio en Termux
echo "📦 Paso 1/5: Instalando proot-distro y pulseaudio..."
pkg install -y proot-distro pulseaudio termux-api
echo "✅ proot-distro y pulseaudio instalados"

# 2. Instalar Ubuntu
echo "📦 Paso 2/5: Instalando Ubuntu (puede tardar ~5 min)..."
proot-distro install ubuntu 2>/dev/null || echo "Ubuntu ya instalado"
echo "✅ Ubuntu listo"

# 3. Instalar Vosk y PyAudio dentro de Ubuntu
echo "📦 Paso 3/5: Instalando Vosk dentro de Ubuntu..."
proot-distro login ubuntu -- bash -c '
    apt update -y
    apt install -y python3 python3-pip portaudio19-dev wget unzip
    pip3 install vosk pyaudio
    echo "✅ Vosk instalado dentro de Ubuntu"
'

# 4. Descargar modelo de español dentro de Ubuntu
echo "📦 Paso 4/5: Descargando modelo de español..."
proot-distro login ubuntu -- bash -c '
    mkdir -p /root/.lola/models
    if [ ! -d "/root/.lola/models/vosk-model-small-es-0.42" ]; then
        cd /root/.lola/models
        wget -q --show-progress https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
        unzip -q vosk-model-small-es-0.42.zip
        rm vosk-model-small-es-0.42.zip
        echo "✅ Modelo español descargado"
    else
        echo "✅ Modelo español ya existe"
    fi
'

# 5. Crear el script de escucha continua
echo "📦 Paso 5/5: Creando listener continuo..."
proot-distro login ubuntu -- bash -c 'cat > /root/lola_listener.py << '"'"'PYEOF'"'"'
#!/usr/bin/env python3
"""
lola_listener.py — Escucha continua con Vosk.
Micrófono SIEMPRE ACTIVO. Cuando detecta "lola", envía señal.
"""
import pyaudio
import json
import sys
import os
from vosk import Model, KaldiRecognizer

MODEL_PATH = "/root/.lola/models/vosk-model-small-es-0.42"
WAKE_WORD = "lola"
SAMPLE_RATE = 16000

def main():
    print("🎤 Cargando modelo de voz...", flush=True)
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, SAMPLE_RATE)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=4096,
    )
    stream.start_stream()

    print("🎤 MICRÓFONO ACTIVO — Escuchando siempre...", flush=True)
    print(f"   Di \"{WAKE_WORD}\" para activar", flush=True)

    while True:
        try:
            data = stream.read(4096, exception_on_overflow=False)

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower().strip()
                if text:
                    # Enviar TODO lo que escucha a stdout
                    print(f"HEARD:{text}", flush=True)

                    if WAKE_WORD in text:
                        # Extraer comando después de "lola"
                        parts = text.split(WAKE_WORD, 1)
                        command = parts[1].strip() if len(parts) > 1 else ""
                        print(f"WAKE:{command}", flush=True)
            else:
                partial = json.loads(rec.PartialResult())
                partial_text = partial.get("partial", "").lower()
                if WAKE_WORD in partial_text:
                    print(f"PARTIAL_WAKE:", flush=True)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"ERROR:{e}", flush=True)

    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == "__main__":
    main()
PYEOF'
echo "✅ Listener creado"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  🎤 VOSK INSTALADO CORRECTAMENTE            ║"
echo "║  Micrófono siempre activo como Alexa         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Para probar: bash probar_vosk.sh"
echo ""
