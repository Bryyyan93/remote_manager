from ssh import utils, api_petitions as petition, comandos_ssh as ssh
from api_onomondo import onomondo
from tkinter import scrolledtext, Toplevel, ttk
from . import gui_main as main
import tkinter as tk
import threading
import logging

logger = logging.getLogger("cmds")


########################################################
# Funicion que adquiere la tags
########################################################
def obtener_tags():
    # crea la instancia  para poder llamar a la api
    headers = utils.api_headers()
    # llama a la api y le devuelve los nombres de los tags
    data = onomondo.get_tags(headers)

    print("tags adquiridas: ", data)

    return data


########################################################
# Funicion que obtiene las ips online
########################################################
def obtener_ips(tag):
    # crea la instancia  para poder llamar a la api
    headers = utils.api_headers()
    # pide la lista de ips, y almacena las online en data
    data = petition.ip_list_api_mono(headers, tag)

    return data


########################################################
# Funicion que abre una emergente para la seleccion de las ips
########################################################
def abrir_emergente_ips(callback):
    def validar_ips(texto):
        # Limpia y divide las IPs por coma o salto de línea
        return [ip.strip() for ip in texto.replace('\n', ',').split(',') if ip.strip()]

    def mover_a_derecha():
        ips_nuevas = validar_ips(entrada_ips.get("1.0", tk.END))
        ya_agregadas = listbox_derecha.get(0, tk.END)
        for ip in ips_nuevas:
            if ip not in ya_agregadas:
                listbox_derecha.insert(tk.END, ip)
        actualizar_contador()

    def mover_a_izquierda():
        seleccionados = list(listbox_derecha.curselection())
        for i in reversed(seleccionados):
            listbox_derecha.delete(i)
        actualizar_contador()

    def actualizar_contador():
        contador_label.config(text=f"Total seleccionadas: {listbox_derecha.size()}")

    def aceptar():
        seleccionadas = [listbox_derecha.get(i) for i in listbox_derecha.curselection()]
        main.ip_seleccionadas = tk.StringVar(value=",".join(seleccionadas))
        main.ip_a_utilizar = tk.StringVar(value=",".join(seleccionadas))
        callback(seleccionadas)
        modal.destroy()

    modal = tk.Toplevel()
    modal.title("Insertar IPs")
    modal.configure(bg="#2b2b2b")
    modal.geometry("700x500")

    contenedor = ttk.Frame(modal)
    contenedor.pack(pady=10, padx=10, fill="both", expand=True)

    ttk.Label(contenedor, text="Intoducir IPs").grid(row=0, column=0)
    ttk.Label(contenedor, text="Seleccionar IPs").grid(row=0, column=2)

    # Entrada tipo ScrolledText para escribir múltiples IPs
    entrada_ips = scrolledtext.ScrolledText(contenedor,
                                            bg="#2e2e2e",
                                            fg="white",
                                            insertbackground="white",
                                            width=35,
                                            height=20)
    entrada_ips.grid(row=1, column=0, padx=10)

    # Botones de mover
    botones = ttk.Frame(contenedor)
    botones.grid(row=1, column=1)
    ttk.Button(botones,
               style="Rounded.TButton",
               text=">>",
               command=mover_a_derecha).pack(pady=10)
    ttk.Button(botones,
               style="Rounded.TButton",
               text="<<",
               command=mover_a_izquierda).pack(pady=10)

    # Listbox de IPs seleccionadas
    listbox_derecha = tk.Listbox(contenedor,
                                 bg="#2e2e2e",
                                 fg="white",
                                 selectmode=tk.EXTENDED,
                                 width=35,
                                 height=20)
    listbox_derecha.grid(row=1, column=2, padx=10)

    contador_label = ttk.Label(modal, text="Total seleccionadas: 0")
    contador_label.pack(pady=5)

    # Precargar IPs anteriores si existen
    if main.ip_a_utilizar:
        for ip in main.ip_a_utilizar.get().split(","):
            listbox_derecha.insert(tk.END, ip.strip())
        actualizar_contador()

    boton_frame = ttk.Frame(modal)
    boton_frame.pack(pady=10)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Aceptar",
               command=aceptar).pack(side="left", padx=10)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Cerrar",
               command=modal.destroy).pack(side="left", padx=10)


########################################################
# Funicion que abre una emergente para la seleccion de las tags
########################################################
def abrir_emergente_tags(callback):
    # Obtiene las IPs de la API y las muestra en una lista segun el tag
    def cargar_ips():
        listbox_a.delete(0, tk.END)
        seleccionadas = [listbox_tags.get(i) for i in listbox_tags.curselection()]
        # Si no hay seleccion, no hace nada
        if not seleccionadas:
            return

        todas_las_ips = []  # Lista para almacenar las IPs obtenidas
        for tag in seleccionadas:
            try:
                ips = obtener_ips(tag)
                # Añadir las IPs
                todas_las_ips.extend(ips)
            except Exception as e:
                logging.error(f"Error con {tag}: {e}")
        # Insertar las IPs en el listbox_a
        for ip in todas_las_ips:
            if ip not in listbox_a.get(0, tk.END):  # Evitar duplicados
                listbox_a.insert(tk.END, ip)

    # Crear la ventana principal
    modal = Toplevel()
    modal.title("Tags")
    modal.configure(bg="#2b2b2b")  # Fondo oscuro
    modal.geometry("650x600")

    # Frame para la lista de tags
    fila_tags = ttk.Frame(modal)
    fila_tags.pack(pady=5)

    ttk.Label(fila_tags, text="Selecciona Tags:").pack(pady=5)
    tags = onomondo.get_tags(utils.api_headers())
    listbox_tags = tk.Listbox(fila_tags,
                              bg="#2e2e2e",
                              fg="white",
                              selectmode=tk.EXTENDED,
                              height=10)

    for tag in tags:
        listbox_tags.insert(tk.END, tag)
    listbox_tags.pack(side="left", padx=5)

    ttk.Button(fila_tags,
               style="Rounded.TButton",
               text="Ver IPs",
               command=cargar_ips).pack(side="left", padx=10)

    # Actualiza el contador de IPs
    def actualizar_contador():
        contador_label.config(text=f"Total seleccionadas: {listbox_b.size()}")
        contador_label.config(text=f"Total en lista: {listbox_a.size()}")

    # Mover los elementos entre las dos listas
    def mover_seleccionados(origen, destino):
        seleccionados = list(origen.curselection())
        valores = [origen.get(i) for i in seleccionados]
        for i in reversed(seleccionados):
            origen.delete(i)
        for valor in valores:
            if valor not in destino.get(0, tk.END):
                destino.insert(tk.END, valor)
        actualizar_contador()

    def aceptar():
        seleccionadas = list(listbox_b.get(0, tk.END))
        callback(seleccionadas)
        modal.destroy()

    contenedor = ttk.Frame(modal)
    contenedor.pack(pady=10)

    ttk.Label(contenedor, text="IPs disponibles").grid(row=0, column=0)
    ttk.Label(contenedor, text="IPs seleccionadas").grid(row=0, column=2)

    listbox_a = tk.Listbox(contenedor,
                           bg="#2e2e2e",
                           fg="white",
                           selectmode=tk.EXTENDED,
                           width=40, height=15)
    listbox_a.grid(row=1, column=0, padx=10)

    boton_frame = ttk.Frame(contenedor)
    boton_frame.grid(row=1, column=1)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text=">>",
               command=lambda: mover_seleccionados(listbox_a, listbox_b)).pack(pady=10)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="<<",
               command=lambda: mover_seleccionados(listbox_b, listbox_a)).pack(pady=10)

    listbox_b = tk.Listbox(contenedor,
                           bg="#2e2e2e",
                           fg="white",
                           selectmode=tk.EXTENDED,
                           width=40, height=15)
    listbox_b.grid(row=1, column=2, padx=10)

    contador_label = ttk.Label(modal, text="Total seleccionadas: 0")
    contador_label.pack(pady=5)

    boton_final = ttk.Frame(modal)
    boton_final.pack(pady=10)

    ttk.Button(boton_final,
               style="Rounded.TButton",
               text="Aceptar",
               command=aceptar).pack(side="left", padx=10)
    ttk.Button(boton_final,
               style="Rounded.TButton",
               text="Cerrar",
               command=modal.destroy).pack(side="left", padx=10)


########################################################
# Funicion que contiene la pantalla principal de tags
########################################################
def pantalla_commands(contenedor, pantalla_inicio):
    def cmd(cmmd_entry):
        comandos = cmmd_entry.get("1.0", tk.END).split("\n")  # Obtener texto desde la línea 1, posición 0 hasta el final
        print("Texto ingresado:", comandos)
        return comandos

    def user(user_entry):
        user = user_entry.get()
        print("User ingresado:", user)
        return user

    def psswd(psswd_entry):
        psswd = psswd_entry.get()
        print("Password ingresado:", psswd)
        return psswd

    def ip():
        ips = main.ip_seleccionadas.get().split(",")
        print("lista ips: ", ips)
        return ips

    # callback para establecer las IPs seleccionadas desde el modal
    def set_ips_desde_tags(lista_ips):
        joined = ",".join(lista_ips)
        main.ip_a_utilizar = tk.StringVar(value=joined)
        main.ip_seleccionadas = tk.StringVar(value=joined)
        print("IPs establecidas desde tags:", lista_ips)

    main.estilo()
    pantalla_tags = ttk.Frame(contenedor)
    # Usamos grid() en todo el diseño
    pantalla_tags.columnconfigure(1, weight=1)

    ttk.Label(pantalla_tags, text="Enviar comandos por tag", font=("Arial", 14)).grid(row=0, column=0, columnspan=2, pady=10)
    # Fila con Label + Entry
    input_frame = ttk.Frame(pantalla_tags)
    input_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10))

    # Campo de entrada para el usuario
    ttk.Label(input_frame, text="User:", style="TLabel").grid(row=0, column=0, padx=5, pady=1, sticky="n")
    user_entry = tk.Entry(input_frame,
                          bg="#2e2e2e",
                          fg="white",
                          insertbackground="white",
                          width=30)
    user_entry.grid(row=1, column=0, padx=5, pady=5)

    # Campo de entrada para la contraseña
    ttk.Label(input_frame, text="Password:", style="TLabel").grid(row=0, column=1, padx=5, pady=1, sticky="n")
    psswd_entry = tk.Entry(input_frame,
                           bg="#2e2e2e",
                           fg="white",
                           insertbackground="white",
                           show="*",
                           width=30)  # Usamos show="*" para ocultar la contraseña
    psswd_entry.grid(row=1, column=1, padx=5, pady=5)

    # Boton de tag (Redireccion a pantalla emergente)
    tag_button = ttk.Button(input_frame,
                            text="Obtener IP por Tag",
                            command=lambda: threading.Thread(target=abrir_emergente_tags, args=(set_ips_desde_tags,)).start(),
                            style="Rounded.TButton")
    tag_button.grid(row=3, column=0, padx=5, pady=5)

    # Boton de lista de ips (Redireccion a pantalla emergente)
    tag_button = ttk.Button(input_frame,
                            text="Insertar IP",
                            command=lambda: threading.Thread(target=abrir_emergente_ips(callback=set_ips_desde_tags,)).start(), style="Rounded.TButton")
    tag_button.grid(row=3, column=1, padx=5, pady=5)

    # Fila con los botones lado a lado
    boton_frame = ttk.Frame(pantalla_tags)
    boton_frame.grid(row=4, column=1, padx=5, pady=5)

    # Campo de entrada para el usuario
    ttk.Label(input_frame, text="Comandos:", style="TLabel").grid(row=5, column=0, padx=1, pady=1)
    cmmd_entry = tk.Text(input_frame,
                         bg="#2e2e2e",
                         fg="white",
                         insertbackground="white",
                         width=60,
                         height=6,
                         font=("Consolas", 10),
                         wrap="word")
    cmmd_entry.grid(row=5, column=1, padx=3, pady=3)

    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Ejecutar",
               command=lambda: ssh.command_all_ips(cmd(cmmd_entry),
                                                   user(user_entry),
                                                   psswd(psswd_entry), ip())).grid(row=6, column=0, padx=5, pady=5)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Volver",
               command=lambda: main.mostrar_pantalla(pantalla_inicio)).grid(row=6, column=1, padx=5, pady=5)

    salida_comandos = scrolledtext.ScrolledText(pantalla_tags,
                                                bg="#2e2e2e",
                                                fg="white",
                                                insertbackground="white",
                                                width=80,
                                                height=15)
    salida_comandos.grid(row=7, column=1, padx=5, pady=5)

    # Configurar logger con salida al widget
    tk_handler = utils.TkinterHandler(salida_comandos)
    utils.configurar_logger("cmds", handler_personalizado=tk_handler)

    return pantalla_tags
