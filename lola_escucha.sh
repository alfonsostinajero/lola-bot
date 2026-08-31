#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════════════════
# LOLA LISTENER — Micrófono siempre activo
# Termux graba el audio → Vosk en Ubuntu lo procesa
# ══════════════════════════════════════════════════════════════

AUDIO_DIR="$HOME/.lola/data/audio"
mkdir -p "$AUDIO_DIR"

echo "🎤 MICRÓFONO SIEMPRE ACTIVO — Di 'Lola' para activar"
echo "   Ctrl+C para parar"
echo ""

while true; do
    # 1. Grabar 3 segundos con el micrófono REAL del teléfono
    AUDIO_FILE="$AUDIO_DIR/chunk.wav"
    termux-microphone-record -f "$AUDIO_FILE" -l 3 -r 16000 -c 1 2>/dev/null
    sleep 3.5
    termux-microphone-record -q 2>/dev/null
    sleep 0.2

    # 2. Verificar que el archivo existe y tiene contenido
    if [ ! -s "$AUDIO_FILE" ]; then
        continue
    fi

    # 3. Copiar audio a donde Ubuntu puede leerlo
    cp "$AUDIO_FILE" "$HOME/.lola/data/audio/process.wav" 2>/dev/null

    # 4. Procesar con Vosk dentro de Ubuntu
    RESULT=$(proot-distro login ubuntu -- python3 -c "
import json, sys, wave, os
try:
    from vosk import Model, KaldiRecognizer
    model = Model('/root/.lola/models/vosk-model-small-es-0.42')
    
    # El archivo está accesible via proot en la misma ruta
    audio_path = '/data/data/com.termux/files/home/.lola/data/audio/process.wav'
    if not os.path.exists(audio_path):
        sys.exit(0)
    
    wf = wave.open(audio_path, 'rb')
    rec = KaldiRecognizer(model, wf.getframerate())
    
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        rec.AcceptWaveform(data)
    
    result = json.loads(rec.FinalResult())
    text = result.get('text', '')
    if text:
        print(text)
except Exception as e:
    pass
" 2>/dev/null)

    # 5. Verificar si dijo "lola"
    if [ -n "$RESULT" ]; then
        echo "🎧 Escuché: '$RESULT'"
        
        if echo "$RESULT" | grep -qi "lola"; then
            echo "🎯 ¡LOLA DETECTADA!"
            
            # Vibrar
            termux-vibrate -d 300 2>/dev/null
            termux-toast "🎤 Te escucho, Ingeniero..." 2>/dev/null
            
            # Extraer comando si viene junto con "lola"
            COMMAND=$(echo "$RESULT" | sed 's/.*lola//I' | xargs)
            
            if [ -z "$COMMAND" ]; then
                # Si solo dijo "lola", escuchar el comando
                echo "🎤 Escuchando comando..."
                termux-speech-to-text > /tmp/lola_cmd.txt 2>/dev/null &
                STT_PID=$!
                sleep 8
                kill $STT_PID 2>/dev/null
                COMMAND=$(cat /tmp/lola_cmd.txt 2>/dev/null | xargs)
            fi
            
            if [ -n "$COMMAND" ]; then
                echo "📝 Comando: '$COMMAND'"
                # Enviar comando a Lola via API
                RESPONSE=$(curl -s http://127.0.0.1:8080/v1/chat/completions \
                    -H "Content-Type: application/json" \
                    -d "{\"messages\":[{\"role\":\"user\",\"content\":\"$COMMAND\"}]}" \
                    2>/dev/null)
                
                # Extraer respuesta y hablar
                REPLY=$(echo "$RESPONSE" | python3 -c "
import json,sys
try:
    r=json.load(sys.stdin)
    print(r['choices'][0]['message']['content'][:250])
except:
    print('No entendí, Ingeniero')
" 2>/dev/null)
                
                echo "🤖 Lola: $REPLY"
                termux-tts-speak "$REPLY" &
            fi
        fi
    fi
done
