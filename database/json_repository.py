import json
from datetime import datetime
from pathlib import Path
from typing import Any


class JsonRepositoryError(Exception):
    """Error legible para problemas con el archivo JSON."""


class JsonRepository:
    """Persistencia sencilla de resultados en un archivo JSON."""

    def __init__(self, path: str | Path = "data/resultados.json") -> None:
        self.path = Path(path)

    def save(self, data: dict[str, Any]) -> None:
        temporal = self.path.with_name(f".{self.path.name}.tmp")
        try:
            contenido = json.dumps(data, ensure_ascii=False, indent=2)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporal.write_text(contenido, encoding="utf-8")
            temporal.replace(self.path)
        except (TypeError, ValueError) as error:
            raise JsonRepositoryError(
                f"No se pudieron preparar los datos para guardar '{self.path.name}'. "
                "Hay información que no se puede convertir a JSON."
            ) from error
        except OSError as error:
            raise JsonRepositoryError(
                f"No se pudo guardar '{self.path.name}'. "
                "Comprueba los permisos, que el archivo no esté abierto en otro programa "
                "y que haya espacio disponible."
            ) from error
        finally:
            try:
                if temporal.exists():
                    temporal.unlink()
            except OSError:
                pass

    def apartar_archivo_corrupto(self) -> Path | None:
        """Mueve el JSON dañado a una copia de respaldo y deja libre su ruta."""
        if not self.path.exists():
            return None
        marca_tiempo = datetime.now().strftime("%Y%m%d-%H%M%S")
        respaldo = self.path.with_name(
            f"{self.path.stem}.corrupto-{marca_tiempo}{self.path.suffix}"
        )
        try:
            self.path.replace(respaldo)
        except OSError as error:
            raise JsonRepositoryError(
                f"No se pudo apartar el archivo dañado '{self.path.name}'."
            ) from error
        return respaldo

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            contenido = self.path.read_text(encoding="utf-8")
            datos = json.loads(contenido)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
            raise JsonRepositoryError(
                f"No se puede leer '{self.path.name}'. "
                "El archivo de datos parece estar dañado. "
                "Puedes corregirlo o apartarlo y volver a iniciar la aplicación."
            ) from error
        if not isinstance(datos, dict):
            raise JsonRepositoryError(
                f"El archivo '{self.path.name}' no contiene un formato de datos valido."
            )
        return datos
