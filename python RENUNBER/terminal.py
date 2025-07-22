import os
import platform
import shlex
import subprocess
from datetime import datetime
import socket
import urllib.request
import json
import shutil
import time
from typing import Dict, List, Optional

# =========================
# Configuración inicial
# =========================
try:
    import readline  # Para autocompletado (Unix)
except ImportError:
    try:
        import pyreadline as readline  # Windows
    except ImportError:
        readline = None

# =========================
# Colores ANSI
# =========================
COLORES = {
    "verde": "\033[1;32m",
    "morado": "\033[95m",
    "rojo": "\033[91m",
    "azul": "\033[94m",
    "amarillo": "\033[93m",
    "cian": "\033[96m",
    "blanco": "\033[97m",
    "gris": "\033[90m",
    "reset": "\033[0m",
}

tema_actual = {
    "prompt": COLORES["morado"],
    "output": COLORES["azul"],
    "error": COLORES["rojo"],
    "exito": COLORES["verde"],
    "advertencia": COLORES["amarillo"],
}

# =========================
# Variables globales
# =========================
HISTORIAL_ACTIVO = True
HISTORIAL_ARCHIVO = "vsouver_historial.txt"
_historial_cache: List[str] = []
variables_entorno: Dict[str, str] = {}
plugins_cargados: Dict[str, callable] = {}

# =========================
# Logo
# =========================
logo = f"""{COLORES["verde"]}
░██████╗░█████╗░██╗░░░██╗██╗░░░██╗███████╗██████╗░
██╔════╝██╔══██╗██║░░░██║██║░░░██║██╔════╝██╔══██╗
╚█████╗░██║░░██║██║░░░██║╚██╗░██╔╝█████╗░░██████╔╝
░╚═══██╗██║░░██║██║░░░██║░╚████╔╝░██╔══╝░░██╔══██╗
██████╔╝╚█████╔╝╚██████╔╝░░╚██╔╝░░███████╗██║░░██║
╚═════╝░░╚════╝░░╚═════╝░░░░╚═╝░░░╚══════╝╚═╝░░╚═╝
{COLORES['gris']}Creado por: {COLORES['verde']}Morales
{COLORES['gris']}Instagram: {COLORES['cian']}https://www.instagram.com/m0rales24/{COLORES['reset']}\n
"""

# =========================
# Utilidades
# =========================
def limpiar():
    os.system("cls" if platform.system() == "Windows" else "clear")

def imprimir_error(msg: str):
    print(f"{tema_actual['error']}✖ {msg}{COLORES['reset']}")

def imprimir_exito(msg: str):
    print(f"{tema_actual['exito']}✔ {msg}{COLORES['reset']}")

def mostrar_hora():
    hora = datetime.now().strftime("%H:%M:%S")
    print(f"{COLORES['amarillo']}🕒 Hora actual: {hora}{COLORES['reset']}")

def mostrar_ayuda():
    ayuda = f"""
{COLORES["cian"]}Comandos principales VsoUver:
 vso-ayuda            → Mostrar esta ayuda
 vso-info             → Información del sistema
 vso-tema claro|oscuro→ Cambiar tema
 vso-limpiar          → Limpiar pantalla
 vso-hora             → Mostrar hora
 vso-historial        → Ver historial de comandos
 vso-python           → REPL de Python integrado
 vso-plugins          → Listar plugins cargados

{COLORES["verde"]}Comandos de red:
 vso-ip-publica       → Mostrar IP pública
 vso-ip-local         → Mostrar IPs locales
 vso-ip-dominio <dom> → Resolver IP de dominio
 ping <host>          → Hacer ping a un host
 escaneo-puertos <host> <rango> → Escanear puertos

{COLORES["amarillo"]}Comandos de archivos:
 cd <ruta>            → Cambiar directorio
 ls [ruta]            → Listar archivos
 pwd                  → Mostrar ruta actual
 mkdir <carpeta>      → Crear carpeta
 rm <archivo>         → Borrar archivo
 cp <origen> <dest>   → Copiar archivo
 mv <origen> <dest>   → Mover/renombrar
 cat <archivo>        → Mostrar contenido
 grep <patrón> <archivo> → Buscar en archivos
 find <nombre>        → Buscar archivos

{COLORES["morado"]}Variables y scripts:
 set <var>=<valor>    → Definir variable
 env                  → Mostrar variables
 script <archivo.vso> → Ejecutar script

{COLORES["blanco"]}Herramientas avanzadas:
 automatizar <archivo> → Ejecutar script de comandos
 analisis-seguridad <host> → Análisis básico de seguridad
 monitorizar          → Monitorización del sistema en tiempo real
 benchmark           → Pruebas de rendimiento del sistema

Usa 'salir' para cerrar la terminal.
{COLORES["reset"]}"""
    print(ayuda)

def mostrar_info():
    try:
        user = os.getlogin()
    except Exception:
        user = os.environ.get("USERNAME") or os.environ.get("USER") or "desconocido"
    print(f"""{COLORES["blanco"]}
Sistema operativo : {platform.system()}
Versión del sistema: {platform.version()}
Nombre del equipo  : {platform.node()}
Usuario actual     : {user}
Python versión     : {platform.python_version()}
Hora actual        : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Directorio actual  : {os.getcwd()}
{COLORES["reset"]}""")

# =========================
# Historial
# =========================
def cargar_historial():
    if not HISTORIAL_ACTIVO:
        return
    if os.path.exists(HISTORIAL_ARCHIVO):
        try:
            with open(HISTORIAL_ARCHIVO, "r", encoding="utf-8") as f:
                _historial_cache.extend([l.rstrip("\n") for l in f])
        except Exception as e:
            imprimir_error(f"No se pudo cargar historial: {e}")

def guardar_en_historial(comando: str):
    if not HISTORIAL_ACTIVO:
        return
    _historial_cache.append(comando)
    try:
        with open(HISTORIAL_ARCHIVO, "a", encoding="utf-8") as f:
            f.write(comando + "\n")
    except Exception as e:
        imprimir_error(f"No se pudo guardar historial: {e}")

def mostrar_historial():
    if not HISTORIAL_ACTIVO:
        imprimir_error("El historial no está activado (edita HISTORIAL_ACTIVO=True en el código).")
        return
    if not _historial_cache:
        print("Historial vacío.")
        return
    for i, cmd in enumerate(_historial_cache, 1):
        print(f"{i:>3}: {cmd}")

# =========================
# Comandos tipo shell internos (cross-platform)
# =========================
def cmd_cd(args):
    if not args:
        imprimir_error("Uso: cd <ruta>")
        return
    ruta = args[0]
    try:
        os.chdir(os.path.expanduser(ruta))
    except FileNotFoundError:
        imprimir_error(f"No existe: {ruta}")
    except NotADirectoryError:
        imprimir_error(f"No es un directorio: {ruta}")
    except PermissionError:
        imprimir_error(f"Sin permiso: {ruta}")
    except Exception as e:
        imprimir_error(f"Error al cambiar directorio: {e}")

def cmd_pwd(_args):
    print(os.getcwd())

def cmd_ls(args):
    ruta = args[0] if args else "."
    ruta = os.path.expanduser(ruta)
    try:
        items = os.listdir(ruta)
    except Exception as e:
        imprimir_error(f"No se puede listar {ruta}: {e}")
        return
    for nombre in sorted(items):
        full = os.path.join(ruta, nombre)
        if os.path.isdir(full):
            print(f"{COLORES['cian']}{nombre}/ {COLORES['reset']}")
        else:
            print(nombre)

def _safe_rm_file(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        imprimir_error(f"No existe: {path}")
    except IsADirectoryError:
        imprimir_error(f"Es directorio (usa rmdir o rm -r): {path}")
    except PermissionError:
        imprimir_error(f"Sin permiso: {path}")
    except Exception as e:
        imprimir_error(f"Error eliminando: {e}")

def _safe_rmdir(path):
    try:
        os.rmdir(path)
    except FileNotFoundError:
        imprimir_error(f"No existe: {path}")
    except OSError as e:
        imprimir_error(f"No se pudo borrar (¿no está vacío?): {path} ({e})")
    except Exception as e:
        imprimir_error(f"Error: {e}")

def _safe_rm_recursive(path):
    try:
        shutil.rmtree(path)
    except FileNotFoundError:
        imprimir_error(f"No existe: {path}")
    except Exception as e:
        imprimir_error(f"Error borrando recursivo: {e}")

def cmd_rm(args):
    if not args:
        imprimir_error("Uso: rm <archivo> | rm -r <ruta>")
        return
    if args[0] == "-r":
        if len(args) < 2:
            imprimir_error("Uso: rm -r <ruta>")
            return
        _safe_rm_recursive(os.path.expanduser(args[1]))
        return
    for p in args:
        _safe_rm_file(os.path.expanduser(p))

def cmd_mkdir(args):
    if not args:
        imprimir_error("Uso: mkdir <carpeta>")
        return
    for d in args:
        d = os.path.expanduser(d)
        try:
            os.makedirs(d, exist_ok=True)
        except Exception as e:
            imprimir_error(f"No se pudo crear {d}: {e}")

def cmd_cp(args):
    if len(args) < 2:
        imprimir_error("Uso: cp <origen> <dest>")
        return
    src, dst = args[0], args[1]
    try:
        shutil.copy2(os.path.expanduser(src), os.path.expanduser(dst))
    except Exception as e:
        imprimir_error(f"Error copiando: {e}")

def cmd_mv(args):
    if len(args) < 2:
        imprimir_error("Uso: mv <origen> <dest>")
        return
    src, dst = args[0], args[1]
    try:
        os.rename(os.path.expanduser(src), os.path.expanduser(dst))
    except Exception as e:
        imprimir_error(f"Error moviendo: {e}")

def cmd_cat(args):
    if not args:
        imprimir_error("Uso: cat <archivo>")
        return
    for archivo in args:
        archivo = os.path.expanduser(archivo)
        try:
            with open(archivo, "r", encoding="utf-8", errors="replace") as f:
                print(f.read(), end="")
        except Exception as e:
            imprimir_error(f"No se pudo leer {archivo}: {e}")

def cmd_touch(args):
    if not args:
        imprimir_error("Uso: touch <archivo>")
        return
    for archivo in args:
        archivo = os.path.expanduser(archivo)
        try:
            with open(archivo, "a", encoding="utf-8"):
                os.utime(archivo, None)
        except Exception as e:
            imprimir_error(f"No se pudo tocar {archivo}: {e}")

def cmd_type(args):
    cmd_cat(args)

def cmd_dir(args):
    cmd_ls(args)

def cmd_echo(args):
    print(" ".join(args))

def cmd_whoami(_args):
    try:
        print(os.getlogin())
    except Exception:
        print(os.environ.get("USERNAME") or os.environ.get("USER") or "desconocido")

def cmd_date(_args):
    print(datetime.now().strftime("%a %b %d %H:%M:%S %Y"))

def cmd_clear(_args):
    limpiar()

def cmd_head(args):
    if not args:
        imprimir_error("Uso: head <archivo>")
        return
    archivo = os.path.expanduser(args[0])
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            for _ in range(10):
                linea = f.readline()
                if not linea:
                    break
                print(linea, end="")
    except Exception as e:
        imprimir_error(f"No se pudo leer {archivo}: {e}")

def cmd_tail(args):
    if not args:
        imprimir_error("Uso: tail <archivo>")
        return
    archivo = os.path.expanduser(args[0])
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            lineas = f.readlines()[-10:]
            for l in lineas:
                print(l, end="")
    except Exception as e:
        imprimir_error(f"No se pudo leer {archivo}: {e}")

def cmd_gci(args):
    cmd_ls(args)

def cmd_gps(_args):
    try:
        cmd = "tasklist" if platform.system() == "Windows" else "ps aux"
        subprocess.run(cmd, shell=True)
    except Exception as e:
        imprimir_error(f"Error al listar procesos: {e}")

def cmd_hostname(_args):
    print(platform.node())

def cmd_ip_publica(_args):
    try:
        with urllib.request.urlopen('https://api.ipify.org') as response:
            ip = response.read().decode()
            print(f"{COLORES['verde']}IP pública: {ip}{COLORES['reset']}")
    except Exception as e:
        imprimir_error(f"No se pudo obtener IP pública: {e}")

def cmd_ip_local(_args):
    try:
        hostname = socket.gethostname()
        ips = socket.gethostbyname_ex(hostname)[2]
        ips_unicas = sorted(set(ips))
        print(f"{COLORES['verde']}IPs locales para {hostname}:{COLORES['reset']}")
        for ip in ips_unicas:
            print(f" - {ip}")
    except Exception as e:
        imprimir_error(f"No se pudo obtener IP local: {e}")

def cmd_ip_dominio(args):
    if not args:
        imprimir_error("Uso: vso-ip-dominio <dominio>")
        return
    dominio = args[0]
    try:
        ip = socket.gethostbyname(dominio)
        print(f"{COLORES['verde']}IP de {dominio}: {ip}{COLORES['reset']}")
    except Exception as e:
        imprimir_error(f"No se pudo resolver IP de {dominio}: {e}")

def cambiar_tema(modo: str):
    if modo == "claro":
        tema_actual["prompt"] = COLORES["cian"]
        tema_actual["output"] = COLORES["azul"]
        print(f"{COLORES['verde']}✔ Tema claro activado.{COLORES['reset']}")
    elif modo == "oscuro":
        tema_actual["prompt"] = COLORES["morado"]
        tema_actual["output"] = COLORES["azul"]
        print(f"{COLORES['verde']}✔ Tema oscuro activado.{COLORES['reset']}")
    else:
        imprimir_error("Modo no válido (usa claro u oscuro)")

# =========================
# Nuevas funcionalidades añadidas
# =========================
def cmd_automatizar(args):
    """Ejecuta una serie de comandos desde un archivo de automatización"""
    if not args:
        imprimir_error("Uso: automatizar <archivo.auto>")
        return
    try:
        with open(args[0], 'r') as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith('#'):
                    print(f"{COLORES['morado']}$ {linea}{COLORES['reset']}")
                    ejecutar_comando_interno(linea) or ejecutar_en_shell(linea)
    except Exception as e:
        imprimir_error(f"Error en automatización: {e}")

def cmd_analisis_seguridad(args):
    """Analiza aspectos básicos de seguridad de un sistema"""
    if not args:
        imprimir_error("Uso: analisis-seguridad <dominio/IP>")
        return
    
    objetivo = args[0]
    print(f"{COLORES['amarillo']}🔍 Analizando seguridad básica de {objetivo}...{COLORES['reset']}")
    
    # Comandos básicos de análisis (éticos)
    print(f"\n{COLORES['cian']}=== Información básica ==={COLORES['reset']}")
    ejecutar_en_shell(f"ping -c 4 {objetivo}" if platform.system() != "Windows" else f"ping -n 4 {objetivo}")
    
    print(f"\n{COLORES['cian']}=== Encabezados HTTP ==={COLORES['reset']}")
    ejecutar_en_shell(f"curl -I http://{objetivo}" if platform.system() != "Windows" else f"curl -I http://{objetivo}")
    
    print(f"\n{COLORES['cian']}=== Puertos comunes ==={COLORES['reset']}")
    ejecutar_en_shell(f"nmap -T4 -F {objetivo}")

def cmd_monitorizar(args):
    """Monitoriza recursos del sistema en tiempo real"""
    try:
        while True:
            limpiar()
            print(f"{COLORES['verde']}=== Monitor del Sistema (Ctrl+C para salir) ==={COLORES['reset']}")
            
            if platform.system() == "Windows":
                ejecutar_en_shell("tasklist")
                ejecutar_en_shell("systeminfo | findstr /B /C:'OS Name' /C:'OS Version' /C:'System Type' /C:'Total Physical Memory'")
            else:
                ejecutar_en_shell("top -n 1 -b | head -n 5")
                ejecutar_en_shell("df -h | grep -v loop")
                ejecutar_en_shell("free -h")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n{COLORES['verde']}Monitorización detenida.{COLORES['reset']}")

def cmd_benchmark(args):
    """Ejecuta pruebas de rendimiento del sistema"""
    print(f"{COLORES['amarillo']}🚀 Ejecutando benchmark del sistema...{COLORES['reset']}")
    
    # Prueba de CPU
    start = time.time()
    [x**2 for x in range(1000000)]
    cpu_time = time.time() - start
    
    # Prueba de disco
    start = time.time()
    with open("temp_benchmark.txt", "w") as f:
        for i in range(10000):
            f.write(f"Linea de prueba {i}\n")
    write_time = time.time() - start
    
    os.remove("temp_benchmark.txt")
    
    print(f"\n{COLORES['cian']}Resultados del Benchmark:{COLORES['reset']}")
    print(f"CPU: {cpu_time:.4f} segundos (cálculo intensivo)")
    print(f"Disco: {write_time:.4f} segundos (escritura de 10k líneas)")

def cmd_python_repl(_args):
    print(f"{COLORES['verde']}🔮 Modo Python interactivo (escribe 'salir' para volver){COLORES['reset']}")
    while True:
        try:
            codigo = input(f"{COLORES['amarillo']}>>> {COLORES['reset']}").strip()
            if codigo.lower() in ["salir", "exit"]:
                break
            
            try:
                resultado = eval(codigo)
                if resultado is not None:
                    print(f"{COLORES['azul']}{resultado}{COLORES['reset']}")
            except SyntaxError:
                exec(codigo)
        except Exception as e:
            imprimir_error(f"Error en Python: {e}")

def cmd_ping(args):
    if not args:
        imprimir_error("Uso: ping <host>")
        return
    host = args[0]
    comando = f"ping -c 4 {host}" if platform.system() != "Windows" else f"ping -n 4 {host}"
    ejecutar_en_shell(comando)

def cmd_escaneo_puertos(args):
    if len(args) < 2:
        imprimir_error("Uso: escaneo-puertos <host> <rango> (ej: 1-100)")
        return
    
    host, rango = args[0], args[1]
    try:
        inicio, fin = map(int, rango.split('-'))
        print(f"{COLORES['verde']}Escaneando {host} (puertos {inicio}-{fin})...{COLORES['reset']}")
        
        for puerto in range(inicio, fin + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)
                resultado = sock.connect_ex((host, puerto))
                if resultado == 0:
                    print(f"{COLORES['cian']}✔ Puerto {puerto} abierto{COLORES['reset']}")
    except Exception as e:
        imprimir_error(f"Error en escaneo: {e}")

def cmd_grep(args):
    if len(args) < 2:
        imprimir_error("Uso: grep <patrón> <archivo>")
        return
    
    patron, archivo = args[0], args[1]
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            for i, linea in enumerate(f, 1):
                if patron.lower() in linea.lower():
                    print(f"{COLORES['verde']}{i}:{COLORES['reset']} {linea.rstrip()}")
    except Exception as e:
        imprimir_error(f"Error en grep: {e}")

def cmd_find(args):
    if not args:
        imprimir_error("Uso: find <nombre>")
        return
    
    nombre = args[0]
    for root, dirs, files in os.walk("."):
        for f in files:
            if nombre.lower() in f.lower():
                print(f"{COLORES['cian']}{os.path.join(root, f)}{COLORES['reset']}")

def cmd_set(args):
    if not args or "=" not in args[0]:
        imprimir_error("Uso: set <NOMBRE>=<valor>")
        return
    
    nombre, valor = args[0].split("=", 1)
    variables_entorno[nombre] = valor
    imprimir_exito(f"Variable definida: {nombre}={valor}")

def cmd_env(_args):
    for k, v in variables_entorno.items():
        print(f"{COLORES['cian']}{k}={v}{COLORES['reset']}")

def cmd_script(args):
    if not args:
        imprimir_error("Uso: script <archivo.vso>")
        return
    
    archivo = args[0]
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if linea and not linea.startswith("#"):
                    print(f"{COLORES['morado']}$ {linea}{COLORES['reset']}")
                    ejecutar_comando_interno(linea) or ejecutar_en_shell(linea)
    except Exception as e:
        imprimir_error(f"Error ejecutando script: {e}")

def cmd_plugins(_args):
    if not plugins_cargados:
        print("No hay plugins cargados.")
        return
    
    print(f"{COLORES['verde']}Plugins cargados:{COLORES['reset']}")
    for nombre, func in plugins_cargados.items():
        print(f" - {nombre}: {func.__doc__ or 'Sin descripción'}")

def setup_autocompletado():
    if readline:
        def completar(texto, estado):
            comandos = list(tabla_comandos.keys()) + ["salir", "exit", "vso-ayuda"]
            opciones = [cmd for cmd in comandos if cmd.startswith(texto)]
            return opciones[estado] if estado < len(opciones) else None
        
        readline.set_completer(completar)
        readline.parse_and_bind("tab: complete")
        readline.parse_and_bind('"\e[A": history-search-backward')
        readline.parse_and_bind('"\e[B": history-search-forward')

def cargar_plugins():
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    if not os.path.exists(plugins_dir):
        os.makedirs(plugins_dir, exist_ok=True)
        return
    
    for archivo in os.listdir(plugins_dir):
        if archivo.endswith(".py") and archivo != "__init__.py":
            nombre = archivo[:-3]
            try:
                modulo = __import__(f"plugins.{nombre}", fromlist=["*"])
                if hasattr(modulo, "registrar_comandos"):
                    plugins_cargados.update(modulo.registrar_comandos())
                    imprimir_exito(f"Plugin cargado: {nombre}")
            except Exception as e:
                imprimir_error(f"Error cargando plugin {nombre}: {e}")

def ejecutar_en_background(comando: str):
    try:
        pid = os.fork()
        if pid == 0:
            os.system(comando)
            os._exit(0)
    except Exception as e:
        imprimir_error(f"No se pudo ejecutar en background: {e}")

# =========================
# Tabla de comandos completa
# =========================
tabla_comandos = {
    # Comandos originales
    "cd": cmd_cd,
    "pwd": cmd_pwd,
    "ls": cmd_ls,
    "dir": cmd_dir,
    "mkdir": cmd_mkdir,
    "rm": cmd_rm,
    "rmdir": _safe_rmdir,
    "cp": cmd_cp,
    "mv": cmd_mv,
    "cat": cmd_cat,
    "type": cmd_type,
    "touch": cmd_touch,
    "echo": cmd_echo,
    "whoami": cmd_whoami,
    "date": cmd_date,
    "clear": cmd_clear,
    "cls": cmd_clear,
    "head": cmd_head,
    "tail": cmd_tail,
    "gci": cmd_gci,
    "gps": cmd_gps,
    "hostname": cmd_hostname,
    "vso-ip-publica": cmd_ip_publica,
    "vso-ip-local": cmd_ip_local,
    "vso-ip-dominio": cmd_ip_dominio,
    
    # Nuevos comandos
    "vso-python": cmd_python_repl,
    "ping": cmd_ping,
    "escaneo-puertos": cmd_escaneo_puertos,
    "grep": cmd_grep,
    "find": cmd_find,
    "set": cmd_set,
    "env": cmd_env,
    "script": cmd_script,
    "vso-plugins": cmd_plugins,
    
    # Comandos de automatización y análisis
    "automatizar": cmd_automatizar,
    "analisis-seguridad": cmd_analisis_seguridad,
    "monitorizar": cmd_monitorizar,
    "benchmark": cmd_benchmark,
}

# =========================
# Despachador de comandos
# =========================
def ejecutar_comando_interno(comando: str) -> bool:
    if not comando:
        return True

    if comando in ["salir", "exit", "quit"]:
        raise SystemExit

    if comando == "vso-ayuda":
        mostrar_ayuda()
        return True

    if comando == "vso-info":
        mostrar_info()
        return True

    if comando == "vso-limpiar":
        limpiar()
        return True

    if comando == "vso-hora":
        mostrar_hora()
        return True

    if comando == "vso-historial":
        mostrar_historial()
        return True

    if comando.startswith("vso-tema"):
        _, *args = comando.split()
        if args:
            cambiar_tema(args[0])
        else:
            imprimir_error("Uso: vso-tema claro|oscuro")
        return True

    partes = shlex.split(comando)
    if not partes:
        return True
    cmd, *args = partes

    # Buscar en comandos principales
    if cmd in tabla_comandos:
        tabla_comandos[cmd](args)
        return True
    
    # Buscar en plugins
    if cmd in plugins_cargados:
        plugins_cargados[cmd](args)
        return True

    return False

# =========================
# Ejecución en shell real
# =========================
def ejecutar_en_shell(comando: str):
    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True
        )
        if resultado.stdout:
            print(f"{tema_actual['output']}{resultado.stdout}{COLORES['reset']}", end="")
        if resultado.stderr:
            imprimir_error(resultado.stderr.rstrip("\n"))
    except Exception as e:
        imprimir_error(f"Error ejecutando comando externo: {e}")

# =========================
# Loop principal mejorado
# =========================
def iniciar_terminal():
    cargar_historial()
    cargar_plugins()
    setup_autocompletado()
    
    limpiar()
    print(logo)
    print(f"{COLORES['amarillo']}🌟 VsoUver Terminal v2.0 {COLORES['reset']}")
    print(f"{COLORES['gris']}Escribe 'vso-ayuda' para ver comandos.{COLORES['reset']}\n")

    while True:
        try:
            # Prompt inteligente con información contextual
            cwd = os.getcwd()
            user = os.getlogin() if platform.system() != "Windows" else os.environ.get("USERNAME", "?")
            host = platform.node()
            prompt = f"{tema_actual['prompt']}{user}@{host}:{cwd} ⛮ $ {COLORES['reset']}"
            
            comando = input(prompt).strip()
            if not comando:
                continue
                
            guardar_en_historial(comando)
            
            # Procesamiento especial para comandos en background
            if comando.endswith("&"):
                ejecutar_en_background(comando[:-1])
                continue
                
            # Ejecución normal
            manejado = ejecutar_comando_interno(comando)
            if not manejado:
                ejecutar_en_shell(comando)

        except SystemExit:
            print(f"{COLORES['rojo']}⛔ Cerrando terminal...{COLORES['reset']}")
            break
        except KeyboardInterrupt:
            print(f"\n{COLORES['rojo']}⛔ Usa 'salir' para cerrar la terminal.{COLORES['reset']}")
        except EOFError:
            print(f"\n{COLORES['rojo']}⛔ Entrada finalizada. Cerrando...{COLORES['reset']}")
            break
        except Exception as e:
            imprimir_error(f"Error inesperado: {e}")

# =========================
# Main
# =========================
if __name__ == "__main__":
    iniciar_terminal()