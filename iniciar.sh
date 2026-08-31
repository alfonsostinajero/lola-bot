#!/data/data/com.termux/files/usr/bin/bash
# INICIAR LOLA AI — bash iniciar.sh
echo "🤖 Iniciando Lola AI..."

mkdir -p ~/.termux/boot ~/.lola/models ~/.lola/data/audio ~/.lola/logs

# Auto-inicio
cat > ~/.termux/boot/start-lola.sh << 'BOOT'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
sleep 10
cd ~/llama.cpp && ./build/bin/llama-server -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -c 2048 -t 4 > ~/.lola/logs/llama-server.log 2>&1 &
for i in $(seq 1 60); do curl -s http://127.0.0.1:8080/health > /dev/null 2>&1 && break; sleep 2; done
cd ~/lola-bot && python lola_escucha.py >> ~/.lola/logs/lola.log 2>&1 &
termux-notification --title "Lola AI Activa" --content "Diga Lola" --ongoing --id lola_active
BOOT
chmod +x ~/.termux/boot/start-lola.sh
echo "✅ Auto-inicio configurado"

# Limpiar
pkill -f llama-server 2>/dev/null
pkill -f lola_escucha 2>/dev/null
pkill -f termux-microphone-record 2>/dev/null
sleep 2

# Arrancar Gemma 4
echo "⏳ Arrancando Gemma 4..."
cd ~/llama.cpp
./build/bin/llama-server -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -c 2048 -t 4 > ~/.lola/logs/llama-server.log 2>&1 &

for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:8080/health > /dev/null 2>&1; then
        echo "✅ Gemma 4 lista"
        break
    fi
    echo "  ⏳ Cargando ($i/60)..."
    sleep 2
done

termux-wake-lock 2>/dev/null

# Arrancar Lola
cd ~/lola-bot
python lola_escucha.py
