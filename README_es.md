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
  <img src="https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macOS-8b97b8?style=flat" alt="Platform">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
</p>

<p align="center">
  <a href="#-inicio-rápido">Inicio rápido</a> &nbsp;&middot;&nbsp;
  <a href="#-qué-trae">Qué trae</a> &nbsp;&middot;&nbsp;
  <a href="#-capturas">Capturas</a> &nbsp;&middot;&nbsp;
  <a href="#-panel">Panel</a> &nbsp;&middot;&nbsp;
  <a href="#-proveedores">Proveedores</a> &nbsp;&middot;&nbsp;
  <a href="#-本地模型">本地模型</a> &nbsp;&middot;&nbsp;
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

**En Windows** (no hace falta WSL): doble clic en `run.bat`. Busca Python 3.9+, arranca el backend y abre la ventana
de la app con Edge o Chrome en *modo aplicación* (sin barra de navegador). `install-windows.bat` crea el acceso directo
en el escritorio y en el menú Inicio, y `stop.bat` detiene el backend. También puedes seguir usando la web en
<http://127.0.0.1:8765> desde cualquier navegador.

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
- **Interfaz en 7 idiomas** (inglés, español, chino, japonés, coreano, árabe e indonesio), se cambia desde la barra superior; el árabe pone la interfaz de derecha a izquierda.
- **Modelos locales sin clave de API**: NEXUS instala Ollama o LM Studio, descarga el modelo que elijas (29 modelos pequeños, sin censura incluidos) y lo deja listo para chatear.
- **Adjuntos que se quedan** — envía imágenes o documentos y se guardan con la conversación (miniatura o ficha del archivo, pulsa para abrir o descargar); siguen ahí al recargar y se reenvían al regenerar.

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

## 🧩 Modelos locales (sin clave de API)

¿Sin clave de API? NEXUS puede ejecutar un **modelo local** en tu propio ordenador: sin cuenta, sin coste y sin que
nada salga del equipo una vez descargado. Se encarga de todo: detecta e instala **[Ollama](https://ollama.com)**
(o **[LM Studio](https://lmstudio.ai)**), descarga el modelo con barra de progreso y deja el proveedor configurado
para que puedas hablar con él en el momento.

Abre 🧩 en la barra superior, o *Ajustes → Modelos locales*.

**Dos caminos:**

- **Ollama** (recomendado): NEXUS lo instala (Linux: script oficial con tu contraseña; **Windows**: descarga y ejecuta
  `OllamaSetup.exe`; macOS: la descarga oficial) y luego trae el modelo que elijas.
- **LM Studio**: NEXUS lo detecta, arranca su servidor local y puede descargar modelos con el comando `lms`. Cada ficha
  te dice el repositorio de Hugging Face que usa.

**El catálogo** (29 modelos, todos de 3 GB o menos, con tamaños comprobados contra el registro real de Ollama y los
ficheros de Hugging Face) está pensado para equipos ligeros y con acento en los modelos **sin censura** (Dolphin y
los *abliterated*), con una nota honesta en cada ficha de lo que sabe y lo que no:

| Modelo | Tamaño | Sin censura | Herramientas |
|---|---|---|---|
| Qwen2.5 0.5B abliterated | 379 MB | sí | no |
| TinyDolphin 1.1B (Q4/Q6) | 637 MB / 862 MB | sí | no |
| Dolphin 3.0 Llama 3.2 1B (Q4) ᴴᶠ | 770 MB | sí | no |
| Llama 3.2 1B abliterated | 911 MB | sí | no |
| Qwen2.5 1.5B abliterated | 940 MB | sí | no |
| Qwen3 1.7B abliterated | 1,06 GB | sí | no |
| Qwen2.5 Coder 1.5B abliterated | 1,07 GB | sí | no |
| Dolphin Phi 2.7B (Q2/Q4) | 1,12 / 1,53 GB | sí | no |
| StableLM Zephyr 3B | 1,53 GB | permisivo | no |
| Dolphin 3.0 Llama 3.2 3B (Q3) ᴴᶠ | 1,61 GB | sí | no |
| Qwen2.5 / Qwen2.5-Coder 3B abliterated | 1,84 GB | sí | no |
| Dolphin 3.0 Qwen2.5 3B (Q4/Q5) ᴴᶠ | 1,84 / 2,12 GB | sí | no |
| Dolphin 3.0 Llama 3.2 3B (Q4/Q5) ᴴᶠ | 1,93 / 2,22 GB | sí | no |
| Hermes 3 Llama 3.2 3B ᴴᶠ · Ollama | 1,93 GB | permisivo | **sí** |
| Llama 3.2 3B abliterated | 2,14 GB | sí | no |
| Qwen3 4B · Qwen3 1.7B | 2,38 / 1,30 GB | no | **sí** |
| Spark X2.5 4B heretic | 2,48 GB | sí | sí |
| MiniCPM5 2B heretic | 2,56 GB | sí | no |
| Wizard Vicuna 7B sin censura (Q2) | 2,69 GB | sí | no |
| Dolphin Mistral 7B (Q2) · OpenHermes 2.5 7B (Q2) | 2,94 GB | sí / permisivo | no |

ᴴᶠ = no está en la biblioteca de Ollama: se descarga desde Hugging Face (`ollama pull hf.co/usuario/repo:Q4_K_M`), que
es lo que hace el botón Descargar por ti.


**Modelos locales en modo agente.** NEXUS prepara Hermes la primera vez que usas un modelo local en modo
agente: registra el endpoint del proveedor (`hermes config set providers.ollama.base_url …`), le pide a Ollama
una ventana de 64k (`model.ollama_num_ctx`, el mínimo de Hermes) y desactiva el streaming para ese proveedor,
porque Hermes se queda colgado con Ollama al transmitir llamadas a herramientas. Y luego todo depende del
modelo: **el modo agente necesita un modelo que sepa llamar a funciones**. Comprobado contra el propio Ollama:
`qwen3:1.7b` (1,3 GB), `qwen3:4b` (2,4 GB) y `hermes3:3b` (1,9 GB) sí; **los traídos de Hugging Face
(`hf.co/…`) no** (Ollama responde *HTTP 400: does not support tools*), así que esos solo para chat. Y corre en
tu CPU: un turno del agente en local tarda.
**Solo para el modo agente**: un modelo local necesita entender la *llamada a funciones* para tocar archivos o ejecutar
órdenes, y muy pocos modelos pequeños lo hacen. Las fichas marcadas con *con herramientas* (**Hermes 3 3B**,
**Qwen3 1.7B/4B**, **Spark X2.5 4B**) son las que merece la pena probar; el resto son para conversar, redactar, resumir
y traducir. Además corre en tu CPU, así que es lento: para trabajo de agente serio, mejor un proveedor por API.

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
      prompts.json         biblioteca de prompts de ejemplo (25)
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
- Requiere Python 3.9+ y un navegador. Funciona en **Windows, Linux y macOS**: en Windows, doble clic en `run.bat`
    (abre Edge o Chrome en modo aplicación); en Linux o macOS, `run.sh`.
- La interfaz viene en **7 idiomas** (inglés, español, chino, japonés, coreano, árabe e indonesio); se cambia desde la barra superior o en Ajustes. El árabe además pone la interfaz de derecha a izquierda.

## 📄 Licencia

MIT — ver [LICENSE](LICENSE).
