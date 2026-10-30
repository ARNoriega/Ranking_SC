import tkinter as tk
from datetime import date
import math
import re
from tkinter import messagebox, ttk

from application.processing_gateway import TopAcumulativoProcessor
from application.ranking_service import RankingService
from application.torneo_service import TorneoService
from database.json_repository import JsonRepository, JsonRepositoryError
from processing.ranking_engine import Torneo
from simulation.runner import crear_demo_torneos


class RankingApp:
    """Prototipo visual minimo para introducir torneos y calcular el ranking."""

    def __init__(
        self,
        root: tk.Tk,
        service: RankingService,
        torneo_service: TorneoService,
    ) -> None:
        self.root = root
        self.service = service
        self.torneo_service = torneo_service
        try:
            self.torneos = torneo_service.cargar_torneos()
        except JsonRepositoryError as error:
            self.torneos = []
            try:
                respaldo = torneo_service.apartar_archivo_corrupto()
            except JsonRepositoryError as reparacion_error:
                messagebox.showerror(
                    "No se pudieron cargar los datos",
                    f"{error}\n\n{reparacion_error}",
                    parent=root,
                )
            else:
                messagebox.showerror(
                    "Datos dañados recuperados",
                    f"{error}\n\nSe ha apartado una copia de respaldo en:\n{respaldo}\n\n"
                    "La aplicación continuará con un archivo de datos nuevo.",
                    parent=root,
                )
        self.indice_edicion: int | None = None
        self.indices_visibles: list[int] = []
        self.ranking_actual: list[tuple[str, float]] = []
        self.nombre_ranking_actual: str | None = None
        self.editando_ranking = False
        self._crear_interfaz()
        self._actualizar_lista_torneos()
        self._actualizar_lista_rankings()

    def _crear_interfaz(self) -> None:
        self.root.title("Rankings - Top Acumulativo")
        ancho_pantalla = self.root.winfo_screenwidth()
        alto_pantalla = self.root.winfo_screenheight()
        ancho = max(520, min(900, int(ancho_pantalla * 0.9)))
        alto = max(500, min(760, int(alto_pantalla * 0.9)))
        self.root.geometry(f"{ancho}x{alto}")
        self.root.minsize(480, 420)
        self.root.resizable(True, True)

        marco_principal = ttk.Frame(self.root)
        marco_principal.pack(fill="both", expand=True)
        marco_principal.columnconfigure(0, weight=1)
        marco_principal.rowconfigure(0, weight=1)

        lienzo = tk.Canvas(marco_principal, highlightthickness=0)
        barra = ttk.Scrollbar(marco_principal, orient="vertical", command=lienzo.yview)
        lienzo.configure(yscrollcommand=barra.set)
        lienzo.grid(row=0, column=0, sticky="nsew")
        barra.grid(row=0, column=1, sticky="ns")

        contenedor = ttk.Frame(lienzo, padding=16)
        ventana_contenedor = lienzo.create_window((0, 0), window=contenedor, anchor="nw")

        def actualizar_desplazamiento(_event=None) -> None:
            lienzo.configure(scrollregion=lienzo.bbox("all"))

        def ajustar_ancho(_event) -> None:
            lienzo.itemconfigure(ventana_contenedor, width=lienzo.winfo_width())

        contenedor.bind("<Configure>", actualizar_desplazamiento)
        lienzo.bind("<Configure>", ajustar_ancho)

        def rueda_raton(_event) -> None:
            lienzo.yview_scroll(-1 if _event.delta > 0 else 1, "units")

        lienzo.bind_all("<MouseWheel>", rueda_raton)
        contenedor.columnconfigure(1, weight=1)
        contenedor.rowconfigure(4, weight=1)
        contenedor.rowconfigure(6, weight=1)

        ttk.Label(contenedor, text="Nombre del torneo").grid(row=0, column=0, sticky="w", pady=4)
        self.nombre = ttk.Entry(contenedor)
        self.nombre.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(contenedor, text="Puntos del torneo").grid(row=1, column=0, sticky="w", pady=4)
        self.puntos = ttk.Entry(contenedor)
        self.puntos.grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(contenedor, text="Año del torneo").grid(row=2, column=0, sticky="w", pady=4)
        self.anho = ttk.Entry(contenedor)
        self.anho.insert(0, str(date.today().year))
        self.anho.grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(contenedor, text="Año del ranking").grid(row=3, column=0, sticky="w", pady=4)
        self.filtro_anho = ttk.Combobox(contenedor, state="readonly")
        self.filtro_anho.bind("<<ComboboxSelected>>", lambda _event: self._actualizar_lista_torneos())
        self.filtro_anho.grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(
            contenedor,
            text="Participantes, uno por linea: seed, jugador",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 4))
        self.participantes = tk.Text(contenedor, height=10, width=60)
        self.participantes.grid(row=5, column=0, columnspan=2, sticky="nsew")

        botones = ttk.Frame(contenedor)
        botones.grid(row=6, column=0, columnspan=2, sticky="ew", pady=10)
        for columna in range(10):
            botones.columnconfigure(columna, weight=1)
        self.boton_torneo = ttk.Button(botones, text="Anadir torneo", command=self.anadir_torneo)
        self.boton_torneo.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(botones, text="Cargar demo", command=self.cargar_demo).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(botones, text="Editar torneo", command=self.editar_torneo).grid(row=0, column=2, sticky="ew", padx=4)
        ttk.Button(botones, text="Eliminar torneo", command=self.eliminar_torneo).grid(row=0, column=3, sticky="ew", padx=4)
        ttk.Button(botones, text="Generar", command=self.generar).grid(row=0, column=4, sticky="ew", padx=4)
        ttk.Button(botones, text="Editar ranking", command=self.editar_ranking).grid(row=0, column=5, sticky="ew", padx=4)
        ttk.Button(botones, text="Guardar ranking", command=self.guardar_ranking).grid(row=0, column=6, sticky="ew", padx=4)
        ttk.Button(
            botones,
            text="Cancelar edicion",
            command=self.cancelar_edicion,
        ).grid(row=0, column=7, sticky="ew", padx=4)
        ttk.Button(botones, text="Limpiar", command=self.limpiar).grid(row=0, column=8, sticky="ew", padx=4)
        ttk.Button(botones, text="Salir", command=self.salir).grid(row=0, column=9, sticky="ew", padx=(4, 0))

        ttk.Label(contenedor, text="Torneos introducidos (Ctrl+Click para varios)").grid(row=7, column=0, sticky="nw")
        self.lista_torneos = tk.Listbox(contenedor, height=8, selectmode=tk.EXTENDED)
        self.lista_torneos.grid(row=7, column=1, sticky="nsew")

        ttk.Label(contenedor, text="Ranking acumulativo").grid(row=8, column=0, columnspan=2, sticky="w", pady=(12, 4))
        self.resultado = tk.Text(contenedor, height=10, state="disabled")
        self.resultado.grid(row=9, column=0, columnspan=2, sticky="nsew")
        contenedor.rowconfigure(9, weight=1)

        ttk.Label(contenedor, text="Rankings guardados").grid(
            row=10, column=0, sticky="nw", pady=(12, 4)
        )
        self.lista_rankings = tk.Listbox(contenedor, height=5, exportselection=False)
        self.lista_rankings.grid(row=11, column=0, sticky="nsew")
        botones_rankings = ttk.Frame(contenedor)
        botones_rankings.grid(row=11, column=1, sticky="new", padx=(8, 0))
        ttk.Button(
            botones_rankings,
            text="Cargar ranking",
            command=self.cargar_ranking_guardado,
        ).pack(fill="x", pady=(0, 4))
        ttk.Button(
            botones_rankings,
            text="Eliminar ranking",
            command=self.eliminar_ranking_guardado,
        ).pack(fill="x")
        contenedor.rowconfigure(11, weight=1)

    def _leer_torneo(self) -> Torneo:
        nombre = self.nombre.get().strip()
        if not nombre:
            raise ValueError("El torneo necesita un nombre")

        try:
            puntos = float(self.puntos.get().strip())
        except ValueError as error:
            raise ValueError("Los puntos deben ser numericos") from error
        try:
            anho = int(self.anho.get().strip())
        except ValueError as error:
            raise ValueError("El año debe ser numerico") from error
        if anho < 1:
            raise ValueError("El año no es valido")

        participantes: list[tuple[int, str]] = []
        seeds: set[int] = set()
        jugadores: set[str] = set()
        for numero_linea, linea in enumerate(self.participantes.get("1.0", "end").splitlines(), 1):
            if not linea.strip():
                continue
            partes = linea.split(",", 1)
            if len(partes) != 2:
                raise ValueError(f"Linea {numero_linea}: usa 'seed, jugador'")
            try:
                seed = int(partes[0].strip())
            except ValueError as error:
                raise ValueError(f"Linea {numero_linea}: seed no valida") from error
            jugador = partes[1].strip()
            if seed < 1 or not jugador:
                raise ValueError(f"Linea {numero_linea}: seed y jugador son obligatorios")
            if seed in seeds or jugador in jugadores:
                raise ValueError(f"Linea {numero_linea}: seed o jugador repetido")
            seeds.add(seed)
            jugadores.add(jugador)
            participantes.append((seed, jugador))

        if not participantes:
            raise ValueError("Introduce al menos un participante")
        if not math.isfinite(puntos) or puntos < 0:
            raise ValueError("Los puntos deben ser un numero finito no negativo")
        torneo = Torneo(puntos, participantes, nombre, anho)
        return torneo

    def _actualizar_lista_torneos(self) -> None:
        self.lista_torneos.delete(0, tk.END)
        anhos = sorted({torneo.anho for torneo in self.torneos})
        valores_filtro = ["Todos"] + [str(anho) for anho in anhos]
        filtro_actual = self.filtro_anho.get()
        self.filtro_anho["values"] = valores_filtro
        self.filtro_anho.set(filtro_actual if filtro_actual in valores_filtro else "Todos")
        self.indices_visibles = []
        for indice, torneo in enumerate(self.torneos):
            if self.filtro_anho.get() != "Todos" and torneo.anho != int(self.filtro_anho.get()):
                continue
            self.indices_visibles.append(indice)
            self.lista_torneos.insert(
                tk.END,
                f"{torneo.nombre} ({torneo.anho}) - {torneo.puntuacion:g} puntos - {len(torneo.participantes)} jugadores",
            )

    def anadir_torneo(self) -> None:
        try:
            torneo = self._leer_torneo()
        except ValueError as error:
            messagebox.showerror("Datos no validos", str(error))
            return
        torneos_existentes = [
            torneo
            for indice, torneo in enumerate(self.torneos)
            if indice != self.indice_edicion
        ]
        if torneo in torneos_existentes:
            messagebox.showwarning(
                "Torneo duplicado",
                "Ese torneo ya esta guardado.",
                parent=self.root,
            )
            return
        if self.indice_edicion is None:
            self.torneos.append(torneo)
        else:
            self.torneos[self.indice_edicion] = torneo
        try:
            self.torneo_service.guardar_torneos(self.torneos)
        except JsonRepositoryError as error:
            messagebox.showerror("No se pudo guardar el torneo", str(error), parent=self.root)
            return
        self._actualizar_lista_torneos()
        self._cancelar_edicion()

    def cargar_demo(self) -> None:
        """Añade las demos que todavía no existen y elimina duplicados exactos."""
        demos = crear_demo_torneos()
        torneos_sin_duplicados = self.torneo_service.quitar_duplicados(self.torneos)
        demos_nuevas = [
            demo for demo in demos
            if demo not in torneos_sin_duplicados
        ]
        torneos_sin_duplicados.extend(demos_nuevas)
        if not demos_nuevas and len(torneos_sin_duplicados) == len(self.torneos):
            messagebox.showinfo(
                "Demo ya cargada",
                "Los torneos demo ya están cargados.",
                parent=self.root,
            )
            return
        self.torneos = torneos_sin_duplicados
        try:
            self.torneo_service.guardar_torneos(self.torneos)
        except JsonRepositoryError as error:
            messagebox.showerror("No se pudo guardar la demo", str(error), parent=self.root)
            return
        self._actualizar_lista_torneos()
        self.calcular_ranking()

    def editar_torneo(self) -> None:
        seleccion = self.lista_torneos.curselection()
        if not seleccion:
            messagebox.showwarning("Sin seleccion", "Selecciona un torneo para editarlo")
            return
        if len(seleccion) > 1:
            messagebox.showwarning(
                "Seleccion multiple",
                "Selecciona un solo torneo para editarlo",
                parent=self.root,
            )
            return
        self.indice_edicion = self.indices_visibles[seleccion[0]]
        torneo = self.torneos[self.indice_edicion]
        self.nombre.delete(0, tk.END)
        self.nombre.insert(0, torneo.nombre)
        self.puntos.delete(0, tk.END)
        self.puntos.insert(0, str(torneo.puntuacion))
        self.anho.delete(0, tk.END)
        self.anho.insert(0, str(torneo.anho))
        self.participantes.delete("1.0", tk.END)
        self.participantes.insert(
            "1.0",
            "\n".join(f"{seed}, {jugador}" for seed, jugador in torneo.participantes),
        )
        self.boton_torneo.configure(text="Actualizar torneo")

    def eliminar_torneo(self) -> None:
        seleccion = self.lista_torneos.curselection()
        if not seleccion:
            messagebox.showwarning("Sin seleccion", "Selecciona un torneo para eliminarlo")
            return
        cantidad = len(seleccion)
        confirmacion = messagebox.askyesno(
            "Confirmar eliminacion",
            f"¿Quieres eliminar {cantidad} torneo(s) seleccionado(s)?",
        )
        if not confirmacion:
            return
        indices = sorted((self.indices_visibles[indice] for indice in seleccion), reverse=True)
        for indice in indices:
            del self.torneos[indice]
        try:
            self.torneo_service.guardar_torneos(self.torneos)
        except JsonRepositoryError as error:
            messagebox.showerror("No se pudo eliminar el torneo", str(error), parent=self.root)
            return
        self._actualizar_lista_torneos()
        self._cancelar_edicion()

    def _cancelar_edicion(self) -> None:
        self.indice_edicion = None
        self.boton_torneo.configure(text="Anadir torneo")
        self.nombre.delete(0, tk.END)
        self.puntos.delete(0, tk.END)
        self.anho.delete(0, tk.END)
        self.anho.insert(0, str(date.today().year))
        self.participantes.delete("1.0", tk.END)

    def _cancelar_edicion_ranking(self) -> None:
        self.editando_ranking = False
        if self.ranking_actual:
            self._mostrar_ranking(self.ranking_actual)
            return
        self.resultado.configure(state="normal")
        self.resultado.delete("1.0", tk.END)
        self.resultado.configure(state="disabled")

    def cancelar_edicion(self) -> None:
        """Descarta los cambios pendientes del formulario o del ranking."""
        if self.indice_edicion is not None:
            self._cancelar_edicion()
        if self.editando_ranking:
            self._cancelar_edicion_ranking()

    def _torneos_del_anho(self) -> list[Torneo]:
        """Devuelve los torneos incluidos en el filtro anual seleccionado."""
        filtro = self.filtro_anho.get()
        if filtro == "Todos" or not filtro:
            return list(self.torneos)
        return [torneo for torneo in self.torneos if torneo.anho == int(filtro)]

    def calcular_ranking(self) -> None:
        torneos = self._torneos_del_anho()
        if not torneos:
            messagebox.showwarning("Sin torneos", "Anade al menos un torneo")
            return
        ranking = self.service.generar_ranking(torneos)
        self.ranking_actual = ranking
        self.nombre_ranking_actual = None
        self.editando_ranking = False
        self._mostrar_ranking(ranking)

    @staticmethod
    def _parsear_ranking(texto: str) -> list[tuple[str, float]]:
        """Convierte las filas editadas de la vista en datos de ranking."""
        ranking = []
        jugadores = set()
        patron = re.compile(r"^\s*\d+\.\s*(.+?):\s*(-?\d+(?:\.\d+)?)\s*$")
        puesto_esperado = 1
        for numero_linea, linea in enumerate(texto.splitlines(), 1):
            if not linea.strip():
                continue
            coincidencia = patron.match(linea)
            if coincidencia is None:
                raise ValueError(f"Linea {numero_linea}: usa 'puesto. jugador: puntuacion'")
            puesto = int(re.match(r"^\s*(\d+)", linea).group(1))
            if puesto != puesto_esperado:
                raise ValueError(
                    f"Linea {numero_linea}: los puestos deben ser consecutivos empezando en 1"
                )
            puesto_esperado += 1
            jugador = coincidencia.group(1).strip()
            puntuacion = float(coincidencia.group(2))
            if not jugador:
                raise ValueError(f"Linea {numero_linea}: el jugador no puede estar vacio")
            if not math.isfinite(puntuacion):
                raise ValueError(f"Linea {numero_linea}: la puntuacion no es valida")
            if jugador in jugadores:
                raise ValueError(f"Linea {numero_linea}: jugador repetido")
            if ranking and puntuacion > ranking[-1][1]:
                raise ValueError(
                    f"Linea {numero_linea}: las puntuaciones deben estar ordenadas de mayor a menor"
                )
            jugadores.add(jugador)
            ranking.append((jugador, puntuacion))
        if not ranking:
            raise ValueError("El ranking no puede estar vacio")
        return ranking

    def editar_ranking(self) -> None:
        if not self.ranking_actual:
            messagebox.showwarning("Sin ranking", "Genera primero un ranking")
            return
        self.editando_ranking = True
        self.resultado.configure(state="normal")
        self.resultado.focus_set()

    def _mostrar_ranking(self, ranking: list[tuple[str, float]]) -> None:
        self.resultado.configure(state="normal")
        self.resultado.delete("1.0", tk.END)
        for puesto, (jugador, puntuacion) in enumerate(ranking, 1):
            self.resultado.insert(tk.END, f"{puesto}. {jugador}: {puntuacion:.4f}\n")
        self.resultado.configure(state="normal" if self.editando_ranking else "disabled")

    def generar(self) -> None:
        """Genera y muestra el ranking acumulativo actual."""
        self.calcular_ranking()

    def limpiar(self) -> None:
        """Limpia el formulario y el resultado sin borrar torneos añadidos."""
        self._cancelar_edicion()
        self.ranking_actual = []
        self.nombre_ranking_actual = None
        self.editando_ranking = False
        self.resultado.configure(state="normal")
        self.resultado.delete("1.0", tk.END)
        self.resultado.configure(state="disabled")

    def salir(self) -> None:
        """Cierra la ventana principal."""
        self.root.destroy()

    def guardar_ranking(self) -> None:
        if self.editando_ranking:
            try:
                ranking = self._parsear_ranking(self.resultado.get("1.0", "end"))
            except ValueError as error:
                messagebox.showerror("Ranking no valido", str(error))
                return
            nombre = self.nombre_ranking_actual or f"ranking_{self.filtro_anho.get()}"
            try:
                existe = nombre in self.service.listar_rankings()
            except JsonRepositoryError as error:
                messagebox.showerror("No se pudo comprobar el ranking", str(error), parent=self.root)
                return
            if existe and not messagebox.askyesno(
                "Confirmar sobrescritura",
                f"El ranking '{nombre}' ya existe. ¿Quieres reemplazarlo?",
                parent=self.root,
            ):
                return
            try:
                self.service.guardar_ranking(
                    ranking,
                    nombre,
                    sobrescribir=existe,
                )
            except (JsonRepositoryError, ValueError, FileExistsError) as error:
                messagebox.showerror("No se pudo guardar el ranking", str(error), parent=self.root)
                return
            self.ranking_actual = ranking
            self.nombre_ranking_actual = nombre
            self.editando_ranking = False
            self.resultado.configure(state="disabled")
            self._actualizar_lista_rankings()
            messagebox.showinfo("Guardado", f"Ranking guardado con {len(ranking)} jugadores")
            return
        torneos = self._torneos_del_anho()
        if not torneos:
            messagebox.showwarning("Sin torneos", "Calcula o anade un torneo primero")
            return
        nombre = f"ranking_{self.filtro_anho.get()}"
        try:
            existe = nombre in self.service.listar_rankings()
        except JsonRepositoryError as error:
            messagebox.showerror("No se pudo comprobar el ranking", str(error), parent=self.root)
            return
        if existe and not messagebox.askyesno(
            "Confirmar sobrescritura",
            f"El ranking '{nombre}' ya existe. ¿Quieres reemplazarlo?",
            parent=self.root,
        ):
            return
        try:
            ranking = self.service.generar_y_guardar(
                torneos,
                nombre,
            ) if not existe else self.service.generar_ranking(torneos)
            if existe:
                self.service.guardar_ranking(ranking, nombre, sobrescribir=True)
        except (JsonRepositoryError, ValueError, FileExistsError) as error:
            messagebox.showerror("No se pudo guardar el ranking", str(error), parent=self.root)
            return
        self.ranking_actual = ranking
        self.nombre_ranking_actual = nombre
        self._mostrar_ranking(ranking)
        self._actualizar_lista_rankings()
        messagebox.showinfo("Guardado", f"Ranking guardado con {len(ranking)} jugadores")

    def _actualizar_lista_rankings(self) -> None:
        try:
            nombres = self.service.listar_rankings()
        except JsonRepositoryError as error:
            messagebox.showerror("No se pudieron cargar los rankings", str(error), parent=self.root)
            return
        self.lista_rankings.delete(0, tk.END)
        for nombre in nombres:
            self.lista_rankings.insert(tk.END, nombre)

    def cargar_ranking_guardado(self) -> None:
        seleccion = self.lista_rankings.curselection()
        if not seleccion:
            messagebox.showwarning(
                "Sin seleccion",
                "Selecciona un ranking guardado para cargarlo",
                parent=self.root,
            )
            return
        nombre = self.lista_rankings.get(seleccion[0])
        try:
            ranking = self.service.cargar_ranking(nombre)
        except JsonRepositoryError as error:
            messagebox.showerror("No se pudo cargar el ranking", str(error), parent=self.root)
            return
        self.ranking_actual = ranking
        self.nombre_ranking_actual = nombre
        self.editando_ranking = False
        self._mostrar_ranking(ranking)

    def eliminar_ranking_guardado(self) -> None:
        seleccion = self.lista_rankings.curselection()
        if not seleccion:
            messagebox.showwarning(
                "Sin seleccion",
                "Selecciona un ranking guardado para eliminarlo",
                parent=self.root,
            )
            return
        nombre = self.lista_rankings.get(seleccion[0])
        if not messagebox.askyesno(
            "Confirmar eliminacion",
            f"¿Quieres eliminar el ranking '{nombre}'?",
            parent=self.root,
        ):
            return
        try:
            self.service.eliminar_ranking(nombre)
        except (JsonRepositoryError, ValueError) as error:
            messagebox.showerror("No se pudo eliminar el ranking", str(error), parent=self.root)
            return
        if self.nombre_ranking_actual == nombre:
            self.ranking_actual = []
            self.nombre_ranking_actual = None
            self.editando_ranking = False
            self.resultado.configure(state="normal")
            self.resultado.delete("1.0", tk.END)
            self.resultado.configure(state="disabled")
        self._actualizar_lista_rankings()


def crear_app() -> RankingApp:
    root = tk.Tk()
    repository = JsonRepository("data/resultados.json")
    service = RankingService(
        repository,
        TopAcumulativoProcessor(),
    )
    return RankingApp(root, service, TorneoService(repository))


if __name__ == "__main__":
    app = crear_app()
    app.root.mainloop()
