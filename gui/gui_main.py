import tkinter as tk
from tkinter import ttk
from . import gui_commands as commands, gui_update as update, gui_api as api, gui_upload as upload


# --- Variables Globales ---
global ip_seleccionadas  # ips que se seleccionan para despues mandar un comando
global ip_a_utilizar    # Para la pantalla de tags y comandos
ip_a_utilizar = None
ip_seleccionadas = None
# --- Fin Variables Globales ---


def estilo():
    style = ttk.Style()
    style.theme_use("clam")  # Base moderna

    # Fondo oscuro para frames, labels, etc.
    style.configure(".", background="#2b2b2b", foreground="#f0f0f0", font=("Helvetica", 10))

    # Botones azulados
    style.configure("Rounded.TButton",
                    background="#1e81b0",       # Azul
                    foreground="white",         # Texto blanco
                    borderwidth=1,
                    focusthickness=3,
                    focuscolor='none',
                    padding=10)

    style.map("Rounded.TButton",
              background=[('active', '#16658a')],  # Azul más oscuro al pasar el mouse
              foreground=[('disabled', '#a0a0a0')])


def mostrar_pantalla(frame):
    frame.tkraise()


# --- Interfaz Gráfica ---
ventana = tk.Tk()
ventana.title("Remote Manager")
ventana.geometry("700x600")

# Contenedor que aloja todas las pantallas (frames)

estilo()
contenedor = ttk.Frame(ventana)
contenedor.pack(fill="both", expand=True)

# Crear los distintos frames/pantallas de la aplicación
pantalla_inicio = ttk.Frame(contenedor)  # Menú principal
pantalla_datos = api.pantalla_api(contenedor, pantalla_inicio)  # Consulta de datos (desde archivo api)
pantalla_update = update.pantalla_update(contenedor, pantalla_inicio)  # Actualización de cabeceras
pantalla_commands = commands.pantalla_commands(contenedor, pantalla_inicio)  # Envío de comandos por tag
pantalla_upload = upload.pantalla_upload(contenedor, pantalla_inicio)  # Subir ficheros

# Colocar todas las pantallas en la misma posición. Se usará tkraise() para mostrar una a la vez
for frame in (pantalla_inicio, pantalla_datos, pantalla_update, pantalla_upload, pantalla_commands):
    frame.grid(row=0, column=0, sticky='nsew')

# --- Pantalla de inicio ---
pantalla_inicio.columnconfigure(0, weight=1)
# Frame interno para centrar botones
frame_central = ttk.Frame(pantalla_inicio)
frame_central.grid(row=1, column=0)
frame_central.columnconfigure((0, 1), weight=1)  # dos columnas de igual peso

title = ttk.Label(pantalla_inicio, text="Menú principal", font=("Hevetica", 16, "bold"))
title.grid(row=0, column=0, columnspan=2, pady=(30, 20))

# Botón para ver datos de consumo
btn1 = ttk.Button(frame_central,
                  style="Rounded.TButton",
                  text="API Onomondo",
                  command=lambda: mostrar_pantalla(pantalla_datos))

# Botón para enviar comandos por tag
btn2 = ttk.Button(frame_central,
                  style="Rounded.TButton",
                  text="Enviar comandos",
                  command=lambda: mostrar_pantalla(pantalla_commands))

# Botón para actualizar cabeceras
btn3 = ttk.Button(frame_central,
                  style="Rounded.TButton",
                  text="Update cabeceras",
                  command=lambda: mostrar_pantalla(pantalla_update))

# Botón para subir ficheros a la cabecera
btn4 = ttk.Button(frame_central,
                  style="Rounded.TButton",
                  text="Upload files",
                  command=lambda: mostrar_pantalla(pantalla_upload))

# Botón para salir de la aplicación
btn5 = ttk.Button(frame_central,
                  style="Rounded.TButton",
                  text="Salir",
                  command=ventana.quit)

# Distribucion en grid
btn1.grid(row=1, column=0, padx=15, pady=15)
btn2.grid(row=1, column=1, padx=15, pady=15)
btn3.grid(row=2, column=0, padx=15, pady=15)
btn4.grid(row=2, column=1, padx=15, pady=15)
btn5.grid(row=3, column=0, columnspan=2, pady=15)
