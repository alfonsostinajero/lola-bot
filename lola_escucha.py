#!/usr/bin/env python3
"""
Lola AI — Versión simple que FUNCIONA.
Escriba su mensaje, Lola responde por texto y voz.
Escriba 'v' para usar micrófono.
"""
import subprocess, json, os, sys, datetime, re

try:
    import requests
except:
    subprocess.run([sys.executable, "-m", "pip", "install", "requests"], capture_output=True)
    import requests

URL = "http://127.0.0.1:8080/v1/chat/completions"
HISTORIAL = [{"role": "system", "content": f"""Eres Lola, asistente AI del Ingeniero Alfonso Tinajero.
Fecha: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}
Habla español mexicano. Llámalo Ingeniero, Señor o Jefe. Siempre de usted.
Sé breve (máximo 3 oraciones). Cálida e inteligente.
Sabes de TODO: historia, ciencia, código, cuentos, tecnología.
Si pide una historia, cuéntala completa (máximo 200 palabras).
Responde SOLO texto plano, NO uses JSON."""}]


def hablar(texto):
    if texto:
        try:
            p = subprocess.Popen(["termux-tts-speak", texto[:300]],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.wait(timeout=20)
        except:
            pass


def rapida(t):
    t = t.lower().strip()
    if "hora" in t and ("qué" in t or "que" in t or "dime" in t):
        return f"Son las {datetime.datetime.now().strftime('%I:%M %p')}, Ingeniero."
    if "fecha" in t or "día es" in t or "dia es" in t:
        return f"Hoy es {datetime.datetime.now().strftime('%d de %B de %Y')}, Ingeniero."
    if "batería" in t or "bateria" in t or "pila" in t:
        try:
            r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
            info = json.loads(r.stdout)
            return f"Tiene {info.get('percentage','?')}% de batería, Ingeniero."
        except: pass
    if "linterna" in t and ("prende" in t or "enciende" in t):
        subprocess.run(["termux-torch", "on"], capture_output=True, timeout=3)
        return "Linterna encendida, Ingeniero."
    if "linterna" in t and ("apaga" in t):
        subprocess.run(["termux-torch", "off"], capture_output=True, timeout=3)
        return "Linterna apagada, Ingeniero."
    return None


def pensar(texto):
    HISTORIAL.append({"role": "user", "content": texto})
    if len(HISTORIAL) > 20:
        HISTORIAL.pop(1)
    try:
        r = requests.post(URL, json={
            "messages": HISTORIAL,
            "max_tokens": 400,
            "temperature": 0.7,
        }, timeout=60)
        data = r.json()
        resp = data["choices"][0]["message"]["content"].strip()

        # Si Gemma devolvió JSON, extraer respuesta_usuario
        try:
            j = json.loads(resp)
            if "respuesta_usuario" in j:
                resp = j["respuesta_usuario"]
        except:
            pass

        # Limpiar JSON basura
        resp = re.sub(r'\{.*?\}', '', resp, flags=re.DOTALL).strip()
        if not resp:
            resp = "Disculpe Ingeniero, no le entendí."

        HISTORIAL.append({"role": "assistant", "content": resp})
        return resp
    except requests.exceptions.ConnectionError:
        return "Error: Gemma 4 no está corriendo. Ejecute llama-server primero."
    except Exception as e:
        return f"Error: {e}"


def main():
    print("")
    print("╔═══════════════════════════════════╗")
    print("║  🤖 LOLA AI                       ║")
    print("║  Escriba su mensaje + Enter       ║")
    print("║  Escriba 'v' para usar micrófono  ║")
    print("║  Ctrl+C para salir                ║")
    print("╚═══════════════════════════════════╝")
    print("")

    saludo = "Buenas, Ingeniero. Lola lista."
    print(f"🤖 Lola: {saludo}")
    hablar(saludo)

    while True:
        try:
            texto = input("\n🎤 Usted: ").strip()

            if not texto:
                continue

            if texto.lower() in ("v", "voz"):
                print("  🎙️ Hable ahora...")
                try:
                    r = subprocess.run(["termux-speech-to-text"],
                                       capture_output=True, text=True, timeout=15)
                    texto = r.stdout.strip() if r.returncode == 0 else ""
                    if not texto:
                        print("  ❌ No escuché nada.")
                        continue
                    print(f"  🗣️ Escuché: {texto}")
                except:
                    print("  ❌ Error con micrófono.")
                    continue

            if texto.lower() in ("salir", "exit", "bye"):
                print("👋 Hasta luego, Ingeniero.")
                hablar("Hasta luego, Ingeniero.")
                break

            # Respuesta rápida
            r = rapida(texto)
            if r:
                print(f"⚡ Lola: {r}")
                hablar(r)
                continue

            # Gemma 4
            print("🧠 Pensando...", end="", flush=True)
            resp = pensar(texto)
            print(f"\r🤖 Lola: {resp}")
            hablar(resp)

        except KeyboardInterrupt:
            print("\n👋 Adiós, Ingeniero.")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")


if __name__ == "__main__":
    main()
