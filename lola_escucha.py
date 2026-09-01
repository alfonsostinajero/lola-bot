#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
  LOLA AI — Asistente Completa del Ingeniero Alfonso Tinajero
  Motor: Gemma 4 (llama.cpp) | Voz: termux-tts-speak
  Control total del teléfono | Código | Historias | Todo
═══════════════════════════════════════════════════════════════
"""
import subprocess, json, os, sys, datetime, re, time

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], capture_output=True)
    import requests

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════
URL = "http://127.0.0.1:8080/v1/chat/completions"
HOME = os.path.expanduser("~")
HORA = datetime.datetime.now().strftime("%I:%M %p")
FECHA = datetime.datetime.now().strftime("%A %d de %B de %Y")

SYSTEM_PROMPT = f"""Eres Lola, asistente AI del Ingeniero Alfonso Tinajero. Fecha: {FECHA}, {HORA}.
Español mexicano, cálida. Llámalo Ingeniero, Jefe o Señor. De usted. Responde BREVE (1-2 oraciones).
Para historias usa más texto. Sabes de TODO. Si pide acción del teléfono, usa tags: [YOUTUBE:búsqueda] [ABRIR:app] [LINTERNA:on/off] [BRILLO:0-255] [SISTEMA:comando].
Si alguien más habla, responde amable. NUNCA digas no puedo."""

HISTORIAL = [{"role": "system", "content": SYSTEM_PROMPT}]
MAX_HIST = 12

# ══════════════════════════════════════════════════════════════
# VOZ — Hablar
# ══════════════════════════════════════════════════════════════
def hablar(texto):
    """Habla por voz. Divide textos largos en bloques."""
    if not texto:
        return
    # Limpiar tags de acción del texto hablado
    limpio = re.sub(r'\[.*?\]', '', texto).strip()
    limpio = re.sub(r'\s+', ' ', limpio)
    if not limpio:
        return

    # Dividir en bloques de ~250 chars por oración
    if len(limpio) > 250:
        oraciones = re.split(r'(?<=[.!?])\s+', limpio)
        bloque = ""
        for o in oraciones:
            if len(bloque) + len(o) < 250:
                bloque += " " + o
            else:
                _decir(bloque.strip())
                bloque = o
        if bloque.strip():
            _decir(bloque.strip())
    else:
        _decir(limpio)


def _decir(texto):
    try:
        p = subprocess.Popen(["termux-tts-speak", texto],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.wait(timeout=25)
    except subprocess.TimeoutExpired:
        p.kill()
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════
# RESPUESTAS RÁPIDAS — Sin Gemma 4 (<1 segundo)
# ══════════════════════════════════════════════════════════════
def corregir_texto(texto):
    """Corrige errores comunes del reconocimiento de voz."""
    fixes = {
        "bola": "hola", "ola": "hola", "jola": "hola", "olla": "hola",
        "loa": "lola", "lolla": "lola", "nola": "lola",
        "bueno": "buenos", "wenas": "buenas",
        "cómo": "como", "k": "que", "q": "que",
    }
    palabras = texto.lower().split()
    corregidas = [fixes.get(p, p) for p in palabras]
    return " ".join(corregidas)


def rapida(texto):
    t = corregir_texto(texto).lower().strip()

    # ── SALUDOS ──
    if re.search(r'(hola|hey|buenas|buenos|qué onda|que onda|saludos|qué tal|que tal)', t):
        import random
        saludos = [
            "¡Hola, Ingeniero! ¿En qué le ayudo?",
            "¡Buenas, Jefe! A sus órdenes.",
            "¡Qué tal, Ingeniero! Aquí estoy para lo que necesite.",
            "¡Hola! ¿Qué se le ofrece, Señor Tinajero?",
            "¡Buenas, Ingeniero! Lola lista.",
        ]
        return random.choice(saludos)

    # ── DESPEDIDAS ──
    if re.search(r'(adiós|adios|bye|hasta luego|nos vemos|chao)', t):
        return "Hasta luego, Ingeniero. Que le vaya muy bien."

    # ── CÓMO ESTÁS ──
    if re.search(r'(como estas|como vas|como te va|como andas)', t):
        return "Muy bien, Ingeniero. Lista para servirle. ¿En qué le ayudo?"

    # ── GRACIAS ──
    if re.search(r'(gracias|te lo agradezco|muy amable)', t):
        return "Con gusto, Ingeniero. Para eso estoy."

    # ── QUIÉN ERES ──
    if re.search(r'(quién eres|quien eres|cómo te llamas|como te llamas|tu nombre)', t):
        return "Soy Lola, su asistente personal con inteligencia artificial, Ingeniero."

    # ── QUÉ PUEDES HACER ──
    if re.search(r'(qué puedes|que puedes|qué sabes|que sabes|qué haces|que haces)', t):
        return "Puedo controlar su teléfono, contar historias, crear código, buscar en YouTube, y responder cualquier pregunta, Ingeniero."

    # ── SÍ / NO ──
    if t in ("si", "sí", "ok", "vale", "está bien", "esta bien", "claro", "dale"):
        return "Perfecto, Ingeniero. ¿Algo más?"
    if t in ("no", "nada", "nada más", "nada mas", "así está bien", "asi esta bien"):
        return "Entendido, Ingeniero. Aquí estaré."

    # ── NOMBRE DE LOLA ──
    if re.search(r'^lola$', t):
        return "¿Sí, Ingeniero? Dígame."
    # Hora
    if re.search(r'(qué|que|dime).*(hora)', t):
        return f"Son las {datetime.datetime.now().strftime('%I:%M %p')}, Ingeniero."
    # Fecha
    if re.search(r'(qué|que).*(día|dia|fecha)', t) or "dia es hoy" in t:
        return f"Hoy es {datetime.datetime.now().strftime('%A %d de %B de %Y')}, Ingeniero."
    # Batería
    if re.search(r'(batería|bateria|pila|carga)', t):
        try:
            r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
            info = json.loads(r.stdout)
            return f"Tiene {info.get('percentage','?')}% de batería, Ingeniero."
        except: pass
    # Linterna
    if re.search(r'(prende|enciende).*(linterna|flash)', t):
        subprocess.run(["termux-torch", "on"], capture_output=True, timeout=3)
        return "Linterna encendida, Ingeniero."
    if re.search(r'(apaga).*(linterna|flash)', t):
        subprocess.run(["termux-torch", "off"], capture_output=True, timeout=3)
        return "Linterna apagada, Ingeniero."
    # WiFi
    if re.search(r'(prende|enciende|activa).*(wifi)', t):
        subprocess.run(["termux-wifi-enable", "true"], capture_output=True, timeout=3)
        return "WiFi activado, Ingeniero."
    if re.search(r'(apaga|desactiva).*(wifi)', t):
        subprocess.run(["termux-wifi-enable", "false"], capture_output=True, timeout=3)
        return "WiFi desactivado, Ingeniero."
    # Bluetooth
    if re.search(r'(prende|enciende|activa).*(bluetooth)', t):
        subprocess.run(["termux-bluetooth-enable", "true"], capture_output=True, timeout=3)
        return "Bluetooth activado, Ingeniero."
    if re.search(r'(apaga|desactiva).*(bluetooth)', t):
        subprocess.run(["termux-bluetooth-enable", "false"], capture_output=True, timeout=3)
        return "Bluetooth desactivado, Ingeniero."
    # Brillo
    if re.search(r'(brillo).*(máximo|maximo|max|sube)', t) or re.search(r'(sube|más|mas).*(brillo)', t):
        subprocess.run(["termux-brightness", "255"], capture_output=True, timeout=3)
        return "Brillo al máximo, Ingeniero."
    if re.search(r'(brillo).*(mínimo|minimo|baja)', t) or re.search(r'(baja).*(brillo)', t):
        subprocess.run(["termux-brightness", "30"], capture_output=True, timeout=3)
        return "Brillo al mínimo, Ingeniero."
    # Volumen
    if re.search(r'(volumen|vol).*(máximo|maximo|sube)', t) or re.search(r'(sube).*(volumen)', t):
        subprocess.run(["termux-volume", "music", "15"], capture_output=True, timeout=3)
        return "Volumen al máximo, Ingeniero."
    if re.search(r'(volumen|vol).*(mínimo|minimo|baja|silencio)', t) or re.search(r'(baja).*(volumen)', t):
        subprocess.run(["termux-volume", "music", "0"], capture_output=True, timeout=3)
        return "Volumen al mínimo, Ingeniero."
    # Notificaciones
    if re.search(r'(notificaciones|qué hay nuevo|que hay nuevo)', t):
        try:
            r = subprocess.run(["termux-notification-list"], capture_output=True, text=True, timeout=5)
            notifs = json.loads(r.stdout)
            if notifs:
                resumen = [f"{n.get('title','')}: {n.get('content','')[:40]}" for n in notifs[:3] if n.get('title')]
                return f"Tiene {len(notifs)} notificaciones. {'. '.join(resumen)}"
            return "No tiene notificaciones, Ingeniero."
        except: pass
    # SMS
    if re.search(r'(mensajes|sms|lee.*mensaje)', t):
        try:
            r = subprocess.run(["termux-sms-list", "-l", "3"], capture_output=True, text=True, timeout=5)
            msgs = json.loads(r.stdout)
            if msgs:
                resumen = [f"De {m.get('number','?')}: {m.get('body','')[:40]}" for m in msgs[:3]]
                return f"Últimos mensajes: {'. '.join(resumen)}"
        except: pass
    # Foto
    if re.search(r'(toma|saca).*(foto)', t):
        ruta = os.path.expanduser("~/storage/dcim/lola_foto.jpg")
        subprocess.run(["termux-camera-photo", ruta], capture_output=True, timeout=10)
        return "Foto tomada, Ingeniero."
    # Ubicación
    if re.search(r'(dónde estoy|donde estoy|ubicación|ubicacion|gps)', t):
        try:
            r = subprocess.run(["termux-location", "-p", "gps", "-r", "once"],
                               capture_output=True, text=True, timeout=15)
            loc = json.loads(r.stdout)
            return f"Está en latitud {loc.get('latitude','?')}, longitud {loc.get('longitude','?')}, Ingeniero."
        except: pass
    # Llamadas
    if re.search(r'(quién.*llamó|quien.*llamo|historial.*llamadas)', t):
        try:
            r = subprocess.run(["termux-call-log", "-l", "5"], capture_output=True, text=True, timeout=5)
            calls = json.loads(r.stdout)
            if calls:
                resumen = [f"{c.get('name', c.get('number','?'))}" for c in calls[:5]]
                return f"Últimas llamadas: {', '.join(resumen)}."
        except: pass
    # Contactos
    if re.search(r'(contactos|mis contactos)', t):
        try:
            r = subprocess.run(["termux-contact-list"], capture_output=True, text=True, timeout=10)
            contactos = json.loads(r.stdout)
            nombres = [c.get("name","") for c in contactos[:8]]
            return f"Tiene {len(contactos)} contactos. Algunos: {', '.join(nombres)}."
        except: pass
    # Clipboard
    if re.search(r'(qué copié|que copie|portapapeles|clipboard)', t):
        try:
            r = subprocess.run(["termux-clipboard-get"], capture_output=True, text=True, timeout=3)
            return f"Tiene copiado: {r.stdout.strip()[:150]}"
        except: pass
    # Wallpaper
    if re.search(r'(wallpaper|fondo.*pantalla|cambia.*fondo)', t):
        subprocess.Popen(["termux-wallpaper", "-u", "https://picsum.photos/1080/1920"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return "Cambiando fondo de pantalla, Ingeniero."
    # YouTube directo
    m = re.search(r'(?:busca|pon|reproduce).*(?:youtube|en youtube)\s*(.*)', t)
    if m and m.group(1).strip():
        q = m.group(1).strip()
        subprocess.Popen(["termux-open-url", f"https://www.youtube.com/results?search_query={q.replace(' ','+')}"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return f"Buscando {q} en YouTube, Ingeniero."

    return None

# ══════════════════════════════════════════════════════════════
# GEMMA 4 — Cerebro
# ══════════════════════════════════════════════════════════════
def pensar(texto):
    HISTORIAL.append({"role": "user", "content": texto})
    while len(HISTORIAL) > MAX_HIST:
        HISTORIAL.pop(1)

    try:
        r = requests.post(URL, json={
            "messages": HISTORIAL,
            "max_tokens": 100,
            "temperature": 0.3,
        }, timeout=30)

        data = r.json()
        resp = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        if not resp:
            return "Disculpe Ingeniero, no generé respuesta. Intente de nuevo."

        # Limpiar si Gemma devolvió JSON por error
        try:
            j = json.loads(resp)
            if isinstance(j, dict):
                resp = j.get("respuesta_usuario", j.get("mensaje", resp))
        except:
            pass

        HISTORIAL.append({"role": "assistant", "content": resp})
        return resp

    except requests.exceptions.ConnectionError:
        return "Gemma 4 no responde. ¿Está corriendo llama-server?"
    except Exception as e:
        return f"Error: {str(e)[:100]}"

# ══════════════════════════════════════════════════════════════
# EJECUTAR ACCIONES — Detecta tags en la respuesta
# ══════════════════════════════════════════════════════════════
def ejecutar_tags(texto):
    """Busca y ejecuta tags [ACCION:param] en la respuesta de Lola."""
    tags = re.findall(r'\[([A-Z_]+):?(.*?)\]', texto)
    for tag, param in tags:
        try:
            if tag == "ABRIR":
                apps = {"youtube":"com.google.android.youtube","whatsapp":"com.whatsapp",
                        "instagram":"com.instagram.android","spotify":"com.spotify.music",
                        "chrome":"com.android.chrome","gmail":"com.google.android.gm",
                        "telegram":"org.telegram.messenger","tiktok":"com.zhiliaoapp.musically",
                        "cámara":"com.android.camera","camara":"com.android.camera",
                        "ajustes":"com.android.settings","maps":"com.google.android.apps.maps",
                        "facebook":"com.facebook.katana","twitter":"com.twitter.android"}
                pkg = apps.get(param.lower(), "")
                if pkg:
                    subprocess.Popen(["am", "start", "-a", "android.intent.action.MAIN",
                                      "-n", f"{pkg}/.MainActivity"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  ▸ Abriendo {param}")

            elif tag == "YOUTUBE":
                subprocess.Popen(["termux-open-url",
                    f"https://www.youtube.com/results?search_query={param.replace(' ','+')}"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  ▸ YouTube: {param}")

            elif tag == "LINTERNA":
                subprocess.run(["termux-torch", param], capture_output=True, timeout=3)
            elif tag == "WIFI":
                subprocess.run(["termux-wifi-enable", "true" if param=="on" else "false"],
                               capture_output=True, timeout=3)
            elif tag == "BLUETOOTH":
                subprocess.run(["termux-bluetooth-enable", "true" if param=="on" else "false"],
                               capture_output=True, timeout=3)
            elif tag == "BRILLO":
                subprocess.run(["termux-brightness", param], capture_output=True, timeout=3)
            elif tag == "VOLUMEN":
                subprocess.run(["termux-volume", "music", param], capture_output=True, timeout=3)
            elif tag == "VIBRAR":
                subprocess.run(["termux-vibrate", "-d", "300"], capture_output=True, timeout=3)
            elif tag == "FOTO":
                subprocess.run(["termux-camera-photo", f"{HOME}/storage/dcim/lola_foto.jpg"],
                               capture_output=True, timeout=10)
            elif tag == "LLAMAR":
                subprocess.Popen(["termux-telephony-call", param],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif tag == "SMS":
                parts = param.split(":", 1)
                if len(parts) == 2:
                    subprocess.run(["termux-sms-send", "-n", parts[0], parts[1]],
                                   capture_output=True, timeout=10)
            elif tag == "ALARMA":
                parts = param.split(":")
                if len(parts) >= 2:
                    subprocess.Popen(["am", "start", "-a", "android.intent.action.SET_ALARM",
                                      "--ei", "android.intent.extra.alarm.HOUR", parts[0],
                                      "--ei", "android.intent.extra.alarm.MINUTES", parts[1]],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif tag == "CONFIGURACION":
                intents = {"wifi":"WIFI_SETTINGS","bluetooth":"BLUETOOTH_SETTINGS",
                           "pantalla":"DISPLAY_SETTINGS","sonido":"SOUND_SETTINGS",
                           "desarrollador":"APPLICATION_DEVELOPMENT_SETTINGS",
                           "apps":"APPLICATION_SETTINGS","general":"SETTINGS"}
                intent = intents.get(param, "SETTINGS")
                subprocess.Popen(["am", "start", "-a", f"android.settings.{intent}"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif tag == "NOTIFICACION":
                parts = param.split(":", 1)
                titulo = parts[0] if parts else "Lola"
                msg = parts[1] if len(parts) > 1 else param
                subprocess.Popen(["termux-notification", "--title", titulo, "--content", msg],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif tag == "SISTEMA":
                result = subprocess.run(param, shell=True, capture_output=True, text=True, timeout=30)
                if result.stdout.strip():
                    print(f"  ▸ {result.stdout.strip()[:200]}")
            elif tag == "ARCHIVO":
                parts = param.split(":", 1)
                if len(parts) == 2:
                    ruta = os.path.expanduser(parts[0])
                    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
                    with open(ruta, "w") as f:
                        f.write(parts[1].replace("\\n", "\n"))
                    print(f"  ▸ Archivo creado: {ruta}")
            elif tag == "INSTALAR_PIP":
                subprocess.run([sys.executable, "-m", "pip", "install", param],
                               capture_output=True, timeout=120)
                print(f"  ▸ Instalado: {param}")
            elif tag == "INSTALAR_PKG":
                subprocess.run(["pkg", "install", "-y", param],
                               capture_output=True, timeout=120)
                print(f"  ▸ Instalado: {param}")
            elif tag == "CODIGO":
                result = subprocess.run([sys.executable, "-c", param],
                                        capture_output=True, text=True, timeout=30)
                if result.stdout:
                    print(f"  ▸ Resultado: {result.stdout[:200]}")
        except Exception as e:
            print(f"  ⚠️ Error en [{tag}]: {e}")

# ══════════════════════════════════════════════════════════════
# MAIN — Conversación completa
# ══════════════════════════════════════════════════════════════
def main():
    print("")
    print("╔═══════════════════════════════════════════════╗")
    print("║  🤖 L O L A  —  AI Completa                   ║")
    print("║  🎤 Solo HABLE — Lola siempre escucha         ║")
    print("║  🧠 Gemma 4 — conocimiento, historias, código  ║")
    print("║  📱 Control total del teléfono                 ║")
    print("║  ⌨️  Escriba 't' + Enter para modo texto       ║")
    print("║  ❌ Ctrl+C para apagar                        ║")
    print("╚═══════════════════════════════════════════════╝")
    print("")

    subprocess.Popen(
        ["termux-notification", "--title", "🤖 Lola AI Activa",
         "--content", "Solo hable. Lola escucha.",
         "--ongoing", "--id", "lola_active"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    saludo = "Buenas, Ingeniero. Lola lista. Solo hable."
    print(f"🤖 Lola: {saludo}")
    hablar(saludo)

    modo_texto = False
    fallos_voz = 0

    while True:
        try:
            texto = ""

            if modo_texto:
                # ── MODO TEXTO ──
                texto = input("\n⌨️ Usted: ").strip()
                if texto.lower() == "v":
                    modo_texto = False
                    print("🎤 Cambiando a modo VOZ...")
                    continue
            else:
                # ── MODO VOZ — Solo hable ──
                subprocess.run(["termux-vibrate", "-d", "200"], capture_output=True, timeout=2)
                print("\n🎤 Hable ahora...")

                # ── MÉTODO 1: Whisper.cpp (local, preciso) ──
                whisper_bin = os.path.expanduser("~/whisper.cpp/build/bin/whisper-cli")
                whisper_model = os.path.expanduser("~/whisper.cpp/models/ggml-tiny.bin")

                if os.path.exists(whisper_bin) and os.path.exists(whisper_model):
                    try:
                        # Grabar 4 segundos
                        audio_m4a = os.path.expanduser("~/.lola/data/audio/voz.m4a")
                        audio_wav = os.path.expanduser("~/.lola/data/audio/voz.wav")
                        os.makedirs(os.path.dirname(audio_m4a), exist_ok=True)

                        # Limpiar archivos anteriores
                        for f in [audio_m4a, audio_wav]:
                            if os.path.exists(f):
                                os.remove(f)

                        # Grabar
                        subprocess.Popen(
                            ["termux-microphone-record", "-f", audio_m4a, "-l", "3"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
                        time.sleep(3)
                        subprocess.run(
                            ["termux-microphone-record", "-q"],
                            capture_output=True, timeout=3
                        )
                        time.sleep(0.5)

                        # Convertir a WAV
                        subprocess.run(
                            ["ffmpeg", "-y", "-i", audio_m4a,
                             "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le",
                             audio_wav],
                            capture_output=True, timeout=10
                        )

                        # Transcribir con Whisper
                        if os.path.exists(audio_wav):
                            r = subprocess.run(
                                [whisper_bin, "-m", whisper_model,
                                 "-f", audio_wav, "-l", "es",
                                 "--no-timestamps", "-nt"],
                                capture_output=True, text=True, timeout=15
                            )
                            texto = r.stdout.strip()
                            # Limpiar output de whisper
                            texto = re.sub(r'\[.*?\]', '', texto).strip()
                            texto = texto.replace('\n', ' ').strip()
                            if texto:
                                fallos_voz = 0
                            else:
                                fallos_voz += 1
                    except Exception as e:
                        print(f"  ⚠️ {e}")
                        fallos_voz += 1
                else:
                    # ── MÉTODO 2: Google Speech (fallback) ──
                    try:
                        r = subprocess.run(
                            ["termux-speech-to-text"],
                            capture_output=True, text=True, timeout=15
                        )
                        if r.returncode == 0 and r.stdout.strip():
                            texto = r.stdout.strip()
                            fallos_voz = 0
                        else:
                            fallos_voz += 1
                    except:
                        fallos_voz += 1

                if fallos_voz >= 5:
                    print("⚠️ Micrófono no responde. Modo texto.")
                    print("   Escriba 'v' para reintentar voz.")
                    modo_texto = True
                if not texto:
                    continue

            if not texto or len(texto) < 2:
                continue

            # Corregir errores de voz
            original = texto
            texto = corregir_texto(texto)
            if texto != original.lower():
                print(f"🗣️ Escuché: {original} → {texto}")
            else:
                print(f"🗣️ Usted: {texto}")

            # Salir
            if texto.lower() in ("salir", "exit", "bye", "adiós", "adios", "apágate", "apagate"):
                despedida = "Hasta luego, Ingeniero. Que descanse."
                print(f"🤖 Lola: {despedida}")
                hablar(despedida)
                subprocess.run(["termux-notification-remove", "lola_active"],
                               capture_output=True, timeout=3)
                break

            # Cambiar a modo texto
            if texto.lower() in ("t", "texto"):
                modo_texto = True
                print("⌨️ Modo texto activado. Escriba 'v' para volver a voz.")
                continue

            # ── RESPUESTA RÁPIDA ──
            r = rapida(texto)
            if r:
                print(f"⚡ Lola: {r}")
                hablar(r)
                continue

            # ── GEMMA 4 PIENSA ──
            print("🧠 Pensando...", end="", flush=True)
            respuesta = pensar(texto)
            print(f"\r🤖 Lola: {respuesta}")

            # ── EJECUTAR ACCIONES ──
            if "[" in respuesta:
                ejecutar_tags(respuesta)

            # ── HABLAR ──
            hablar(respuesta)

        except KeyboardInterrupt:
            print("\n👋 Adiós, Ingeniero Tinajero.")
            hablar("Hasta luego, Ingeniero.")
            subprocess.run(["termux-notification-remove", "lola_active"],
                           capture_output=True, timeout=3)
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
