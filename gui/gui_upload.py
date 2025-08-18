from ssh import comandos_ssh, utils, upload_files as upload, api_petitions as petition
from tkinter import scrolledtext, filedialog, ttk
from . import gui_main as main
from api_onomondo import onomondo
import tkinter as tk
import logging


########################################################
# Funicion que obtiene las ips online
########################################################
def obtener_ips(tag):
    # crea la instancia  para poder llamar a la api
    headers = utils.api_headers()

    data = petition.ip_list_api_mono(headers, tag)

    return data


##############################################################################
# Abre una ventana emergente para seleccionar IPs manualmente o desde API,
# según la opción seleccionada en el menú desplegable.
###############################################################################
def seleccionar_lista(seleccion_ips):
    if seleccion_ips.get() == "ip_list":
        abrir_modal_iplist(lambda lista: setattr(comandos_ssh, "ip_list", lista))
    else:
        abrir_modal_taglist(lambda lista: setattr(comandos_ssh, "ip_list", lista))


#################################################################################
# Ejecuta el proceso de actualización en función del tipo de dispositivo.
#################################################################################
def ejecutar_upload(ip_list, entry_file, local_file, user_entry, pass_entry, salida, seleccion_dispositivo):
    logger = logging.getLogger("upload")

    dispositivo = seleccion_dispositivo.get()
    entry_file = entry_file.get()
    local_file = local_file.get()

    # Guardar valores
    upload.user = user_entry.get()
    upload.password = pass_entry.get()
    upload.local_filepath = entry_file
    upload.remote_filepath = local_file
    salida.delete(1.0, tk.END)

    logger.info(f"Dispositivo seleccionado: {dispositivo}")
    logger.info(f"Fichero: {entry_file}")

    if dispositivo == "CA/LX":
        upload.upload_files(ip_list, upload.user, upload.password, entry_file, local_file)
    elif dispositivo == "IMX":
        upload.upload_files(ip_list, upload.user, upload.password, entry_file, local_file)


#################################################################################
# Abre un explorador de archivos para seleccionar un archivo .zip.
# Guarda la ruta en el campo de entrada correspondiente.
#################################################################################
def seleccionar_file(entry):
    filepath = filedialog.askopenfilename()
    if filepath:
        entry.delete(0, tk.END)
        entry.insert(0, filepath)


#################################################################################
# Abre una ventana donde el usuario puede ingresar manualmente una lista de IPs.
# Al confirmar, las IPs se pasan a la función callback.
#################################################################################
def abrir_modal_iplist(callback):
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


#################################################################################
# Abre una ventana que muestra IPs obtenidas desde la API (por tag).
# Al aceptar, se pasan a la función callback.
#################################################################################
def abrir_modal_taglist(callback):
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
    modal = tk.Toplevel()
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
                              selectmode=tk.EXTENDED, height=10)

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


#################################################################################
# Crea y devuelve una pantalla (Frame) con todos los elementos para actualizar cabeceras
# en dispositivos remotos (CA/LX o IMX).
#################################################################################
def pantalla_upload(contenedor, pantalla_inicio):
    pantalla_upload = ttk.Frame(contenedor)
    ttk.Label(pantalla_upload, text="Subir ficheros", font=("Arial", 14)).pack(pady=10)

    # User + Pass horizontal
    main.estilo()  # aplicar el estilo
    userpass_frame = ttk.Frame(pantalla_upload)
    userpass_frame.pack(pady=(0, 10))

    ttk.Label(userpass_frame, text="User:").pack(side="left", padx=(0, 5))
    entry_user = tk.Entry(userpass_frame,
                          bg="#2e2e2e",
                          fg="white",
                          insertbackground="white",
                          width=15)
    entry_user.pack(side="left", padx=(0, 20))

    ttk.Label(userpass_frame, text="Pass:").pack(side="left", padx=(0, 5))
    entry_pass = tk.Entry(userpass_frame,
                          bg="#2e2e2e",
                          fg="white",
                          insertbackground="white",
                          width=15,
                          show="*")
    entry_pass.pack(side="left")

    # Dispositivo
    selector_frame = ttk.Frame(pantalla_upload)
    selector_frame.pack(pady=5)

    dispositivo_frame = ttk.Frame(selector_frame)
    dispositivo_frame.pack(side="left", padx=20)
    ttk.Label(dispositivo_frame, text="Dispositivo:").pack(side="left")
    dispositivos = ["CA/LX", "IMX"]
    seleccion_dispositivo = tk.StringVar(value=dispositivos[0])
    ttk.OptionMenu(dispositivo_frame,
                   seleccion_dispositivo,
                   dispositivos[0],
                   style="Rounded.TButton",
                   *dispositivos).pack(side="left")

    # IP list
    ips_frame = ttk.Frame(selector_frame)
    ips_frame.pack(side="left", padx=20)
    ttk.Label(ips_frame, text="Lista de IPs:").pack(side="left")
    ips = ["ip_list", "tag_list"]
    seleccion_ips = tk.StringVar(value=ips[0])

    ttk.OptionMenu(ips_frame,
                   seleccion_ips,
                   ips[0],
                   *ips,
                   style="Rounded.TButton",
                   command=lambda _: seleccionar_lista(seleccion_ips)).pack(side="left")

    # Seleccionador de ficheros .zip
    file_frame = ttk.Frame(pantalla_upload)
    file_frame.pack(pady=5)
    # Entry para mostrar la ruta del archivo seleccionado
    entry_file = tk.Entry(file_frame,
                          bg="#2e2e2e",
                          fg="white",
                          insertbackground="white",
                          width=40)
    entry_file.pack(side="left")

    # Botones
    ttk.Button(file_frame,
               style="Rounded.TButton",
               text="Seleccionar file",
               command=lambda: seleccionar_file(entry_file)).pack(side="left", padx=5)

    local_frame = ttk.Frame(pantalla_upload)
    local_frame.pack(pady=5)
    ttk.Label(local_frame, text="Ruta local:").pack(side="left", padx=(0, 5))
    entry_local = tk.Entry(local_frame,
                           bg="#2e2e2e",
                           fg="white",
                           insertbackground="white",
                           width=50)
    entry_local.pack(side="left")

    boton_frame = ttk.Frame(pantalla_upload)
    boton_frame.pack(pady=(0, 10))

    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Subir",
               command=lambda: ejecutar_upload(getattr(comandos_ssh, "ip_list", []),
                                               entry_file,
                                               entry_local,
                                               entry_user,
                                               entry_pass,
                                               salida_upload,
                                               seleccion_dispositivo)).pack(side="left", padx=5)
    ttk.Button(boton_frame,
               style="Rounded.TButton",
               text="Volver",
               command=lambda: main.mostrar_pantalla(pantalla_inicio)).pack(side="left", padx=5)

    salida_upload = scrolledtext.ScrolledText(pantalla_upload,
                                              bg="#2e2e2e",
                                              fg="white",
                                              insertbackground="white",
                                              width=80,
                                              height=20)
    salida_upload.pack(padx=10, pady=10)
    # Configurar logger con salida al widget
    tk_handler = utils.TkinterHandler(salida_upload)
    utils.configurar_logger("upload", handler_personalizado=tk_handler)

    return pantalla_upload
