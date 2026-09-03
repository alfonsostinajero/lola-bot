#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════
# INICIAR LOLA — bash iniciar.sh
# ══════════════════════════════════════════
echo "🤖 Iniciando Lola AI..."

mkdir -p ~/.termux/boot ~/.lola/models ~/.lola/logs

# Auto-inicio
cat > ~/.termux/boot/start-lola.sh << 'BOOT'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
sleep 10
cd ~/llama.cpp && ./build/bin/llama-server -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf --host 127.0.0.1 --port 8080 -c 2048 -t 4 > ~/.lola/logs/llama.log 2>&1 &
for i in $(seq 1 60); do curl -s http://127.0.0.1:8080/health > /dev/null 2>&1 && break; sleep 2; done
cd ~/lola-bot && python lola_escucha.py >> ~/.lola/logs/lola.log 2>&1 &
BOOT
chmod +x ~/.termux/boot/start-lola.sh

# Matar procesos anteriores
pkill -f llama-server 2>/dev/null
pkill -f lola_escucha 2>/dev/null
sleep 2

# ── ARRANCAR GEMMA 4 (config segura que NO falla) ──
echo "⚡ Arrancando Gemma 4..."
cd ~/llama.cpp
./build/bin/llama-server \
    -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf \
    --host 127.0.0.1 \
    --port 8080 \
    -c 2048 \
    -t 4 \
    > ~/.lola/logs/llama.log 2>&1 &

# Esperar
for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:8080/health 2>/dev/null | grep -q "ok"; then
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
