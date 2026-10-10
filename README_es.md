<p align="center">
  <a href="README.md">English</a> | <a href="README_zh.md">中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_ko.md">한국어</a> | <a href="README_ar.md">العربية</a> | <b>Español</b> | <a href="README_id.md">Bahasa Indonesia</a>
</p>

<p align="center">
  <img src="app/assets/icon.svg" width="120" alt="NEXUS logo"/>
</p>

<h1 align="center">NEXUS</h1>

<p align="center">
  Consola de chat de IA de escritorio, autoalojada. <b>Sin dependencias</b>, cualquier proveedor compatible con OpenAI y todo se queda en tu equipo.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/dependencies-none-3fb950?style=flat" alt="No dependencies">
  <img src="https://img.shields.io/badge/providers-any%20OpenAI--compatible-7a8dff?style=flat" alt="OpenAI compatible">
  <img src="https://img.shields.io/badge/platform-linux%20%7C%20macOS%20%7C%20WSL-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-inicio-rápido">Inicio rápido</a> &nbsp;&middot;&nbsp;
  <a href="#-qué-trae">Qué trae</a> &nbsp;&middot;&nbsp;
  <a href="#-capturas">Capturas</a> &nbsp;&middot;&nbsp;
  <a href="#-panel">Panel</a> &nbsp;&middot;&nbsp;
  <a href="#-proveedores">Proveedores</a> &nbsp;&middot;&nbsp;
  <a href="#-modo-agente">Modo agente</a> &nbsp;&middot;&nbsp;
  <a href="#-red-local">Red local</a> &nbsp;&middot;&nbsp;
  <a href="#-atajos">Atajos</a> &nbsp;&middot;&nbsp;
  <a href="#-estructura">Estructura</a>
</p>

---

NEXUS es una consola de chat que ejecutas tú: varios chats, varios proveedores, historial persistente, streaming,
adjuntos de archivos e imágenes, un panel lateral de previsualización de código estilo *artifacts* y un panel de control
con tu gasto y uso reales.

Funciona con **cualquier servicio compatible con la API de OpenAI** (OpenAI, OpenRouter, Groq, DeepSeek, Mistral, xAI,
Gemini, Ollama y LM Studio locales…). Eliges el proveedor y pegas la clave dentro de la propia app: no hay ficheros que editar.

Nada sale de tu equipo: el backend escucha en `127.0.0.1` y la única conexión a internet es la petición al proveedor
que tú elijas.

## 🚀 Inicio rápido

```bash
git clone https://github.com/euphoriabot7/nexus.git
cd nexus
python3 server.py
```

Abre <http://127.0.0.1:8765> y el asistente de primera vez te pide proveedor y clave. Nada más: **no hay dependencias que
instalar** (solo Python 3.9+, todo es biblioteca estándar).

¿Prefieres ventana propia (sin barra de navegador) y entrada en el menú?

```bash
bash run.sh              # arranca el backend y abre una ventana chromium en modo --app
bash install-desktop.sh  # crea el acceso directo en el menú y el escritorio
bash stop.sh             # detiene el backend
```

## ⚡ Qué trae

- Varios chats: buscar, fijar, renombrar, duplicar, vaciar, borrar y exportar.
- Modelo por chat, favoritos ★ y búsqueda en la lista de modelos del proveedor.
- Historial persistente en SQLite; nada se pierde al cerrar.
- Streaming token a token, métricas (tokens, latencia), parar y regenerar.
- **Editar y reenviar** cualquiera de tus mensajes.
- **Adjuntos**: arrastra, pega o usa el botón 📎 (texto e imágenes).
- **Previsualización de código**: si la respuesta trae HTML/CSS/JS, un panel lateral muestra el resultado **mientras se
  escribe**, o una tarjeta “Ver resultado” bajo el mensaje. Los archivos que escribe el agente aparecen igual. Se puede desactivar.
- **Búsqueda global** en todos los mensajes, con resaltado y salto al mensaje.
- **Plantillas de prompt**, **paleta de comandos** (Ctrl+P), dictado por voz y lectura en alto.
- Estadísticas por chat, notificación y sonido al terminar, 6 acentos de color e import/export JSON.

## 🖼 Capturas

<p align="center">
  <img src="assets/shots/01-chat.png" width="820" alt="Chat con el panel de previsualización en vivo a la derecha">
  <br><sub>Chat con el panel de previsualización en vivo a la derecha</sub>
</p>
<p align="center">
  <img src="assets/shots/02-asistente.png" width="820" alt="Asistente de primera vez: elegir proveedor, pegar la clave y probarla">
  <br><sub>Asistente de primera vez: elegir proveedor, pegar la clave y probarla</sub>
</p>
<p align="center">
  <img src="assets/shots/03-panel.png" width="820" alt="Panel de control: uso, gasto, actividad diaria y tabla por modelo">
  <br><sub>Panel de control: uso, gasto, actividad diaria y tabla por modelo</sub>
</p>
<p align="center">
  <img src="assets/shots/04-movil.png" width="820" alt="Vista móvil, la misma app por tu red local">
  <br><sub>Vista móvil, la misma app por tu red local</sub>
</p>

## 📊 Panel de control

Botón **Panel** (abajo a la izquierda) o **Ctrl+D**. Cinco pestañas:

**Resumen** — tokens de entrada/salida, llamadas, coste estimado, uso de herramientas, gráfica de actividad diaria,
  tabla por modelo y mapa de calor por hora y día. Rangos de 7 / 30 / 90 días / 1 año y **exportar CSV**.
**Tareas** — encarga un trabajo al agente en segundo plano (título, encargo, carpeta, herramientas, modelo) y sigue su
  estado, salida y tokens en vivo. Requiere el modo agente.
**Proyecto** — explorador de archivos con **previsualización**: los `.html` se renderizan en vivo (con sus CSS/JS
  relativos), las imágenes se ven y el código como texto.
**Registro** — historial de actividad (chats creados, turnos de chat/agente, tareas, sesiones de app) con filtro por tipo.
**Red local** — dirección para entrar desde el móvil u otro equipo y el token.

## 🔑 Tu proveedor y tu clave

En la primera ejecución, o desde **Ajustes → Proveedores y claves**, eliges el proveedor, pegas la clave y pulsas
**Probar conexión**. La app pide al proveedor su lista real de modelos y hace una llamada mínima para comprobar que funciona.

La configuración se guarda en tu equipo, legible solo por ti:

```
~/.config/nexus/config.json      (0600)
```

```json
{ "default": { "provider": "openai", "model": "gpt-4o-mini" },
  "providers": { "openai": { "base_url": "https://api.openai.com/v1", "api_key": "sk-..." } } }
```

También valen las variables de entorno habituales (`OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`,
`DEEPSEEK_API_KEY`…). El catálogo de ejemplos está en `providers.json`; puedes añadir cualquier otro servicio con su URL
base (LiteLLM, vLLM, una pasarela propia, `http://127.0.0.1:11434/v1` para Ollama…).

## 🤖 Modo agente (opcional)

En **modo agente** NEXUS ejecuta [Hermes](https://hermes-agent.nousresearch.com) con herramientas reales: lee y escribe
archivos, ejecuta comandos y navega. Si no lo tienes instalado, la app te ofrece instalarlo con un botón del asistente
(`Ajustes → Proveedores y claves → Modo agente`). Sin Hermes, NEXUS funciona igual: solo se oculta el botón de agente.

Cambia de modo con la píldora **Chat / Agente** de la barra superior. El modo chat es la respuesta directa del modelo;
los adjuntos (archivos de texto e imágenes) se envían al modelo, y las imágenes necesitan un modelo con visión.

## 📱 Red local (móvil, tablet, otro equipo)

El servidor escucha en toda la red (`0.0.0.0`). Desde fuera de este equipo hace falta el **token** que verás en
Panel → Red local:

```
http://TU_IP:8765/login?token=TU_TOKEN
```

Eso guarda una cookie y no vuelve a pedirlo. Sin token, cualquier consulta externa responde **401**. Para desactivar el
acceso por red: `NEXUS_LAN=0 python3 server.py`. En Linux con ufw, `sudo bash lan-allow.sh` abre el puerto para tu subred.

En el móvil la app cambia sola a disposición móvil: historial en cajón, controles más grandes, hojas inferiores y área
segura. Consejo: en Chrome, *⋮ → Añadir a pantalla de inicio* para tenerla a pantalla completa.

## ⌨ Atajos

```text
    Ctrl+N     nuevo chat             Ctrl+P    paleta de comandos
    Ctrl+K     cambiar modelo         Ctrl+F    buscar en chats y mensajes
    Ctrl+D     panel de control       Ctrl+B    mostrar/ocultar historial
    Alt+↑ / ↓  chat anterior / siguiente
    Alt+1…9    saltar al chat nº
    Enter      enviar (Shift+Enter = salto de línea)
    ?          ayuda de atajos        Esc       cerrar ventanas, parar lectura
```

## 🗂 Estructura

```text
    nexus/
      server.py            backend (solo biblioteca estándar de Python)
      providers.json       catálogo de proveedores de ejemplo
      app/                 interfaz (HTML + CSS + JS, sin dependencias)
      assets/shots/        capturas usadas en este README
      run.sh / stop.sh     arranque y parada
      install-desktop.sh   accesos directos del menú y el escritorio
      lan-allow.sh         abre el puerto en ufw (opcional)

    ~/.config/nexus/config.json        proveedores, claves y modelo por defecto
    ~/.config/nexus/models_cache.json  listas de modelos obtenidas del proveedor
    ~/.local/share/nexus/nexus.db      chats, mensajes y plantillas (SQLite)
    ~/.local/share/nexus/server.log    registro del backend

Variables: `NEXUS_PORT` (8765), `NEXUS_DATA`, `NEXUS_CONFIG_DIR`, `NEXUS_LAN=0`.
```

## 📝 Notas

- Las claves **no** están en el repositorio: viven en tu equipo (`~/.config/nexus/config.json`, permisos 0600) o en variables de entorno.
- El modo agente ejecuta comandos en la carpeta de trabajo del chat: es tu propio equipo, úsalo con cuidado.
- Requiere Python 3.9+ y un navegador. Probado en Linux (Mint/Ubuntu); en macOS y Windows/WSL funciona igual
    (ahí usa `python3 server.py` y abre el navegador a mano).
- La interfaz está en español; la traducción de la app a más idiomas está en la lista de pendientes.

## 📄 Licencia

MIT — ver [LICENSE](LICENSE).
