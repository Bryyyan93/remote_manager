# Gestor Remoto de Cabeceras

## 📚 Índice

- [Descripción](#descripción)
- [🚀 Características principales](#-características-principales)
- [🧱 Requisitos](#-requisitos)
  - [Instalación local](#instalación-local)
- [📁 Estructura del proyecto](#estrucura-del-proyecto)
- [🔐 Seguridad](#-seguridad)

## Descripción
**remote_manager** es una aplicación desarrollada en **Python** que permite la gestión remota de cabeceras. 
La aplicación facilita la actualización simultánea del software en múltiples cabeceras, el envío de comandos y la obtención de información desde la API de **Onomondo**.

## 🚀 Características principales
- **Actualización remota**: Permite actualizar el software de todas las cabeceras sin necesidad de acceder a cada una individualmente.
- **Envío de comandos**: Permite ejecutar comandos de **Bash** en varias cabeceras simultaneamente.
- **Integración con Onomondo**: Obtiene información en tiempo real desde la API de Onomondo para mejorar la gestión y monitoreo de las cabeceras.

## 🧱 Requisitos
- **Python 3.8+**
- **Librerías:**
   - `paramiko`
   - `cryptography`
   - `requests`
   - `tkinter` (viene por defecto en la mayoría de instalaciones de Python)
   - `tqdm`
   Dependencias necesarias (ver `requirements.txt`)

### Instalación local
Para poder trabajar sin problemas se deberá crear un entorno virtual con las dependencias necesarias de la siguiente manera:
1. Clona este repositorio:
   ```bash
   git clone remote_manager
   cd remote_manager
   ```
2. Crea un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Estrucura del proyecto
La estrucrura de los scripts del proyecto, es la siguiente
```
📁 ssh/
├── comandos_ssh.py        # Funciones SSH: conexión, envío de comandos, subida de archivos
├── update_devices.py      # Lógica para actualizar dispositivos CA/LX e IMX
├── updateHE.php            # Script remoto que se ejecuta en los dispositivos
├── utils.py               # Herramientas comunes: logging, checksum, autenticación SSH
├── api_petitions.py       # Funciones para obtener datos desde la API de Onomondo
📁 gui/
├── gui_main.py            # Pantalla principal de la interfaz
├── gui_api.py             # Pantalla para ver datos de consumo
├── gui_update.py          # Pantalla para actualizar dispositivos
├── gui_upload.py          # Pantalla para subir archivos o ficheros a los dispositivos
├── gui_commands.py        # Pantalla emergente para selección de IPs o tags
📁 secrets/
└── apisecret_admin.key    # Clave para desencriptar el token de autenticación API
```
