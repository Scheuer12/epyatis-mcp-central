"""
Ponto de entrada para execução do Epyatis MCP Central.
"""

import uvicorn
from central.config import settings


def run():
    uvicorn.run(
        "central.server:app",
        host=settings.CENTRAL_HOST,
        port=settings.CENTRAL_PORT,
        reload=settings.CENTRAL_DEBUG,
    )


if __name__ == "__main__":
    run()
