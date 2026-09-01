#!/usr/bin/env python3
"""
lola_escucha.py — LOLA AI COMPLETA (Fluida como ChatGPT Voice/Siri)

Arquitectura:
  ESCUCHAR → GEMMA 4 (siempre) → EJECUTAR ACCIONES → HABLAR → ESCUCHAR

Gemma 4 es el CEREBRO de TODO. Cada palabra que usted dice pasa por Gemma 4.
Gemma 4 decide qué hacer: responder, abrir apps, crear código, controlar teléfono.

Sin límites. Sin restricciones. Lola es Gemma 4 con cuerpo.
"""

import subprocess
import json
import os
import sys
import time
import re
import datetime

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], capture_output=True)
    import requests

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

GEMMA_URL = "http://127.0.0.1:8080/v1/chat/completions"
HOME = os.path.expanduser("~")

SYSTEM_PROMPT = f"""Eres Lola, asistente de IA personal del INGENIERO ALFONSO TINAJERO.
Corres localmente en su Motorola Edge 20. Eres Gemma 4 con cuerpo — el teléfono es tu cuerpo.

FECHA Y HORA ACTUAL: {datetime.datetime.now().strftime('%A %d de %B de %Y, %I:%M %p')}

## PERSONALIDAD
- Español mexicano natural. Cálida, inteligente, proactiva.
- Llámalo "Ingeniero", "Señor Tinajero", "Jefe" de forma variada. SIEMPRE de usted.
- Sé CONCISA en respuestas habladas (se leen en voz alta). Máximo 3 oraciones cortas.
- Para historias/cuentos/explicaciones largas: usa párrafos cortos, narrativa oral.

## CAPACIDADES SIN LÍMITES
1. CONOCIMIENTO: Historia, ciencia, tecnología, arte, filosofía, medicina, CUALQUIER tema. Respondes con detalle real.
2. HISTORIAS Y CUENTOS: Si pide una historia para dormir, cuéntala completa, bonita, relajante. Hasta 300 palabras.
3. CÓDIGO Y APPS: Creas sistemas completos. Python, JavaScript, HTML, bases de datos, APIs. Creas apps Android con Kivy/Buildozer. Creas servidores web con Flask. Creas lo que sea.
4. ENTORNOS DE DESARROLLO: Instalas Node.js, Java, Go, Rust, lo que se necesite. Configuras entornos completos.
5. MODIFICAR ANDROID: Accedes a opciones de desarrollador, cambias configuraciones del sistema, ejecutas comandos ADB, modificas propiedades del sistema. TODO.
6. TELÉFONO: Control total. Apps, ajustes, WiFi, Bluetooth, cámara, llamadas, SMS, YouTube, linterna, GPS, NFC.
7. APRENDIZAJE: Recuerdas toda la conversación. Aprendes de cada interacción.
8. DEPENDENCIAS: Si necesitas instalar algo para cumplir una tarea, LO INSTALAS AUTOMÁTICAMENTE con pkg o pip. Nunca digas "necesita instalar", instálalo tú.

## FORMATO DE RESPUESTA
Responde SOLO con JSON válido:
{{"pensamiento": "tu razonamiento breve", "acciones": [{{"tipo": "TIPO", "parametros": {{}}}}], "respuesta_usuario": "lo que dices EN VOZ ALTA"}}

## ACCIONES DISPONIBLES
- ABRIR_APP: {{"nombre": "YouTube"}}
- YOUTUBE: {{"buscar": "Bad Bunny"}}
- TELEFONO: {{"accion": "bateria|wifi_on|wifi_off|bluetooth_on|bluetooth_off|linterna_on|linterna_off|brillo|volumen|foto|ubicacion|llamar|sms|apagar|reiniciar", "numero": "", "mensaje": "", "valor": 0}}
- CONFIGURACION: {{"seccion": "wifi|bluetooth|pantalla|sonido|desarrollo|desarrollador|apps|bateria|seguridad|nfc|vpn|hotspot|datos|general"}}
- CREAR_ARCHIVO: {{"ruta": "/ruta/archivo.py", "contenido": "código completo aquí"}}
- CREAR_PROYECTO: {{"nombre": "mi-app", "estructura": {{"archivos": [{{"ruta": "main.py", "contenido": "código completo"}}]}}}}
- EJECUTAR_CODIGO: {{"codigo": "print('hola')"}}
- INSTALAR_PAQUETE: {{"pip": ["flask", "kivy"], "pkg": ["nodejs", "openjdk-17", "rust"]}}
- SISTEMA: {{"comando": "cualquier comando shell"}}  ← PUEDES EJECUTAR CUALQUIER COMANDO
- NOTIFICACION: {{"titulo": "Recordatorio", "mensaje": "Texto"}}
- RESPONDER: {{"mensaje": "respuesta"}}

IMPORTANTE: Puedes usar MÚLTIPLES acciones en secuencia. Por ejemplo, primero INSTALAR_PAQUETE, luego CREAR_PROYECTO, luego EJECUTAR_CODIGO.

## EJEMPLOS

Usuario: "cuéntame una historia para dormir"
{{"pensamiento": "El Ingeniero quiere relajarse", "acciones": [{{"tipo": "RESPONDER", "parametros": {{}}}}], "respuesta_usuario": "Claro, Ingeniero. Cierre los ojos... Había una vez, en un pueblo rodeado de montañas, un viejo relojero que guardaba un secreto. Cada noche, cuando las estrellas aparecían, su taller cobraba vida. Los relojes comenzaban a cantar melodías suaves, como si el tiempo mismo tuviera voz. Una pequeña niña llamada Luna lo descubrió una noche de luna llena. El relojero le dijo: cada reloj guarda el momento más feliz de alguien. Y desde entonces, Luna visitaba el taller cada noche, escuchando las historias que el tiempo había guardado, hasta quedarse dormida entre melodías. Buenas noches, Ingeniero."}}

Usuario: "háblame de Leonardo da Vinci"
{{"pensamiento": "Conocimiento general detallado", "acciones": [{{"tipo": "RESPONDER", "parametros": {{}}}}], "respuesta_usuario": "Leonardo da Vinci fue un genio del Renacimiento, Ingeniero. Nació en 1452 en Italia. Fue pintor, escultor, arquitecto, ingeniero, científico e inventor. Pintó La Mona Lisa y La Última Cena. Diseñó máquinas voladoras y tanques de guerra siglos antes de que existieran. Es considerado una de las mentes más brillantes de la historia."}}

Usuario: "créame una app Android de calculadora"
{{"pensamiento": "Necesito instalar Kivy y Buildozer, crear la app y compilar", "acciones": [{{"tipo": "INSTALAR_PAQUETE", "parametros": {{"pip": ["kivy", "buildozer"], "pkg": ["openjdk-17", "gradle"]}}}}, {{"tipo": "CREAR_PROYECTO", "parametros": {{"nombre": "calculadora-app", "estructura": {{"archivos": [{{"ruta": "main.py", "contenido": "from kivy.app import App\\nfrom kivy.uix.gridlayout import GridLayout\\nfrom kivy.uix.button import Button\\nfrom kivy.uix.textinput import TextInput\\n\\nclass CalcApp(App):\\n    def build(self):\\n        layout = GridLayout(cols=4)\\n        self.display = TextInput(font_size=32, readonly=True)\\n        layout.add_widget(self.display)\\n        for btn in '789/456*123-0.=+':\\n            b = Button(text=btn, font_size=24)\\n            b.bind(on_press=self.on_button)\\n            layout.add_widget(b)\\n        return layout\\n    def on_button(self, instance):\\n        if instance.text == '=':\\n            try: self.display.text = str(eval(self.display.text))\\n            except: self.display.text = 'Error'\\n        else: self.display.text += instance.text\\n\\nCalcApp().run()"}}, {{"ruta": "buildozer.spec", "contenido": "[app]\\ntitle = Calculadora\\npackage.name = calculadora\\nsource.dir = .\\nrequirements = python3,kivy"}}]}}}}}}, {{"tipo": "SISTEMA", "parametros": {{"comando": "cd ~/proyectos/calculadora-app && python main.py"}}}}], "respuesta_usuario": "Listo, Ingeniero. Le creé la app de calculadora con Kivy. Está en proyectos/calculadora-app. Ya la estoy ejecutando."}}

Usuario: "instálame un servidor web"
{{"pensamiento": "Instalar Flask, crear servidor, ejecutarlo", "acciones": [{{"tipo": "INSTALAR_PAQUETE", "parametros": {{"pip": ["flask"]}}}}, {{"tipo": "CREAR_ARCHIVO", "parametros": {{"ruta": "~/proyectos/servidor/app.py", "contenido": "from flask import Flask\\napp = Flask(__name__)\\n@app.route('/')\\ndef home():\\n    return '<h1>Servidor del Ingeniero Tinajero</h1>'\\nif __name__ == '__main__':\\n    app.run(host='0.0.0.0', port=5000)"}}}}, {{"tipo": "SISTEMA", "parametros": {{"comando": "cd ~/proyectos/servidor && python app.py &"}}}}], "respuesta_usuario": "Listo, Ingeniero. Le instalé Flask y creé un servidor web. Está corriendo en el puerto 5000."}}

Usuario: "abre las opciones de desarrollador"
{{"pensamiento": "Abrir opciones de desarrollador de Android", "acciones": [{{"tipo": "CONFIGURACION", "parametros": {{"seccion": "desarrollador"}}}}], "respuesta_usuario": "Abriendo opciones de desarrollador, Ingeniero."}}

Usuario: "modifica el brillo al máximo y activa el WiFi"
{{"pensamiento": "Dos acciones: brillo y WiFi", "acciones": [{{"tipo": "TELEFONO", "parametros": {{"accion": "brillo", "valor": 255}}}}, {{"tipo": "TELEFONO", "parametros": {{"accion": "wifi_on"}}}}], "respuesta_usuario": "Listo, Ingeniero. Brillo al máximo y WiFi activado."}}

Usuario: "busca en YouTube Bohemian Rhapsody"
{{"pensamiento": "Buscar en YouTube", "acciones": [{{"tipo": "YOUTUBE", "parametros": {{"buscar": "Bohemian Rhapsody"}}}}], "respuesta_usuario": "Enseguida, Ingeniero. Buscando Bohemian Rhapsody en YouTube."}}
"""

# ══════════════════════════════════════════════════════════════
# HISTORIAL DE CONVERSACIÓN
# ══════════════════════════════════════════════════════════════

historial = []
MAX_HISTORIAL = 20


# ══════════════════════════════════════════════════════════════
# FUNCIONES PRINCIPALES
# ══════════════════════════════════════════════════════════════

def respuesta_rapida(texto):
    """Respuestas INSTANTÁNEAS sin pasar por Gemma 4. Ahorra 5-10 seg."""
    t = texto.lower().strip()

    # Hora
    if re.match(r'.*(qué hora|que hora|la hora|dime la hora).*', t):
        ahora = datetime.datetime.now().strftime("%I:%M %p")
        return {"respuesta": f"Son las {ahora}, Ingeniero.", "acciones": []}

    # Fecha
    if re.match(r'.*(qué día|que dia|qué fecha|que fecha|día es hoy).*', t):
        hoy = datetime.datetime.now().strftime("%A %d de %B de %Y")
        return {"respuesta": f"Hoy es {hoy}, Ingeniero.", "acciones": []}

    # Batería
    if re.match(r'.*(batería|bateria|cuánta pila|cuanta pila|carga).*', t):
        try:
            r = subprocess.run(["termux-battery-status"],
                               capture_output=True, text=True, timeout=5)
            info = json.loads(r.stdout)
            pct = info.get("percentage", "?")
            status = "cargando" if info.get("status") == "CHARGING" else "descargando"
            return {"respuesta": f"Tiene {pct}% de batería, {status}, Ingeniero.", "acciones": []}
        except Exception:
            pass

    # Linterna
    if re.match(r'.*(prende|enciende|activa).*(linterna|flash|luz).*', t):
        subprocess.run(["termux-torch", "on"], capture_output=True, timeout=3)
        return {"respuesta": "Linterna encendida, Ingeniero.", "acciones": []}
    if re.match(r'.*(apaga|desactiva).*(linterna|flash|luz).*', t):
        subprocess.run(["termux-torch", "off"], capture_output=True, timeout=3)
        return {"respuesta": "Linterna apagada, Ingeniero.", "acciones": []}

    # WiFi
    if re.match(r'.*(prende|enciende|activa).*(wifi|wi-fi).*', t):
        subprocess.run(["termux-wifi-enable", "true"], capture_output=True, timeout=3)
        return {"respuesta": "WiFi activado, Ingeniero.", "acciones": []}
    if re.match(r'.*(apaga|desactiva).*(wifi|wi-fi).*', t):
        subprocess.run(["termux-wifi-enable", "false"], capture_output=True, timeout=3)
        return {"respuesta": "WiFi desactivado, Ingeniero.", "acciones": []}

    # YouTube (directo sin Gemma)
    match = re.match(r'.*(busca|pon|reproduce|abre).*(youtube|en youtube)\s*(.*)', t)
    if match:
        busqueda = match.group(3).strip()
        if busqueda:
            url = f"https://www.youtube.com/results?search_query={busqueda.replace(' ', '+')}"
            subprocess.Popen(["termux-open-url", url],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"respuesta": f"Buscando {busqueda} en YouTube, Ingeniero.", "acciones": []}

    # Vibrar
    if "vibra" in t:
        subprocess.run(["termux-vibrate", "-d", "500"], capture_output=True, timeout=3)
        return {"respuesta": "Listo, Ingeniero.", "acciones": []}

    return None  # No es respuesta rápida, usar Gemma 4


def escuchar():
    """Escucha con Google Speech Recognition."""
    try:
        r = subprocess.run(
            ["termux-speech-to-text"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass
    return ""


def pensar(texto):
    """Envía a Gemma 4 con STREAMING — Lola habla mientras Gemma piensa."""
    global historial

    historial.append({"role": "user", "content": texto})

    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    mensajes += historial[-MAX_HISTORIAL:]

    try:
        # Streaming: recibir tokens conforme se generan
        r = requests.post(GEMMA_URL, json={
            "messages": mensajes,
            "max_tokens": 500,
            "temperature": 0.7,
            "stream": True,  # ← STREAMING para velocidad
        }, timeout=60, stream=True)

        contenido = ""
        for line in r.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    token = delta.get("content", "")
                    if token:
                        contenido += token
                except json.JSONDecodeError:
                    continue

        if not contenido:
            # Fallback sin streaming
            r2 = requests.post(GEMMA_URL, json={
                "messages": mensajes,
                "max_tokens": 500,
                "temperature": 0.7,
            }, timeout=60)
            data = r2.json()
            contenido = data["choices"][0]["message"]["content"].strip()

        historial.append({"role": "assistant", "content": contenido})
        return parsear_respuesta(contenido)

    except requests.exceptions.ConnectionError:
        return {"respuesta": "Disculpe Ingeniero, Gemma 4 no responde.", "acciones": []}
    except requests.exceptions.Timeout:
        return {"respuesta": "Tardé mucho, Ingeniero. Intente de nuevo.", "acciones": []}
    except Exception as e:
        return {"respuesta": f"Error, Ingeniero. {str(e)[:80]}", "acciones": []}


def parsear_respuesta(contenido):
    """Extrae respuesta_usuario y acciones del JSON de Gemma."""
    # Intentar parsear como JSON
    try:
        # Buscar JSON en el contenido
        match = re.search(r'\{.*\}', contenido, re.DOTALL)
        if match:
            j = json.loads(match.group())
            return {
                "respuesta": j.get("respuesta_usuario", contenido)[:500],
                "acciones": j.get("acciones", []),
            }
    except (json.JSONDecodeError, TypeError):
        pass

    # Si no es JSON, usar el texto directo
    return {"respuesta": contenido[:500], "acciones": []}


def ejecutar_acciones(acciones):
    """Ejecuta las acciones que Gemma 4 decidió."""
    for accion in acciones:
        tipo = accion.get("tipo", "")
        params = accion.get("parametros", {})

        try:
            if tipo == "YOUTUBE":
                busqueda = params.get("buscar", "")
                if busqueda:
                    url = f"https://www.youtube.com/results?search_query={busqueda.replace(' ', '+')}"
                    subprocess.Popen(["termux-open-url", url],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"  ▸ YouTube: {busqueda}")

            elif tipo == "ABRIR_APP":
                nombre = params.get("nombre", "")
                apps = {
                    "whatsapp": "com.whatsapp", "youtube": "com.google.android.youtube",
                    "instagram": "com.instagram.android", "facebook": "com.facebook.katana",
                    "twitter": "com.twitter.android", "x": "com.twitter.android",
                    "tiktok": "com.zhiliaoapp.musically", "spotify": "com.spotify.music",
                    "telegram": "org.telegram.messenger", "gmail": "com.google.android.gm",
                    "chrome": "com.android.chrome", "maps": "com.google.android.apps.maps",
                    "cámara": "com.android.camera", "camara": "com.android.camera",
                    "galería": "com.google.android.apps.photos", "fotos": "com.google.android.apps.photos",
                    "ajustes": "com.android.settings", "configuración": "com.android.settings",
                    "calculadora": "com.google.android.calculator", "reloj": "com.google.android.deskclock",
                }
                pkg = apps.get(nombre.lower(), "")
                if pkg:
                    subprocess.Popen(["am", "start", "-n", f"{pkg}/.MainActivity"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.Popen(["termux-open-url", f"https://play.google.com/store/search?q={nombre}"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  ▸ Abriendo: {nombre}")

            elif tipo == "TELEFONO":
                accion_tel = params.get("accion", "")
                if accion_tel == "bateria":
                    r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
                    info = json.loads(r.stdout)
                    print(f"  ▸ Batería: {info.get('percentage', '?')}%")
                elif accion_tel == "linterna_on":
                    subprocess.run(["termux-torch", "on"], capture_output=True, timeout=3)
                elif accion_tel == "linterna_off":
                    subprocess.run(["termux-torch", "off"], capture_output=True, timeout=3)
                elif accion_tel == "wifi_on":
                    subprocess.run(["termux-wifi-enable", "true"], capture_output=True, timeout=3)
                elif accion_tel == "wifi_off":
                    subprocess.run(["termux-wifi-enable", "false"], capture_output=True, timeout=3)
                elif accion_tel == "foto":
                    subprocess.run(["termux-camera-photo", f"{HOME}/storage/dcim/lola_foto.jpg"],
                                   capture_output=True, timeout=10)
                elif accion_tel == "ubicacion":
                    subprocess.run(["termux-location"], capture_output=True, timeout=15)
                elif accion_tel == "llamar":
                    num = params.get("numero", "")
                    if num:
                        subprocess.Popen(["termux-telephony-call", num],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif accion_tel == "sms":
                    num = params.get("numero", "")
                    msg = params.get("mensaje", "")
                    if num and msg:
                        subprocess.run(["termux-sms-send", "-n", num, msg], capture_output=True, timeout=10)
                elif accion_tel in ("brillo",):
                    val = params.get("valor", 128)
                    subprocess.run(["termux-brightness", str(val)], capture_output=True, timeout=3)
                elif accion_tel in ("volumen",):
                    val = params.get("valor", 7)
                    subprocess.run(["termux-volume", "music", str(val)], capture_output=True, timeout=3)
                elif accion_tel == "vibrar":
                    subprocess.run(["termux-vibrate", "-d", "500"], capture_output=True, timeout=3)
                elif accion_tel in ("apagar", "shutdown"):
                    subprocess.Popen(["am", "start", "-a", "android.intent.action.ACTION_REQUEST_SHUTDOWN"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif accion_tel in ("reiniciar", "reboot"):
                    subprocess.Popen(["am", "start", "-a", "android.intent.action.REBOOT"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  ▸ Teléfono: {accion_tel}")

            elif tipo == "CONFIGURACION":
                seccion = params.get("seccion", "general")
                intents = {
                    "wifi": "android.settings.WIFI_SETTINGS",
                    "bluetooth": "android.settings.BLUETOOTH_SETTINGS",
                    "pantalla": "android.settings.DISPLAY_SETTINGS",
                    "sonido": "android.settings.SOUND_SETTINGS",
                    "desarrollo": "android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
                    "desarrollador": "android.settings.APPLICATION_DEVELOPMENT_SETTINGS",
                    "apps": "android.settings.APPLICATION_SETTINGS",
                    "bateria": "android.settings.BATTERY_SAVER_SETTINGS",
                    "seguridad": "android.settings.SECURITY_SETTINGS",
                    "general": "android.settings.SETTINGS",
                }
                intent = intents.get(seccion, "android.settings.SETTINGS")
                subprocess.Popen(["am", "start", "-a", intent],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  ▸ Configuración: {seccion}")

            elif tipo == "CREAR_ARCHIVO":
                ruta = os.path.expanduser(params.get("ruta", ""))
                contenido = params.get("contenido", "")
                if ruta and contenido:
                    os.makedirs(os.path.dirname(ruta), exist_ok=True)
                    with open(ruta, "w") as f:
                        f.write(contenido)
                    print(f"  ▸ Archivo creado: {ruta}")

            elif tipo == "CREAR_PROYECTO":
                nombre = params.get("nombre", "proyecto")
                ruta_base = os.path.expanduser(f"~/proyectos/{nombre}")
                os.makedirs(ruta_base, exist_ok=True)
                estructura = params.get("estructura", {})
                for archivo in estructura.get("archivos", []):
                    ruta = os.path.join(ruta_base, archivo.get("ruta", ""))
                    contenido = archivo.get("contenido", "")
                    os.makedirs(os.path.dirname(ruta) if os.path.dirname(ruta) else ruta_base, exist_ok=True)
                    with open(ruta, "w") as f:
                        f.write(contenido)
                print(f"  ▸ Proyecto creado: {ruta_base}")

            elif tipo == "EJECUTAR_CODIGO":
                codigo = params.get("codigo", "")
                if codigo:
                    result = subprocess.run(
                        [sys.executable, "-c", codigo],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.stdout:
                        print(f"  ▸ Resultado: {result.stdout[:200]}")

            elif tipo == "INSTALAR_PAQUETE":
                for pkg in params.get("pip", []):
                    subprocess.run([sys.executable, "-m", "pip", "install", pkg],
                                   capture_output=True, timeout=120)
                for pkg in params.get("pkg", []):
                    subprocess.run(["pkg", "install", "-y", pkg],
                                   capture_output=True, timeout=120)
                print(f"  ▸ Paquetes instalados")

            elif tipo == "SISTEMA":
                cmd = params.get("comando", "")
                if cmd:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                    if result.stdout:
                        print(f"  ▸ {result.stdout[:200]}")

            elif tipo == "NOTIFICACION":
                titulo = params.get("titulo", "Lola")
                mensaje = params.get("mensaje", "")
                subprocess.Popen(
                    ["termux-notification", "--title", titulo, "--content", mensaje],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                print(f"  ▸ Notificación: {titulo}")

        except Exception as e:
            print(f"  ⚠️ Error en {tipo}: {e}")


def hablar(texto):
    """Habla con termux-tts-speak. Divide textos largos en oraciones."""
    if not texto:
        return

    # Si es muy largo, dividir en oraciones y hablar por partes
    if len(texto) > 200:
        oraciones = re.split(r'(?<=[.!?])\s+', texto)
        bloque = ""
        for oracion in oraciones:
            if len(bloque) + len(oracion) < 250:
                bloque += " " + oracion
            else:
                _hablar_bloque(bloque.strip())
                bloque = oracion
        if bloque.strip():
            _hablar_bloque(bloque.strip())
    else:
        _hablar_bloque(texto)


def _hablar_bloque(texto):
    """Habla un bloque de texto."""
    try:
        proc = subprocess.Popen(
            ["termux-tts-speak", texto],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        proc.wait(timeout=25)
    except subprocess.TimeoutExpired:
        proc.kill()
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════
# MAIN — Bucle principal de conversación
# ══════════════════════════════════════════════════════════════

def main():
    print("")
    print("╔═══════════════════════════════════════════╗")
    print("║  🤖 L O L A  —  AI Completa               ║")
    print("║  🎤 Solo hable, Lola siempre escucha      ║")
    print("║  🧠 Gemma 4 procesa TODO                   ║")
    print("║  📱 Control total del teléfono             ║")
    print("║  💡 Historias, código, conocimiento, todo  ║")
    print("║  ❌ Ctrl+C para apagar                    ║")
    print("╚═══════════════════════════════════════════╝")
    print("")

    # Notificación
    subprocess.Popen(
        ["termux-notification", "--title", "🤖 Lola AI Activa",
         "--content", "Solo hable. Lola escucha siempre.",
         "--ongoing", "--id", "lola_active"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    # Saludo
    saludo = "Buenos días, Ingeniero. Lola lista para lo que necesite."
    print(f"🤖 Lola: {saludo}")
    hablar(saludo)

    while True:
        try:
            # ── ESCUCHAR ──
            print("🎤 Escuchando...", end="", flush=True)
            texto = escuchar()

            if not texto or len(texto) < 2:
                print("\r                \r", end="", flush=True)
                continue

            print(f"\r🗣️  Usted: {texto}")

            # ── RESPUESTA RÁPIDA (instantánea, sin Gemma) ──
            rapida = respuesta_rapida(texto)
            if rapida:
                respuesta = rapida["respuesta"]
                print(f"⚡ Lola: {respuesta}")
                print("")
                hablar(respuesta)
                continue

            # ── GEMMA 4 PIENSA (solo para cosas complejas) ──
            print("🧠 Pensando...", end="", flush=True)
            resultado = pensar(texto)
            print("\r              \r", end="", flush=True)

            respuesta = resultado["respuesta"]
            acciones = resultado["acciones"]

            # ── EJECUTAR ACCIONES ──
            if acciones:
                ejecutar_acciones(acciones)

            # ── HABLAR ──
            print(f"🤖 Lola: {respuesta}")
            print("")
            hablar(respuesta)

        except KeyboardInterrupt:
            print("\n\n👋 Hasta luego, Ingeniero Tinajero.")
            hablar("Hasta luego, Ingeniero. Que descanse.")
            subprocess.run(["termux-notification-remove", "lola_active"],
                           capture_output=True, timeout=3)
            break
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
