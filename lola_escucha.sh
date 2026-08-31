#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════════════════
# LOLA LISTENER — Micrófono siempre activo
# ══════════════════════════════════════════════════════════════

AUDIO_DIR="$HOME/.lola/data/audio"
mkdir -p "$AUDIO_DIR"

echo "🎤 MICRÓFONO SIEMPRE ACTIVO — Di 'Lola' para activar"
echo "   Ctrl+C para parar"
echo ""

while true; do
    # Borrar archivo anterior
    rm -f "$AUDIO_DIR/chunk.wav" 2>/dev/null

    # Grabar 3 segundos
    termux-microphone-record -f "$AUDIO_DIR/chunk.wav" -l 3 -r 16000 -c 1 2>/dev/null
    sleep 3.5
    termux-microphone-record -q 2>/dev/null
    sleep 0.3

    # Verificar archivo
    if [ ! -s "$AUDIO_DIR/chunk.wav" ]; then
        continue
    fi

    # Procesar con Vosk
    RESULT=$(proot-distro login ubuntu -- python3 -c "
import json,sys,wave,os
try:
    from vosk import Model, KaldiRecognizer
    m=Model('/root/.lola/models/vosk-model-small-es-0.42')
    p='/data/data/com.termux/files/home/.lola/data/audio/chunk.wav'
    if not os.path.exists(p): sys.exit(0)
    w=wave.open(p,'rb')
    r=KaldiRecognizer(m,w.getframerate())
    while True:
        d=w.readframes(4000)
        if len(d)==0: break
        r.AcceptWaveform(d)
    t=json.loads(r.FinalResult()).get('text','')
    if t: print(t)
except: pass
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
except: print('No entendí, Ingeniero')
" 2>/dev/null)
                echo "🤖 Lola: $REPLY"
                termux-tts-speak "$REPLY" 2>/dev/null &
            fi
        fi
    fi
done
