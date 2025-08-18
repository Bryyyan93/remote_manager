import tkinter as tk
import logging
from ssh import comandos_ssh, api_petitions, utils
from api_onomondo import onomondo
from tkinter import scrolledtext, ttk
from . import gui_main as main

logger = logging.getLogger("api")


###############################################################
# Realiza la peticion API al pulsar el boton de consultar datos
###############################################################
def obtener_datos(entry_tag, salida, opc):
    tag = entry_tag.get()
    # Comprueba que el tag no esta vacio
    # Limpia el area de texto para mostrar nuevos resultados
    salida.delete(1.0, tk.END)
    if opc == "c":
        comandos_ssh.inst_tag = tag
        api_petitions.get_usage(tag)
    elif opc == "l":
        comandos_ssh.inst_tag = tag
        api_petitions.get_limit(tag)


########################################################
# Funicion que imprime en el cuadro de texto
########################################################
def imprimir_texto(salida, texto):
    salida.insert(tk.END, texto)  # Agrega texto al final
    salida.yview(tk.END)  # Desplaza automáticamente hacia abajo


########################################################
# Funicion que limpia el cuadro de texto
########################################################
def limpiar_consola(salida):
    salida.delete("1.0", tk.END)  # Borra todo el contenido


################################################################################
# Esta función se encarga de cerrar la ventana y eliminar el handler del logger
################################################################################
def cerrar_ventana(pantalla):
    for handler in logger.handlers[:]:
        if isinstance(handler, utils.TkinterHandler):
            logger.removeHandler(handler)
    pantalla.destroy()


################################################################
# Esta función se encarga obtener_datos para cada uno de ellos
################################################################
def cargar_datos(listbox_tags, salida, opc):
    seleccion = [listbox_tags.get(i) for i in listbox_tags.curselection()]
    if not seleccion:
        logger.error("Campo vacío. Debes seleccionar al menos un tag.")
    else:
        for tag in seleccion:
            try:
                # Simular la entrada de un tag en el Entry, usando el tag directamente
                entry_simulado = type('FakeEntry', (object,), {'get': lambda self: tag})()
                obtener_datos(entry_simulado, salida, opc)
            except Exception as e:
                logger.error(f"Error al ejecutar datos de consumo para el tag {tag}: {e}")


#################################################################################
# Crea una pantalla para consultar el consumo de datos de SIMs a partir de un tag
#################################################################################
def ver_consumos(opc):
    modal = tk.Toplevel()
    modal.title("Consumos por tag")
    modal.configure(bg="#2b2b2b")  # Fondo oscuro
    modal.geometry("650x600")

    # Frame para la lista de tags
    fila_tags = ttk.Frame(modal)
    fila_tags.pack(pady=5)

    ttk.Label(fila_tags, text="Selecciona Tags:", font=("Helvetica", 14, "bold")).pack(pady=5)
    tags = onomondo.get_tags(utils.api_headers())
    listbox_tags = tk.Listbox(fila_tags,
                              bg="#2e2e2e",
                              fg="white",
                              selectmode=tk.EXTENDED,
                              height=10)

    for tag in tags:
        listbox_tags.insert(tk.END, tag)
    listbox_tags.pack(side="left", padx=5)

    boton_frame = ttk.Frame(modal)
    boton_frame.pack(pady=10)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Ver datos",
               command=lambda: cargar_datos(listbox_tags, salida, opc)).pack(side="left", padx=5)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Volver",
               command=lambda: cerrar_ventana(modal)).pack(side="left", padx=5)

    salida = scrolledtext.ScrolledText(modal,
                                       bg="#2e2e2e",
                                       fg="white",
                                       insertbackground="white",
                                       width=80,
                                       height=20)
    salida.pack(padx=10, pady=10)

    # Configurar logger con salida al widget
    tk_handler = utils.TkinterHandler(salida)
    utils.configurar_logger("api", handler_personalizado=tk_handler)


#################################################################################
# Crea una pantalla para consultar el consumo de datos de SIMs a partir de un tag
#################################################################################
def ver_limites(opc):
    modal = tk.Toplevel()
    modal.title("Limites de consumos por tag")
    modal.configure(bg="#2b2b2b")  # Fondo oscuro
    modal.geometry("650x600")

    # Frame para la lista de tags
    fila_tags = ttk.Frame(modal)
    fila_tags.pack(pady=5)

    ttk.Label(fila_tags, text="Selecciona Tags:", font=("Helvetica", 14, "bold")).pack(pady=5)
    tags = onomondo.get_tags(utils.api_headers())
    listbox_tags = tk.Listbox(fila_tags,
                              bg="#2e2e2e",
                              fg="white",
                              selectmode=tk.EXTENDED,
                              height=10)

    for tag in tags:
        listbox_tags.insert(tk.END, tag)
    listbox_tags.pack(side="left", padx=5)

    boton_frame = ttk.Frame(modal)
    boton_frame.pack(pady=10)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Ver datos",
               command=lambda: cargar_datos(listbox_tags, salida, opc)).pack(side="left", padx=5)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Volver",
               command=lambda: cerrar_ventana(modal)).pack(side="left", padx=5)
    salida = scrolledtext.ScrolledText(modal,
                                       bg="#2e2e2e",
                                       fg="white",
                                       insertbackground="white",
                                       width=80,
                                       height=20)
    salida.pack(padx=10, pady=10)
    # Configurar logger con salida al widget
    tk_handler = utils.TkinterHandler(salida)
    utils.configurar_logger("api", handler_personalizado=tk_handler)


#################################################################################
# Crea una pantalla para consultar el consumo de datos de SIMs a partir de un tag
#################################################################################
def pantalla_api(contenedor, pantalla_inicio):
    pantalla_api = ttk.Frame(contenedor)
    ttk.Label(pantalla_api, text="Consulta API Onomondo", font=("Helvetica", 14, "bold")).pack(pady=(10, 5))

    # Botones pantalla principal API
    main.estilo()  # aplicar el estilo
    boton_frame = ttk.Frame(pantalla_api)
    boton_frame.pack(pady=(20))

    btn1 = ttk.Button(boton_frame,
                      style="Rounded.TButton",
                      text="Ver consumos",
                      command=lambda: ver_consumos("c"))
    btn2 = ttk.Button(boton_frame,
                      style="Rounded.TButton",
                      text="Ver limites",
                      command=lambda: ver_limites("l"))
    btn3 = ttk.Button(boton_frame,
                      style="Rounded.TButton",
                      text="Volver",
                      command=lambda: main.mostrar_pantalla(pantalla_inicio))

    # Distribucion en grid
    btn1.grid(row=0, column=0, padx=15, pady=10)
    btn2.grid(row=0, column=1, padx=15, pady=10)
    btn3.grid(row=1, column=0, columnspan=2, pady=10)

    return pantalla_api
