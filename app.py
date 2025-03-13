import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials

# ---- CONFIGURACIÓN ----
# Reemplaza el siguiente valor por el ID de tu Google Sheets.
# El ID es la parte de la URL de tu hoja entre "/d/" y "/edit"
SPREADSHEET_ID = "Cue Sheets"
# Nombre de la pestaña donde se guardarán los datos (asegúrate que coincida con tu hoja)
SHEET_NAME = "Cue Sheets"

def parse_megatrack_text(text: str):
    """
    Función para parsear el texto copiado de Megatrack.
    Extrae:
      - trackTitle
      - trackCode
      - iswc
      - isrc
      - albumName
      - albumCode
      - composers (lista)
      - publishers (lista)
    """
    lines = text.split("\n")
    lines = [l.strip() for l in lines if l.strip()]

    trackTitle = ""
    trackCode = ""
    iswc = ""
    isrc = ""
    albumName = ""
    albumCode = ""
    composers = []
    publishers = []

    i = 0
    while i < len(lines):
        lower_line = lines[i].lower()
        # Detectar "Track" (por ejemplo: "Track", "Track:", etc.)
        if lower_line.startswith("track"):
            i += 1
            if i < len(lines):
                trackTitle = lines[i]
                i += 1
            if i < len(lines) and lines[i].lower().startswith("code"):
                parts = lines[i].split()
                if len(parts) > 1:
                    trackCode = parts[1]
                if "ISWC" in parts:
                    idx = parts.index("ISWC")
                    if idx + 1 < len(parts):
                        iswc = parts[idx + 1]
                if "ISRC" in parts:
                    idx = parts.index("ISRC")
                    if idx + 1 < len(parts):
                        isrc = parts[idx + 1]
                i += 1

        # Detectar "Album"
        elif lower_line.startswith("album"):
            i += 1
            if i < len(lines):
                albumName = lines[i]
                i += 1
            if i < len(lines) and lines[i].lower().startswith("code"):
                album_parts = lines[i].split()
                if len(album_parts) > 1:
                    albumCode = album_parts[1]
                i += 1

        # Detectar "Composers"
        elif lower_line.startswith("composers"):
            i += 1
            while i < len(lines) and not lines[i].lower().startswith("publisher"):
                composers.append(lines[i])
                i += 1

        # Detectar "Publisher"
        elif lower_line.startswith("publisher"):
            i += 1
            while i < len(lines):
                publishers.append(lines[i])
                i += 1
        else:
            i += 1

    return {
        "trackTitle": trackTitle,
        "trackCode": trackCode,
        "iswc": iswc,
        "isrc": isrc,
        "albumName": albumName,
        "albumCode": albumCode,
        "composers": composers,
        "publishers": publishers
    }

def append_to_google_sheets(parsed_data, titulo, capitulo, duracion, fecha_emision):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    
    import os, json
    from google.oauth2.service_account import Credentials
    import gspread
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    
    service_account_info = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
    creds = Credentials.from_service_account_info(service_account_info, scopes=scope)
    gc = gspread.authorize(creds)
    
    # Resto del código con la misma indentación
    # ...


    # Abrir el documento de Google Sheets y la pestaña
    sh = gc.open_by_key(SPREADSHEET_ID)
    wks = sh.worksheet(SHEET_NAME)

    # Preparar datos a insertar
    composers_str = "; ".join(parsed_data["composers"])
    publishers_str = "; ".join(parsed_data["publishers"])
    descripcion = f"ISWC: {parsed_data['iswc'] or 'N/A'} | ISRC: {parsed_data['isrc'] or 'N/A'} | Fecha Emisión: {fecha_emision}"
    new_row = [
        capitulo,                  # Columna A
        parsed_data["trackTitle"], # Columna B
        titulo,                    # Columna C
        duracion,                  # Columna D
        "",                        # Columna E (Uso)
        composers_str,             # Columna F
        descripcion,               # Columna G
        publishers_str             # Columna H
    ]

    # Agregar la nueva fila al final de la hoja
    wks.append_row(new_row, value_input_option="USER_ENTERED")

def main():
    st.title("Importar Cue Sheet desde Megatrack")
    st.write("### Instrucciones:")
    st.write("1. Ingresa los datos manuales (Título, Número de capítulo, Duración, Fecha de emisión).")
    st.write("2. Pega el texto copiado de Megatrack en el recuadro de abajo.")
    st.write("3. Presiona el botón 'Importar a Google Sheets' para enviar los datos.")

    # Datos manuales
    titulo = st.text_input("Título del programa/producción", "")
    numero_capitulo = st.text_input("Número de capítulo", "")
    duracion = st.text_input("Duración", "")
    fecha = st.date_input("Fecha de emisión", datetime.date.today())

    # Área de texto para el texto copiado de Megatrack
    megatrack_text = st.text_area("Texto copiado de Megatrack", height=200)

    if st.button("Importar a Google Sheets"):
        if not megatrack_text.strip():
            st.error("Por favor, pega el texto de Megatrack.")
        else:
            parsed_data = parse_megatrack_text(megatrack_text)
            try:
                append_to_google_sheets(
                    parsed_data,
                    titulo,
                    numero_capitulo,
                    duracion,
                    fecha.strftime("%Y-%m-%d")
                )
                st.success("¡Datos importados correctamente a Google Sheets!")
            except Exception as e:
                st.error(f"Error al importar: {e}")

if __name__ == "__main__":
    main()
