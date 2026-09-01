#!/data/data/com.termux/files/usr/bin/bash
# ══════════════════════════════════════════════════════════════
# INICIAR LOLA AI — Optimizado para Snapdragon 778G (8 núcleos)
# bash iniciar.sh
# ══════════════════════════════════════════════════════════════

echo "🤖 Iniciando Lola AI (Snapdragon 778G Max Power)..."

mkdir -p ~/.termux/boot ~/.lola/models ~/.lola/data/audio ~/.lola/logs

# Auto-inicio al reiniciar
cat > ~/.termux/boot/start-lola.sh << 'BOOT'
#!/data/data/com.termux/files/usr/bin/bash
termux-wake-lock
sleep 10
cd ~/llama.cpp && ./build/bin/llama-server \
    -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf \
    --host 127.0.0.1 --port 8080 \
    -c 2048 -t 6 -tb 8 -b 512 --mlock \
    -fa --no-mmap \
    > ~/.lola/logs/llama-server.log 2>&1 &
for i in $(seq 1 60); do curl -s http://127.0.0.1:8080/health > /dev/null 2>&1 && break; sleep 2; done
cd ~/lola-bot && python lola_escucha.py >> ~/.lola/logs/lola.log 2>&1 &
termux-notification --title "Lola AI Activa" --content "Solo hable" --ongoing --id lola_active
BOOT
chmod +x ~/.termux/boot/start-lola.sh
echo "✅ Auto-inicio configurado"

# Limpiar procesos anteriores
pkill -f llama-server 2>/dev/null
pkill -f lola_escucha 2>/dev/null
pkill -f termux-microphone 2>/dev/null
sleep 2

# ══════════════════════════════════════════════════════════════
# ARRANCAR GEMMA 4 — MÁXIMA VELOCIDAD
# Snapdragon 778G: 1x A78@2.4GHz + 3x A78@2.2GHz + 4x A55@1.8GHz
#
# -t 6     → 6 hilos para generación (usa los 4 A78 + 2 A55)
# -tb 8    → 8 hilos para batch (usa TODOS los núcleos)
# -b 512   → Batch size grande = más tokens por segundo
# --mlock  → Bloquea modelo en RAM (no swappea)
# -fa      → Flash Attention (más rápido en ARM)
# -c 2048  → Contexto suficiente para conversaciones largas
# ══════════════════════════════════════════════════════════════

echo "⚡ Arrancando Gemma 4 (8 núcleos, máxima velocidad)..."
cd ~/llama.cpp
./build/bin/llama-server \
    -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf \
    --host 127.0.0.1 \
    --port 8080 \
    -c 2048 \
    -t 6 \
    -tb 8 \
    -b 512 \
    --mlock \
    -fa \
    > ~/.lola/logs/llama-server.log 2>&1 &

# Esperar modelo
for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:8080/health 2>/dev/null | grep -q "ok"; then
        echo "✅ Gemma 4 lista (8 núcleos activos)"
        break
    fi
    # Verificar si el servidor sigue corriendo
    if ! pgrep -f llama-server > /dev/null; then
        echo "⚠️ llama-server falló, reintentando con config segura..."
        ./build/bin/llama-server \
            -m ~/.lola/models/gemma-4-e2b-it-Q4_K_M.gguf \
            --host 127.0.0.1 --port 8080 \
            -c 2048 -t 4 \
            > ~/.lola/logs/llama-server.log 2>&1 &
    fi
    echo "  ⏳ Cargando modelo ($i/60)..."
    sleep 2
done

termux-wake-lock 2>/dev/null

# Arrancar Lola
cd ~/lola-bot
python lola_escucha.py
