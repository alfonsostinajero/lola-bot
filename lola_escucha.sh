#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════════════════
# LOLA — Asistente de voz. Micrófono siempre activo.
# SIMPLE: termux-speech-to-text en loop continuo.
# ══════════════════════════════════════════════════════════════

echo ""
echo "╔══════════════════════════════════════╗"
echo "║  🤖 LOLA AI ACTIVA                  ║"
echo "║  🎤 Diga 'Lola' seguido de comando  ║"
echo "║  Ejemplo: 'Lola buenos días'        ║"
echo "║  Ctrl+C para parar                  ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Notificación
termux-notification --title "Lola AI Activa" \
    --content "Diga 'Lola' para hablar" \
    --ongoing --id lola_active 2>/dev/null

while true; do
    # Escuchar con Google Speech (se activa solo, sin diálogos)
    TEXT=$(termux-speech-to-text 2>/dev/null)

    # Si no escuchó nada, reintentar
    [ -z "$TEXT" ] && continue

    # Convertir a minúsculas
    TEXT_LOWER=$(echo "$TEXT" | tr '[:upper:]' '[:lower:]')

    echo "🎧 Escuché: '$TEXT'"

    # Buscar "lola" en lo que dijo
    if echo "$TEXT_LOWER" | grep -q "lola"; then
        echo "🎯 ¡LOLA ACTIVADA!"
        termux-vibrate -d 300 2>/dev/null

        # Quitar "lola" del texto para obtener el comando
        COMMAND=$(echo "$TEXT" | sed -E 's/[Ll][Oo][Ll][Aa][ ,]?//g' | xargs)

        # Si solo dijo "lola" sin comando, preguntar
        if [ -z "$COMMAND" ] || [ ${#COMMAND} -lt 3 ]; then
            termux-tts-speak "Dígame, Ingeniero" 2>/dev/null
            echo "🎤 Escuchando comando..."
            COMMAND=$(termux-speech-to-text 2>/dev/null)
        fi

        if [ -n "$COMMAND" ] && [ ${#COMMAND} -gt 2 ]; then
            echo "📝 Comando: '$COMMAND'"

            # Enviar a Gemma 4
            echo "🧠 Procesando..."
            REPLY=$(curl -s -m 30 http://127.0.0.1:8080/v1/chat/completions \
                -H "Content-Type: application/json" \
                -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$COMMAND\"}]}" \
                2>/dev/null | python3 -c "
import json,sys
try:
    r=json.load(sys.stdin)
    c=r['choices'][0]['message']['content']
    try:
        j=json.loads(c)
        print(j.get('respuesta_usuario',c)[:300])
    except:
        print(c[:300])
except:
    print('Disculpe Ingeniero, hubo un error')
" 2>/dev/null)

            echo "🤖 Lola: $REPLY"
            echo ""

            # Hablar la respuesta
            termux-tts-speak "$REPLY" 2>/dev/null &
        fi
    fi
done
