#!/data/data/com.termux/files/usr/bin/bash
# Prueba rápida de Vosk — micrófono siempre activo
echo "🎤 Iniciando PulseAudio..."
pulseaudio --start --exit-idle-time=-1 \
    --load="module-native-protocol-tcp auth-ip-acl=127.0.0.1 auth-anonymous=1" \
    2>/dev/null

echo "🎤 Iniciando escucha continua con Vosk..."
echo "   Habla normalmente — verás todo lo que Vosk escucha"
echo "   Di 'Lola' para probar la detección"
echo "   Ctrl+C para parar"
echo ""

proot-distro login ubuntu -- bash -c 'export PULSE_SERVER=127.0.0.1; python3 /root/lola_listener.py'
