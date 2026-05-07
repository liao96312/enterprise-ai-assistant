from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import settings
from app.rag import ingest_documents


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else settings.raw_data_dir
    result = ingest_documents(target, reset=True)
    mode = f"{result.vector_store} / {result.embedding_provider} embedding"
    print(
        f"success: documents={result.documents}, chunks={result.chunks}, mode={mode}"
    )


if __name__ == "__main__":
    main()
