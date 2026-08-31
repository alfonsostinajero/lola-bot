#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════════════════
# LOLA LISTENER — Micrófono siempre activo (versión rápida)
# Graba → Detecta voz con ffmpeg → Si hay voz usa speech-to-text
# ══════════════════════════════════════════════════════════════

which ffmpeg > /dev/null 2>&1 || pkg install -y ffmpeg

AD="$HOME/.lola/data/audio"
mkdir -p "$AD"

echo "🎤 MICRÓFONO SIEMPRE ACTIVO — Di 'Lola' para activar"
echo "   Ctrl+C para parar"
echo ""

while true; do
    rm -f "$AD/raw.m4a" "$AD/chunk.wav" 2>/dev/null

    # Grabar 3 seg
    termux-microphone-record -f "$AD/raw.m4a" -l 3 2>/dev/null
    sleep 3.2
    termux-microphone-record -q 2>/dev/null

    [ ! -s "$AD/raw.m4a" ] && continue

    # Convertir a WAV
    ffmpeg -y -i "$AD/raw.m4a" -ar 16000 -ac 1 "$AD/chunk.wav" 2>/dev/null
    [ ! -s "$AD/chunk.wav" ] && continue

    # Detectar si hay voz (volumen > silencio)
    VOL=$(ffmpeg -i "$AD/chunk.wav" -af "volumedetect" -f null /dev/null 2>&1 | grep mean_volume | awk '{print $5}')

    # Si el volumen es muy bajo (silencio), saltar
    if [ -n "$VOL" ]; then
        VOL_INT=$(echo "$VOL" | cut -d. -f1 | tr -d '-')
        if [ "$VOL_INT" -gt 35 ] 2>/dev/null; then
            continue
        fi
    fi

    # Hay voz! Usar speech-to-text de Google (rápido y preciso)
    echo "🎤 Voz detectada, reconociendo..."
    RESULT=$(termux-speech-to-text 2>/dev/null | head -1)

    if [ -n "$RESULT" ]; then
        echo "🎧 Escuché: '$RESULT'"

        if echo "$RESULT" | grep -qi "lola"; then
            echo "🎯 ¡LOLA DETECTADA!"
            termux-vibrate -d 300 2>/dev/null
            termux-toast "🎤 Te escucho, Ingeniero..." 2>/dev/null

            # Sacar comando quitando "lola"
            COMMAND=$(echo "$RESULT" | sed 's/[Ll][Oo][Ll][Aa]//g' | xargs)

            if [ -z "$COMMAND" ]; then
                echo "🎤 ¿Qué necesita, Ingeniero?"
                termux-tts-speak "¿Qué necesita, Ingeniero?" 2>/dev/null &
                COMMAND=$(termux-speech-to-text 2>/dev/null | head -1)
            fi

            if [ -n "$COMMAND" ]; then
                echo "📝 Comando: '$COMMAND'"

                # Enviar a Gemma 4
                REPLY=$(curl -s http://127.0.0.1:8080/v1/chat/completions \
                    -H "Content-Type: application/json" \
                    -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$COMMAND\"}]}" \
                    2>/dev/null | python3 -c "
import json,sys
try:
    r=json.load(sys.stdin)
    c=r['choices'][0]['message']['content']
    # Intentar extraer respuesta_usuario del JSON
    try:
        j=json.loads(c)
        print(j.get('respuesta_usuario',c)[:250])
    except:
        print(c[:250])
except:print('Disculpe Ingeniero, no entendi')
" 2>/dev/null)

                echo "🤖 Lola: $REPLY"
                termux-tts-speak "$REPLY" 2>/dev/null &
            fi
        fi
    fi
done
