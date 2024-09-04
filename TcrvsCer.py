import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from requests.exceptions import ConnectionError

def obtener_datos_historicos(id_variable, desde, hasta):
    url = f"https://api.bcra.gob.ar/estadisticas/v2.0/DatosVariable/{id_variable}/{desde}/{hasta}"
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()

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
        5: "TC Mayorista",  # Tipo de cambio minorista
        31: "CER",          # Índice CER
    }

    # Fechas de ejemplo (reemplaza con el rango de fechas que necesites)
    desde = '2023-09-04'
    hasta = '2024-09-04'

    # Obtener datos históricos para el TC Minorista y el CER
    datos_tc = obtener_datos_historicos(5, desde, hasta)  # Tipo de cambio minorista
    datos_cer = obtener_datos_historicos(31, desde, hasta)  # Índice CER

    # Verificar que se obtuvieron datos para ambos indicadores
    if not datos_tc or not datos_cer:
        raise ValueError("No se pudieron obtener los datos históricos necesarios.")

    # Convertir los datos a DataFrames para facilitar el procesamiento
    df_tc = pd.DataFrame(datos_tc).sort_values('fecha')
    df_cer = pd.DataFrame(datos_cer).sort_values('fecha')

    # Asegurarse de que las fechas están en el mismo formato y unir los DataFrames
    df_tc['fecha'] = pd.to_datetime(df_tc['fecha'])
    df_cer['fecha'] = pd.to_datetime(df_cer['fecha'])

    # Unir los DataFrames por la columna 'fecha'
    df_merged = pd.merge(df_tc, df_cer, on='fecha', suffixes=('_tc', '_cer'))

    # Obtener el valor del CER en la fecha final
    cer_final = df_merged['valor_cer'].iloc[-1]

    # Calcular el valor deflactado del tipo de cambio usando el CER final
    df_merged['valor_deflactado'] = df_merged['valor_tc'] / df_merged['valor_cer'] * cer_final

    # Graficar el tipo de cambio nominal y deflactado
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df_merged['fecha'], df_merged['valor_tc'], label="Tipo de Cambio Nominal", color="blue")
    ax.plot(df_merged['fecha'], df_merged['valor_deflactado'], label="Tipo de Cambio Deflactado (CER)", color="red", linestyle="--")

    # Anotar los valores de comienzo y final para cada serie
    ax.annotate(f'{df_merged["valor_tc"].iloc[0]:.2f}',
                xy=(df_merged['fecha'].iloc[0], df_merged['valor_tc'].iloc[0]),
                xytext=(-20, 10), textcoords='offset points', color="blue", weight='bold')

    ax.annotate(f'{df_merged["valor_tc"].iloc[-1]:.2f}',
                xy=(df_merged['fecha'].iloc[-1], df_merged['valor_tc'].iloc[-1]),
                xytext=(10, 0), textcoords='offset points', color="blue", weight='bold')

    ax.annotate(f'{df_merged["valor_deflactado"].iloc[0]:.2f}',
                xy=(df_merged['fecha'].iloc[0], df_merged['valor_deflactado'].iloc[0]),
                xytext=(-20, 10), textcoords='offset points', color="red", weight='bold')

    ax.annotate(f'{df_merged["valor_deflactado"].iloc[-1]:.2f}',
                xy=(df_merged['fecha'].iloc[-1], df_merged['valor_deflactado'].iloc[-1]),
                xytext=(10, 0), textcoords='offset points', color="red", weight='bold')

    # Formatear las fechas en el eje x
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.autofmt_xdate()

    # Etiquetas y título
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Valor')
    ax.set_title('Tipo de Cambio Nominal vs. Deflactado (CER)')
    ax.legend()

    # Mostrar la gráfica
    plt.grid(True)
    plt.show()

    # Guardar la imagen como JPG
    plt.savefig('tc_nominal_vs_deflactado.jpg', bbox_inches='tight', dpi=300)
    print("Informe guardado como 'tc_nominal_vs_deflactado.jpg'.")

except ConnectionError as e:
    print(f"Error de conexión: {e}")
except requests.RequestException as e:
    print(f"Error al realizar la solicitud: {e}")
except ValueError as e:
    print(f"Error al procesar los datos: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")