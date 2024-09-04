import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from requests.exceptions import ConnectionError

def obtener_datos_historicos(id_variable, desde, hasta):
    url = f"https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/{id_variable}/{desde}/{hasta}"
    print(f"URL de la solicitud: {url}")  # Imprimir la URL para verificación
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()

        # Imprimir la respuesta completa para diagnóstico
        print(f"Respuesta de datos históricos para ID {id_variable}:", data)

        # Verificar si la respuesta contiene 'results'
        if 'results' in data and isinstance(data['results'], list) and all(isinstance(item, dict) for item in data['results']):
            return data['results']
        else:
            print(f"Datos históricos para ID {id_variable} no tienen el formato esperado.")
            return []
    except requests.RequestException as e:
        print(f"Error al obtener datos históricos para ID {id_variable}: {e}")
        return []

try:
    # URL del endpoint para obtener las principales variables
    url = "https://api.bcra.gob.ar/estadisticas/v2.0/PrincipalesVariables"

    # Realizar la petición GET desactivando la verificación SSL
    response = requests.get(url, verify=False)

    # Verificar el estado de la respuesta
    response.raise_for_status()

    # Convertir la respuesta JSON a un diccionario de Python
    principales_variables = response.json()

    # Verificar que la respuesta JSON tenga el formato esperado
    if not isinstance(principales_variables, dict) or 'results' not in principales_variables:
        raise ValueError("La respuesta JSON de las principales variables no tiene el formato esperado.")

    # Variables específicas que nos interesan con IDs
    variables_interes = {
        1: "Reservas Internacionales del BCRA",
        5: "TC Mayorista",
        27: 'Inflación mensual',
        28: 'Inflación interanual',
        29: 'REM infla prox 12meses(mediana)',
        34: "Tasa de Política Monetaria (TEA)",
        7: 'BADLAR TNA'
    }

    # Filtrar los datos para quedarnos solo con las variables de interés y renombrarlas
    datos_filtrados = [
        {
            'idVariable': variable['idVariable'],
            'descripcion': variables_interes[variable['idVariable']],
            'valor': variable['valor'],
            'fecha': variable['fecha']
        } for variable in principales_variables['results'] if variable['idVariable'] in variables_interes
    ]

    # Definir el orden manual
    orden_manual = [ 1, 5, 27, 28, 29, 34, 7]

    # Ordenar manualmente según el idVariable
    datos_filtrados = sorted(datos_filtrados, key=lambda x: orden_manual.index(x['idVariable']))
    # Verificar el contenido de datos_filtrados
    if not datos_filtrados:
        print("No se encontraron las variables de interés.")
    else:
        print("Datos filtrados encontrados:", datos_filtrados)

    # Crear la figura
    num_variables = len(datos_filtrados)
    fig, axs = plt.subplots(num_variables, 2, figsize=(12, num_variables * 4))
    fig.suptitle('BCRA Principales Variables', fontsize=18)

    # Fechas de ejemplo (reemplaza con el rango de fechas que necesites)
    desde = '2023-09-16'
    hasta = '2024-09-08'

    # Si hay una sola variable, axs no es una lista, así que lo convertimos en lista
    if num_variables == 1:
        axs = [axs]

    # Crear cada cuadro KPI y gráfico histórico
    for i, variable in enumerate(datos_filtrados):
        ax_kpi, ax_hist = axs[i]

        # Crear KPI
        ax_kpi.axis('off')
        ax_kpi.text(0.05, 0.6, variable['descripcion'], fontsize=14, weight='bold', ha='left')
        ax_kpi.text(0.05, 0.4, f"Valor: {variable['valor']}", fontsize=14, ha='left')
        ax_kpi.text(0.05, 0.2, f"Fecha: {variable['fecha']}", fontsize=14, ha='left')
        ax_kpi.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, edgecolor='black', lw=1))

        # Obtener datos históricos
        datos_historicos = obtener_datos_historicos(variable['idVariable'], desde, hasta)
        if datos_historicos:
            fechas = [pd.to_datetime(dato['fecha']) for dato in datos_historicos]
            valores = [dato['valor'] for dato in datos_historicos]

            # Crear gráfico histórico
            ax_hist.plot(fechas, valores, linestyle='-')
            ax_hist.set_title(f"{variable['descripcion']}")
            ax_hist.grid(True)

            # Formatear las fechas en el eje x para que se muestren agrupadas por mes
            ax_hist.xaxis.set_major_locator(mdates.MonthLocator())
            ax_hist.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

            # Mejorar la legibilidad de las fechas en el eje x
            for label in ax_hist.get_xticklabels():
                label.set_rotation(45)
                label.set_horizontalalignment('right')

            # Añadir etiquetas al eje x e y
            ax_hist.set_xlabel('Mes-Año')
            ax_hist.set_ylabel('Valor')

        else:
            ax_hist.axis('off')
            ax_hist.text(0.5, 0.5, 'Datos históricos no disponibles', ha='center', va='center', fontsize=12)

    # Ajustar el layout
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Guardar la imagen como JPG
    plt.savefig('kpi_report_con_historial.jpg', bbox_inches='tight', dpi=300)
    print("Informe KPI con historial guardado como 'kpi_report_con_historial.jpg'.")

except ConnectionError as e:
    print(f"Error de conexión: {e}")
except requests.RequestException as e:
    print(f"Error al realizar la solicitud: {e}")
except ValueError as e:
    print(f"Error al procesar los datos JSON: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")