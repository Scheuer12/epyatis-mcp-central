"""
Sincroniza o mapa nodal de fontes de dados de config/bootstrap_instances.yaml
para a instância horst-suite no central.db SQLite.
"""

import sys
from pathlib import Path
import yaml

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from central.db.session import get_db_context
from central.db.repository import CentralRepository

def main():
    yaml_path = Path(__file__).resolve().parent.parent / "config" / "bootstrap_instances.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    horst_data = next((i for i in data.get("instances", []) if i.get("slug") == "horst-suite"), None)
    if not horst_data:
        print("Instância horst-suite não encontrada no YAML!")
        return

    ds_map = horst_data.get("data_sources_map", {})
    with get_db_context() as db:
        updated = CentralRepository.update_instance_data_sources_map(db, "horst-suite", ds_map)
        if updated:
            print(f"Sucesso! Mapa de fontes atualizado para {updated.slug}.")
            sources = CentralRepository.get_instance_sources(db, "horst-suite")
            print(f"Total de fontes registradas: {len(sources)}")
            for s in sources:
                print(f" - [{s.get('id')}] {s.get('name')} (system={s.get('system')}, tags={s.get('tags')})")
        else:
            print("Falha ao atualizar instância horst-suite no banco.")

if __name__ == "__main__":
    main()
