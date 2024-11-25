import json
import os
import PySimpleGUI as sg
import pandas as pd
import matplotlib.pyplot as plt


USUARIOS_FILE = "usuarios.txt"
EVENTOS_FILE = "eventos.json"
PARTICIPANTES_FILE = "participantes.json"
CONFIG_FILE = "config.json"


def inicializar_archivos():
    if not os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, "w") as f:
            f.write("admin,1234\nusuario1,abcd\nusuario2,pass123\n")

    if not os.path.exists(EVENTOS_FILE):
        with open(EVENTOS_FILE, "w") as f:
            json.dump([], f)

    if not os.path.exists(PARTICIPANTES_FILE):
        with open(PARTICIPANTES_FILE, "w") as f:
            json.dump([], f)

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "validar_aforo": False,
                "solicitar_imagen": False,
                "mostrar_modificar": True,
                "mostrar_eliminar": True
            }, f)

inicializar_archivos()


def leer_json(file):
    try:
        with open(file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def escribir_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)


def ventana_registro():
    layout_registro = [
        [sg.Text("Nombre de Usuario:"), sg.InputText(key="usuario")],
        [sg.Text("Contraseña:"), sg.InputText(key="contraseña", password_char="*")],
        [sg.Button("Registrar"), sg.Button("Cancelar")],
        [sg.Text("", size=(40, 1), key="mensaje_error", text_color="red")]
    ]

    window = sg.Window("Registrar Usuario", layout_registro)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Cancelar"):
            window.close()
            break

        if event == "Registrar":
            usuario = values["usuario"].strip()
            contraseña = values["contraseña"].strip()

            if not usuario or not contraseña:
                window["mensaje_error"].update("Ambos campos son obligatorios.")
                continue

            try:
                with open(USUARIOS_FILE, "r") as f:
                    usuarios = [line.strip().split(",")[0] for line in f if "," in line]
            except FileNotFoundError:
                usuarios = []

            if usuario in usuarios:
                window["mensaje_error"].update("El usuario ya existe.")
                continue

            with open(USUARIOS_FILE, "a") as f:
                f.write(f"{usuario},{contraseña}\n")

            sg.popup("Usuario registrado exitosamente.", title="Éxito")
            window.close()
            break


def ventana_login():
    layout_login = [
        [sg.Text("Usuario:"), sg.InputText(key="usuario")],
        [sg.Text("Contraseña:"), sg.InputText(key="contraseña", password_char="*")],
        [sg.Button("Iniciar Sesión"), sg.Button("Registrar Usuario"), sg.Button("Salir")],
        [sg.Text("", size=(40, 1), key="mensaje_error", text_color="red")]
    ]

    window = sg.Window("Inicio de Sesión", layout_login)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Salir"):
            window.close()
            return None

        if event == "Registrar Usuario":
            window.hide()
            ventana_registro()
            window.un_hide()

        if event == "Iniciar Sesión":
            usuario = values["usuario"].strip()
            contraseña = values["contraseña"].strip()

            try:
                with open(USUARIOS_FILE, "r") as f:
                    usuarios = [line.strip().split(",") for line in f if "," in line]
            except Exception as e:
                sg.popup(f"Error al leer usuarios: {e}", title="Error")
                return None

            for u, p in usuarios:
                if u == usuario and p == contraseña:
                    sg.popup("Inicio de sesión exitoso", title="Éxito")
                    window.close()
                    return usuario

            window["mensaje_error"].update("Usuario o contraseña incorrectos.")


def ventana_eventos():
    eventos = leer_json(EVENTOS_FILE)
    config = leer_json(CONFIG_FILE)

    layout_eventos = [
        [sg.Table(values=[[e["nombre"], e["cupo"], e.get("fecha", ""), e.get("lugar", ""), e.get("hora", ""), e.get("imagen", "")]
                          for e in eventos],
                  headings=["Nombre", "Cupo", "Fecha", "Lugar", "Hora", "Imagen"],
                  key="tabla_eventos",
                  auto_size_columns=False,
                  justification="center",
                  enable_events=True,
                  select_mode=sg.TABLE_SELECT_MODE_BROWSE)],
        [sg.Text("Nombre:"), sg.InputText(key="nombre_evento")],
        [sg.Text("Cupo:"), sg.InputText(key="cupo_evento")],
        [sg.Text("Fecha (YYYY-MM-DD):"), sg.InputText(key="fecha_evento")],
        [sg.Text("Lugar:"), sg.InputText(key="lugar_evento")],
        [sg.Text("Hora (HH:MM):"), sg.InputText(key="hora_evento")],
        [sg.Text("Imagen:"), sg.InputText(key="imagen_evento"), sg.FileBrowse(file_types=(("Archivos de imagen", "*.png;*.jpg;*.jpeg"),))],
        [sg.Button("Agregar Evento"),
         sg.Button("Modificar Evento", visible=config.get("mostrar_modificar", True)),
         sg.Button("Eliminar Evento", visible=config.get("mostrar_eliminar", True)),
         sg.Button("Salir")]
    ]

    window = sg.Window("Gestión de Eventos", layout_eventos)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Salir"):
            window.close()
            break

        if event == "Agregar Evento":
            nombre = values["nombre_evento"].strip()
            cupo = values["cupo_evento"].strip()
            fecha = values["fecha_evento"].strip()
            lugar = values["lugar_evento"].strip()
            hora = values["hora_evento"].strip()
            imagen = values["imagen_evento"].strip()

            if not nombre or not cupo or not fecha or not lugar or not hora:
                sg.popup("Todos los campos son obligatorios (excepto Imagen).", title="Error")
                continue

            try:
                cupo = int(cupo)
            except ValueError:
                sg.popup("El cupo debe ser un número.", title="Error")
                continue

            if any(evento["nombre"] == nombre for evento in eventos):
                sg.popup("Ya existe un evento con ese nombre.", title="Error")
                continue

            nuevo_evento = {
                "nombre": nombre,
                "cupo": cupo,
                "fecha": fecha,
                "lugar": lugar,
                "hora": hora,
                "imagen": imagen
            }
            eventos.append(nuevo_evento)
            escribir_json(EVENTOS_FILE, eventos)
            sg.popup("Evento agregado exitosamente.", title="Éxito")
            window["tabla_eventos"].update([[e["nombre"], e["cupo"], e.get("fecha", ""), e.get("lugar", ""), e.get("hora", ""), e.get("imagen", "")]
                                            for e in eventos])

        if event == "Modificar Evento":
            seleccion = values["tabla_eventos"]
            if not seleccion:
                sg.popup("Seleccione un evento para modificar.", title="Error")
                continue

            indice = seleccion[0]
            nuevo_nombre = values["nombre_evento"].strip()
            nuevo_cupo = values["cupo_evento"].strip()
            nueva_fecha = values["fecha_evento"].strip()
            nuevo_lugar = values["lugar_evento"].strip()
            nueva_hora = values["hora_evento"].strip()
            nueva_imagen = values["imagen_evento"].strip()

            if not nuevo_nombre or not nuevo_cupo or not nueva_fecha or not nuevo_lugar or not nueva_hora:
                sg.popup("Todos los campos son obligatorios (excepto Imagen).", title="Error")
                continue

            try:
                nuevo_cupo = int(nuevo_cupo)
            except ValueError:
                sg.popup("El cupo debe ser un número.", title="Error")
                continue

            eventos[indice] = {
                "nombre": nuevo_nombre,
                "cupo": nuevo_cupo,
                "fecha": nueva_fecha,
                "lugar": nuevo_lugar,
                "hora": nueva_hora,
                "imagen": nueva_imagen
            }

            escribir_json(EVENTOS_FILE, eventos)
            sg.popup("Evento modificado exitosamente.", title="Éxito")
            window["tabla_eventos"].update([[e["nombre"], e["cupo"], e.get("fecha", ""), e.get("lugar", ""), e.get("hora", ""), e.get("imagen", "")]
                                            for e in eventos])

        if event == "Eliminar Evento":
            seleccion = values["tabla_eventos"]
            if not seleccion:
                sg.popup("Seleccione un evento para eliminar.", title="Error")
                continue

            indice = seleccion[0]
            eventos.pop(indice)
            escribir_json(EVENTOS_FILE, eventos)
            sg.popup("Evento eliminado exitosamente.", title="Éxito")
            window["tabla_eventos"].update([[e["nombre"], e["cupo"], e.get("fecha", ""), e.get("lugar", ""), e.get("hora", ""), e.get("imagen", "")]
                                            for e in eventos])


# --- Ventana Participantes ---
def ventana_participantes():
    participantes = leer_json(PARTICIPANTES_FILE)
    eventos = leer_json(EVENTOS_FILE)
    config = leer_json(CONFIG_FILE)

    layout_participantes = [
        [sg.Table(values=[[p["nombre"], p["tipo_documento"], p["documento"], p["telefono"], p["direccion"], p["tipo_participante"], p["evento"]]
                          for p in participantes],
                  headings=["Nombre", "Tipo Documento", "Documento", "Teléfono", "Dirección", "Tipo Participante", "Evento"],
                  key="tabla_participantes",
                  auto_size_columns=False,
                  justification="center",
                  enable_events=True,
                  select_mode=sg.TABLE_SELECT_MODE_BROWSE)],
        [sg.Text("Nombre:"), sg.InputText(key="nombre_participante")],
        [sg.Text("Tipo Documento:"), sg.Combo(["CC", "TI", "Pasaporte"], key="tipo_documento_participante")],
        [sg.Text("Documento:"), sg.InputText(key="documento_participante")],
        [sg.Text("Teléfono:"), sg.InputText(key="telefono_participante")],
        [sg.Text("Dirección:"), sg.InputText(key="direccion_participante")],
        [sg.Text("Foto:"), sg.InputText(key="foto_participante"), sg.FileBrowse(file_types=(("Archivos de imagen", "*.png;*.jpg;*.jpeg"),))],
        [sg.Text("Tipo Participante:"), sg.Combo(["Estudiante", "Invitado", "admin"], key="tipo_participante")],
        [sg.Text("Evento:"), sg.Combo(values=[e["nombre"] for e in eventos], key="evento_participante")],
        [sg.Button("Agregar Participante"),
         sg.Button("Modificar Participante", visible=config.get("mostrar_modificar", True)),
         sg.Button("Eliminar Participante", visible=config.get("mostrar_eliminar", True)),
         sg.Button("Salir")]
    ]

    window = sg.Window("Gestión de Participantes", layout_participantes)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Salir"):
            window.close()
            break

        if event == "Agregar Participante":
            nombre = values["nombre_participante"].strip()
            tipo_documento = values["tipo_documento_participante"]
            documento = values["documento_participante"].strip()
            telefono = values["telefono_participante"].strip()
            direccion = values["direccion_participante"].strip()
            foto = values["foto_participante"].strip()
            tipo_participante = values["tipo_participante"]
            evento_nombre = values["evento_participante"]

            # Validar configuración de imagen
            if config.get("solicitar_imagen", False) and not foto:
                sg.popup("El campo de imagen es obligatorio.", title="Error")
                continue

            # Validar aforo
            if config.get("validar_aforo", False):
                try:
                    evento = next(e for e in eventos if e["nombre"] == evento_nombre)
                    participantes_en_evento = [p for p in participantes if p["evento"] == evento_nombre]
                    if len(participantes_en_evento) >= evento["cupo"]:
                        sg.popup("El evento ha alcanzado su aforo máximo.", title="Error")
                        continue
                except StopIteration:
                    sg.popup("El evento seleccionado no existe.", title="Error")
                    continue

            # Validar campos obligatorios
            if not (nombre and tipo_documento and documento and telefono and direccion and tipo_participante and evento_nombre):
                sg.popup("Todos los campos son obligatorios (excepto Foto).", title="Error")
                continue

            try:
                # Validar duplicados
                for participante in participantes:
                    if participante["documento"] == documento:
                        raise ValueError("Ya existe un participante con ese documento.")
            except ValueError as e:
                sg.popup(str(e), title="Error")
                continue

            nuevo_participante = {
                "nombre": nombre,
                "tipo_documento": tipo_documento,
                "documento": documento,
                "telefono": telefono,
                "direccion": direccion,
                "foto": foto,
                "tipo_participante": tipo_participante,
                "evento": evento_nombre
            }

            participantes.append(nuevo_participante)
            escribir_json(PARTICIPANTES_FILE, participantes)
            sg.popup("Participante agregado exitosamente.", title="Éxito")
            window["tabla_participantes"].update([[p["nombre"], p["tipo_documento"], p["documento"], p["telefono"], p["direccion"], p["tipo_participante"], p["evento"]]
                                                  for p in participantes])

        if event == "Modificar Participante":
            seleccion = values["tabla_participantes"]
            if not seleccion:
                sg.popup("Seleccione un participante para modificar.", title="Error")
                continue

            indice = seleccion[0]
            nuevo_nombre = values["nombre_participante"].strip()
            nuevo_tipo_documento = values["tipo_documento_participante"]
            nuevo_documento = values["documento_participante"].strip()
            nuevo_telefono = values["telefono_participante"].strip()
            nueva_direccion = values["direccion_participante"].strip()
            nueva_foto = values["foto_participante"].strip()
            nuevo_tipo_participante = values["tipo_participante"]
            nuevo_evento = values["evento_participante"]

            if not (nuevo_nombre and nuevo_tipo_documento and nuevo_documento and nuevo_telefono and nueva_direccion and nuevo_tipo_participante and nuevo_evento):
                sg.popup("Todos los campos son obligatorios (excepto Foto).", title="Error")
                continue

            participantes[indice] = {
                "nombre": nuevo_nombre,
                "tipo_documento": nuevo_tipo_documento,
                "documento": nuevo_documento,
                "telefono": nuevo_telefono,
                "direccion": nueva_direccion,
                "foto": nueva_foto,
                "tipo_participante": nuevo_tipo_participante,
                "evento": nuevo_evento
            }

            escribir_json(PARTICIPANTES_FILE, participantes)
            sg.popup("Participante modificado exitosamente.", title="Éxito")
            window["tabla_participantes"].update([[p["nombre"], p["tipo_documento"], p["documento"], p["telefono"], p["direccion"], p["tipo_participante"], p["evento"]]
                                                  for p in participantes])

        if event == "Eliminar Participante":
            seleccion = values["tabla_participantes"]
            if not seleccion:
                sg.popup("Seleccione un participante para eliminar.", title="Error")
                continue

            indice = seleccion[0]
            participantes.pop(indice)
            escribir_json(PARTICIPANTES_FILE, participantes)
            sg.popup("Participante eliminado exitosamente.", title="Éxito")
            window["tabla_participantes"].update([[p["nombre"], p["tipo_documento"], p["documento"], p["telefono"], p["direccion"], p["tipo_participante"], p["evento"]]
                                                  for p in participantes])
            

def ventana_configuracion():
    config = leer_json(CONFIG_FILE)

    layout_config = [
        [sg.Checkbox("Validar aforo al agregar participante", default=config.get("validar_aforo", False), key="validar_aforo")],
        [sg.Checkbox("Solicitar imagen", default=config.get("solicitar_imagen", False), key="solicitar_imagen")],
        [sg.Checkbox("Modificar registro", default=config.get("mostrar_modificar", True), key="mostrar_modificar")],
        [sg.Checkbox("Eliminar registro", default=config.get("mostrar_eliminar", True), key="mostrar_eliminar")],
        [sg.Button("Guardar Configuración"), sg.Button("Cancelar")]
    ]

    window = sg.Window("Configuración", layout_config)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Cancelar"):
            break

        if event == "Guardar Configuración":
            config["validar_aforo"] = values["validar_aforo"]
            config["solicitar_imagen"] = values["solicitar_imagen"]
            config["mostrar_modificar"] = values["mostrar_modificar"]
            config["mostrar_eliminar"] = values["mostrar_eliminar"]
            escribir_json(CONFIG_FILE, config)
            sg.popup("Configuración guardada exitosamente.", title="Éxito")
            break

    window.close()
def ventana_analisis():
    participantes = leer_json(PARTICIPANTES_FILE)
    eventos = leer_json(EVENTOS_FILE)

    # Nombres de los eventos
    nombres_eventos = [evento["nombre"] for evento in eventos]

    # Análisis de los participantes
    participantes_todos_eventos = []
    participantes_un_evento = []
    participantes_primer_evento = []

    try:
        # Participantes que asistieron a todos los eventos
        for participante in participantes:
            eventos_participados = {p["evento"] for p in participantes if p["documento"] == participante["documento"]}
            if set(nombres_eventos).issubset(eventos_participados) and participante not in participantes_todos_eventos:
                participantes_todos_eventos.append(participante)

        # Participantes que asistieron al menos a un evento
        participantes_un_evento = participantes.copy()

        # Participantes que solo asistieron al primer evento
        if nombres_eventos:
            primer_evento = nombres_eventos[0]
            for participante in participantes:
                eventos_participados = {p["evento"] for p in participantes if p["documento"] == participante["documento"]}
                if len(eventos_participados) == 1 and primer_evento in eventos_participados:
                    participantes_primer_evento.append(participante)

    except Exception as e:
        sg.popup(f"Error durante el análisis: {e}", title="Error")

    # Diseñar la interfaz de análisis
    layout_analisis = [
        [sg.Text("Participantes en todos los eventos")],
        [sg.Table(values=[[p["nombre"], p["documento"]] for p in participantes_todos_eventos],
                  headings=["Nombre", "Documento"],
                  auto_size_columns=False,
                  justification="center",
                  key="tabla_todos_eventos")],
        [sg.Text("Participantes en al menos un evento")],
        [sg.Table(values=[[p["nombre"], p["documento"]] for p in participantes_un_evento],
                  headings=["Nombre", "Documento"],
                  auto_size_columns=False,
                  justification="center",
                  key="tabla_un_evento")],
        [sg.Text("Participantes solo en el primer evento")],
        [sg.Table(values=[[p["nombre"], p["documento"]] for p in participantes_primer_evento],
                  headings=["Nombre", "Documento"],
                  auto_size_columns=False,
                  justification="center",
                  key="tabla_primer_evento")],
        [sg.Button("Salir")]
    ]

    window = sg.Window("Análisis de Participantes", layout_analisis)

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Salir"):
            window.close()
            break

def ventana_graficas():
    participantes = leer_json(PARTICIPANTES_FILE)
    eventos = leer_json(EVENTOS_FILE)

    try:
        # Gráfica 1: Participantes por tipo de participante (Gráfica de Pie)
        tipos = [p["tipo_participante"] for p in participantes]
        if tipos:
            tipo_counts = {tipo: tipos.count(tipo) for tipo in set(tipos)}
            plt.pie(tipo_counts.values(), labels=tipo_counts.keys(), autopct="%1.1f%%")
            plt.title("Distribución por Tipo de Participante")
            plt.show()
        else:
            sg.popup("No hay datos de participantes para la gráfica de tipos.", title="Información")

        # Gráfica 2: Participantes por evento (Gráfica de Barras)
        eventos_participantes = [p["evento"] for p in participantes]
        if eventos_participantes:
            evento_counts = {evento: eventos_participantes.count(evento) for evento in set(eventos_participantes)}
            plt.bar(evento_counts.keys(), evento_counts.values())
            plt.title("Participantes por Evento")
            plt.xlabel("Eventos")
            plt.ylabel("Número de Participantes")
            plt.xticks(rotation=45)
            plt.show()
        else:
            sg.popup("No hay datos de participantes para la gráfica de eventos.", title="Información")

        # Gráfica 3: Eventos por fecha (Gráfica de Barras)
        fechas = [e["fecha"] for e in eventos if "fecha" in e]
        if fechas:
            fecha_counts = {fecha: fechas.count(fecha) for fecha in set(fechas)}
            plt.bar(fecha_counts.keys(), fecha_counts.values(), color="orange")
            plt.title("Eventos por Fecha")
            plt.xlabel("Fecha")
            plt.ylabel("Número de Eventos")
            plt.xticks(rotation=45)
            plt.show()
        else:
            sg.popup("No hay datos de eventos para la gráfica de fechas.", title="Información")

    except KeyError as e:
        sg.popup(f"Faltan datos en los registros: {e}", title="Error")
    except Exception as e:
        sg.popup(f"Error al generar gráficas: {e}", title="Error")


# --- Flujo Principal ---
def main():
    usuario = ventana_login()
    if not usuario:
        return

    sg.popup(f"Bienvenido {usuario}", title="Inicio de Sesión")

    layout_main = [
        [sg.Button("Gestión de Eventos"), sg.Button("Gestión de Participantes"),
         sg.Button("Configuración"), sg.Button("Análisis"), sg.Button("Gráficas"), sg.Button("Salir")]
    ]

    window = sg.Window("Sistema de Gestión", layout_main)

    while True:
        event, _ = window.read()

        if event in (sg.WINDOW_CLOSED, "Salir"):
            break

        if event == "Gestión de Eventos":
            ventana_eventos()

        if event == "Gestión de Participantes":
            ventana_participantes()

        if event == "Configuración":
            ventana_configuracion()

        if event == "Análisis":
            ventana_analisis()

        if event == "Gráficas":
            ventana_graficas()

    window.close()

if __name__ == "__main__":
    main()


