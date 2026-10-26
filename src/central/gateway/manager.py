"""
Gerenciador central de instâncias e carregamento de configurações a partir do banco de dados SQLite.
"""

from pathlib import Path
import logging
import yaml

from central.db.repository import CentralRepository
from central.db.session import get_db_context
from central.gateway.instance_gateway import InstanceGateway
from central.models import CentralBootstrapConfig

logger = logging.getLogger(__name__)


class GatewayManager:
    def __init__(self):
        self.instances: dict[str, InstanceGateway] = {}

    def load_from_db(self) -> None:
        """Carrega todas as instâncias ativas cadastradas no SQLite."""
        try:
            with get_db_context() as db:
                configs = CentralRepository.load_instance_configs_from_db(db)
                if not configs:
                    logger.warning("Nenhuma instância ativa encontrada no banco SQLite.")
                    return

                for inst_config in configs:
                    gateway = InstanceGateway(inst_config)
                    self.instances[inst_config.slug] = gateway
                    logger.info(f"Instância carregada do DB: '{inst_config.name}' (slug: {inst_config.slug})")
        except Exception as e:
            logger.error(f"Erro ao carregar instâncias do banco SQLite: {e}", exc_info=True)

    def load_config(self, yaml_path: Path) -> None:
        """Fallback: carrega a partir do arquivo YAML caso o banco de dados esteja inacessível."""
        if not yaml_path.exists():
            logger.warning(f"Arquivo de configuração não encontrado em: {yaml_path}")
            return

        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)

            config = CentralBootstrapConfig.model_validate(raw_data)
            for inst_config in config.instances:
                gateway = InstanceGateway(inst_config)
                self.instances[inst_config.slug] = gateway
                logger.info(f"Instância carregada do YAML: '{inst_config.name}' (slug: {inst_config.slug})")
        except Exception as e:
            logger.error(f"Erro ao carregar instâncias do YAML: {e}", exc_info=True)

    async def reload_instance(self, slug: str) -> bool:
        """Recarrega uma instância específica do banco de dados sem derrubar as demais."""
        logger.info(f"Recarregando instância '{slug}'...")
        old_gateway = self.instances.get(slug)
        if old_gateway:
            try:
                await old_gateway.stop()
            except Exception as e:
                logger.warning(f"Erro ao parar gateway antigo de '{slug}': {e}")

        with get_db_context() as db:
            configs = CentralRepository.load_instance_configs_from_db(db)
            matching = [c for c in configs if c.slug == slug]
            if not matching:
                if slug in self.instances:
                    del self.instances[slug]
                return False

            new_gateway = InstanceGateway(matching[0])
            await new_gateway.start()
            self.instances[slug] = new_gateway
            logger.info(f"Instância '{slug}' recarregada com sucesso.")
            return True

    async def start_all(self) -> None:
        for slug, gateway in self.instances.items():
            await gateway.start()

    async def stop_all(self) -> None:
        for slug, gateway in self.instances.items():
            await gateway.stop()

    def get_instance(self, slug: str) -> InstanceGateway | None:
        return self.instances.get(slug)


gateway_manager = GatewayManager()
