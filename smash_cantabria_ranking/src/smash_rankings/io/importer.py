import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://api.start.gg/gql/alpha"

# ===============================================
# 1) EXTRAER EL SLUG DE LA URL DEL TORNEO
# ===============================================
def extract_slug(url: str) -> str:
    """
    Convierte una URL de torneo en su slug interno de Start.gg.
    
    Ejemplos válidos:
    https://start.gg/tournament/my-tournament/event/ultimate-singles
    https://www.start.gg/tournament/coimbra-2023/details
    """

    pattern = r"tournament/([^/]+)"
    match = re.search(pattern, url)

    if not match:
        raise ValueError(f"No pude encontrar el slug del torneo en la URL: {url}")

    return match.group(1)


# ===============================================
# 2) QUERY GRAPHQL PARA EXPORTAR EL TORNEO
# ===============================================
QUERY = """
query GetTournamentDeep(
  $slug: String!,
  $perPage: Int = 512,
  $page: Int = 1
) {
  tournament(slug: $slug) {
    id
    name
    city
    addrState
    countryCode
    venueName
    venueAddress
    startAt
    endAt
    url

    events {
      id
      name
      slug
      numEntrants
            videoGame: videogame {
        id
        name
      }

      standings(query: { perPage: $perPage, page: $page }) {
        pageInfo {
          total
          totalPages
          page
          perPage
        }
        nodes {
          placement
          entrant {
            id
            name
            participants {
              id
              gamerTag
            }
          }
        }
      }
    }
  }
}
"""

# ===============================================
# 3) LLAMADA A LA API START.GG
# ===============================================
def fetch_tournament(slug: str, api_key: str):
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "query": QUERY,
        "variables": {
            "slug": slug,
            "perPage": 512,
            "page": 1,
        }
    }

    response = requests.post(API_URL, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"Error HTTP: {response.status_code} → {response.text}")

    data = response.json()

    if "errors" in data:
        raise RuntimeError(f"Error GraphQL: {data['errors']}")

    return data


def infer_tournament_year(api_response: dict) -> int:
    """Extrae el anho del torneo desde `startAt` (epoch seconds) de Start.gg."""
    tournament = api_response.get("data", {}).get("tournament", {})
    start_at = tournament.get("startAt")

    if not isinstance(start_at, int):
        raise RuntimeError(
            "No se pudo obtener `startAt` del torneo para determinar el anho de salida."
        )

    return datetime.fromtimestamp(start_at, tz=timezone.utc).year


def read_text_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def read_dotenv_value(key: str, repo_root: Path) -> str | None:
    """Lee una clave de un archivo .env simple en la raiz del repo."""
    env_path = repo_root / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip()
    return None


def get_default_api_key(repo_root: Path) -> str | None:
    """Resuelve API key por defecto desde entorno o .env."""
    env_key = os.getenv("STARTGG_API_KEY")
    if env_key:
        return env_key.strip()
    dotenv_key = read_dotenv_value("STARTGG_API_KEY", repo_root)
    if dotenv_key:
        return dotenv_key.strip()
    return None


def parse_params_txt(path: str) -> tuple[str, str | None]:
    """Lee URL y API key desde un .txt.

     Formatos soportados:
     1) Dos lineas: URL en la primera, API key en la segunda (opcional).
    2) Key-value:
       url=https://start.gg/tournament/...
         api_key=xxxx (opcional)
    """
    raw = read_text_file(path)
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    kv = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            kv[key.strip().lower()] = value.strip()

    if "url" in kv:
        return kv["url"], kv.get("api_key")

    if len(lines) >= 2:
        return lines[0], lines[1]

    if len(lines) == 1:
        return lines[0], None

    raise RuntimeError(
        "El archivo TXT no contiene datos validos. Usa URL en la primera linea "
        "(API key opcional en segunda) o formato key=value."
    )


def resolve_credentials(args: argparse.Namespace, repo_root: Path) -> tuple[str, str]:
    """Resuelve URL/API key segun el modo seleccionado."""
    default_api_key = get_default_api_key(repo_root)

    if args.modo == "interactive":
        url = input("Introduce la URL del torneo: ").strip()
        api_key_input = input("Introduce la API key de Start.gg (Enter para usar .env): ").strip()
        api_key = api_key_input or default_api_key
        if not api_key:
            raise RuntimeError("No hay API key: indica una por consola o define STARTGG_API_KEY en .env.")
        return url, api_key

    if args.modo == "cli":
        if not args.url:
            raise RuntimeError("En modo 'cli' debes indicar --url.")
        api_key = (args.api_key or default_api_key or "").strip()
        if not api_key:
            raise RuntimeError("En modo 'cli' indica --api-key o define STARTGG_API_KEY en .env.")
        return args.url.strip(), api_key

    # modo == txt
    if args.params_txt:
        url, api_key = parse_params_txt(args.params_txt)
        resolved_api_key = (api_key or default_api_key or "").strip()
        if not resolved_api_key:
            raise RuntimeError("En modo 'txt' falta API key en fichero y no existe STARTGG_API_KEY en .env.")
        return url, resolved_api_key

    if args.url_txt and args.api_key_txt:
        return read_text_file(args.url_txt), read_text_file(args.api_key_txt)

    if args.url_txt:
        url = read_text_file(args.url_txt)
        if not default_api_key:
            raise RuntimeError("Con --url-txt sin --api-key-txt debes definir STARTGG_API_KEY en .env.")
        return url, default_api_key

    raise RuntimeError(
        "En modo 'txt' debes indicar --params-txt o ambos --url-txt y --api-key-txt."
    )


# ===============================================
# 4) PROGRAMA PRINCIPAL
# ===============================================
def main():
    parser = argparse.ArgumentParser(description="Importador de torneos Start.gg a JSON")
    parser.add_argument(
        "--modo",
        choices=["interactive", "cli", "txt"],
        default="interactive",
        help="Fuente de parametros: interactive, cli o txt",
    )

    parser.add_argument("--url", help="URL del torneo (modo cli)")
    parser.add_argument("--api-key", help="API key de Start.gg (modo cli)")

    parser.add_argument(
        "--params-txt",
        help="TXT con url y api_key (dos lineas o key=value) (modo txt)",
    )
    parser.add_argument("--url-txt", help="TXT con la URL del torneo (modo txt)")
    parser.add_argument("--api-key-txt", help="TXT con la API key (modo txt)")

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    url, api_key = resolve_credentials(args, repo_root)

    if not url:
        raise RuntimeError("La URL no puede estar vacia.")
    if not api_key:
        raise RuntimeError("La API key no puede estar vacia.")

    print("Extrayendo slug...")
    slug = extract_slug(url)
    print(f"Slug identificado: {slug}")

    print("Consultando Start.gg ...")
    data = fetch_tournament(slug, api_key)

    tournament_year = infer_tournament_year(data)

    output_dir = repo_root / "data" / "Resultados" / str(tournament_year)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{slug}.json"
    print(f"Guardando JSON en {output_file} ...")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✔ Exportación completada con éxito.")


if __name__ == "__main__":
    main()