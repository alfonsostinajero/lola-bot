#!/data/data/com.termux/files/usr/bin/bash
# Reiniciar Lola — bash r.sh
pkill -f llama-server 2>/dev/null
pkill -f lola_escucha 2>/dev/null
pkill -f termux-speech 2>/dev/null
pkill -f termux-microphone 2>/dev/null
sleep 1
cd ~/lola-bot && git pull && bash iniciar.sh
