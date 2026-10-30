from simulation.runner import crear_muestras, ejecutar_simulacion, guardar_grafica


if __name__ == "__main__":
    datos = ejecutar_simulacion(crear_muestras())
    guardar_grafica(datos)
    print(datos)
