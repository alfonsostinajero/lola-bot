#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════
# INICIAR LOLA AI — Script todo-en-uno
# Solo escribe: bash iniciar.sh
# ══════════════════════════════════════════════

echo ""
echo "🤖 Iniciando Lola AI..."
echo ""

# 1. Crear auto-inicio
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/start-lola.sh << 'BOOT'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
sleep 10
cd ~/llama.cpp
./build/bin/llama-server -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -c 2048 -t 4 > ~/.lola/logs/llama-server.log 2>&1 &
for i in $(seq 1 60); do curl -s http://127.0.0.1:8080/health > /dev/null 2>&1 && break; sleep 2; done
cd ~/lola-bot && python lola_core.py --mode full >> ~/.lola/logs/lola.log 2>&1 &
termux-notification --title "Lola AI Activa" --content "Di Lola para activar." --ongoing --id lola_active
BOOT
chmod +x ~/.termux/boot/start-lola.sh
echo "✅ Auto-inicio configurado"

# 2. Crear directorios necesarios
mkdir -p ~/.lola/models ~/.lola/data ~/.lola/logs ~/.lola/backups ~/.lola/piper
echo "✅ Directorios listos"

# 3. Matar servidores anteriores si existen
pkill -f llama-server 2>/dev/null
sleep 2
echo "✅ Limpieza hecha"

# 4. Arrancar servidor de IA
echo "⏳ Arrancando Gemma 4 (espere ~30 segundos)..."
cd ~/llama.cpp
./build/bin/llama-server \
    -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf \
    --host 127.0.0.1 \
    --port 8080 \
    -c 2048 \
    -t 4 \
    > ~/.lola/logs/llama-server.log 2>&1 &

# 5. Esperar a que cargue
for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:8080/health > /dev/null 2>&1; then
        echo "✅ Gemma 4 lista"
        break
    fi
    echo "  ⏳ Cargando modelo... ($i/60)"
    sleep 2
done

# 6. Wake lock
termux-wake-lock 2>/dev/null

# 7. Arrancar Lola
echo ""
echo "╔══════════════════════════════════════╗"
echo "║    🤖 LOLA AI ACTIVA               ║"
echo "║    Di 'Lola' para hablar con ella   ║"
echo "╚══════════════════════════════════════╝"
echo ""

cd ~/lola-bot
python lola_core.py --mode full
