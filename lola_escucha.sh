#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════════════════
# LOLA LISTENER — Micrófono siempre activo
# Graba con Termux → Convierte con ffmpeg → Procesa con Vosk
# ══════════════════════════════════════════════════════════════

# Instalar ffmpeg si no existe
which ffmpeg > /dev/null 2>&1 || pkg install -y ffmpeg

AD="$HOME/.lola/data/audio"
mkdir -p "$AD"

echo "🎤 MICRÓFONO SIEMPRE ACTIVO — Di 'Lola' para activar"
echo "   Ctrl+C para parar"
echo ""

while true; do
    # Borrar archivos anteriores
    rm -f "$AD/raw.m4a" "$AD/chunk.wav" 2>/dev/null

    # Grabar 3 seg en formato nativo
    termux-microphone-record -f "$AD/raw.m4a" -l 3 2>/dev/null
    sleep 3.2
    termux-microphone-record -q 2>/dev/null
    sleep 0.2

    # Verificar
    [ ! -s "$AD/raw.m4a" ] && continue

    # Convertir a WAV 16kHz mono con ffmpeg
    ffmpeg -y -i "$AD/raw.m4a" -ar 16000 -ac 1 -f wav "$AD/chunk.wav" 2>/dev/null

    [ ! -s "$AD/chunk.wav" ] && continue

    # Procesar con Vosk
    RESULT=$(proot-distro login ubuntu -- python3 -c "
import json,sys,wave,os
try:
    from vosk import Model,KaldiRecognizer
    m=Model('/root/.lola/models/vosk-model-small-es-0.42')
    p='/data/data/com.termux/files/home/.lola/data/audio/chunk.wav'
    if not os.path.exists(p):sys.exit(0)
    w=wave.open(p,'rb')
    r=KaldiRecognizer(m,w.getframerate())
    while True:
        d=w.readframes(4000)
        if len(d)==0:break
        r.AcceptWaveform(d)
    t=json.loads(r.FinalResult()).get('text','')
    if t:print(t)
except:pass
" 2>/dev/null)

    if [ -n "$RESULT" ]; then
        echo "🎧 Escuché: '$RESULT'"

        if echo "$RESULT" | grep -qi "lola"; then
            echo "🎯 ¡LOLA DETECTADA!"
            termux-vibrate -d 300 2>/dev/null
            termux-toast "🎤 Te escucho, Ingeniero..." 2>/dev/null

            COMMAND=$(echo "$RESULT" | sed 's/.*lola//I' | xargs)

            if [ -z "$COMMAND" ]; then
                echo "🎤 Escuchando comando..."
                COMMAND=$(termux-speech-to-text 2>/dev/null | head -1)
            fi

            if [ -n "$COMMAND" ]; then
                echo "📝 Comando: '$COMMAND'"
                REPLY=$(curl -s http://127.0.0.1:8080/v1/chat/completions \
                    -H "Content-Type: application/json" \
                    -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$COMMAND\"}]}" \
                    2>/dev/null | python3 -c "
import json,sys
try:
    r=json.load(sys.stdin)
    print(r['choices'][0]['message']['content'][:250])
except:print('No entendi, Ingeniero')
" 2>/dev/null)
                echo "🤖 Lola: $REPLY"
                termux-tts-speak "$REPLY" 2>/dev/null &
            fi
        fi
    fi
done
