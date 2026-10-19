"""Download only pinned CPU pipeline weights, and write an isolated configuration."""
import json
import os
from pathlib import Path

from huggingface_hub import snapshot_download
from mineru.utils.enum_class import ModelPath
from pdf_evidence import MODEL_REVISION


def main():
    paths = [ModelPath.doclayout_yolo, ModelPath.pytorch_paddle, ModelPath.slanet_plus,
             ModelPath.unet_structure, ModelPath.paddle_table_cls, ModelPath.paddle_orientation_classification]
    model_root = snapshot_download(
        "opendatalab/PDF-Extract-Kit-1.0", revision=MODEL_REVISION,
        allow_patterns=[pattern for path in paths for pattern in (path, path + "/*")],
        max_workers=2,
    )
    path = Path(os.environ["MINERU_TOOLS_CONFIG_JSON"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"models-dir": {"pipeline": model_root}}))
    print(f"MinerU pipeline weights ready at revision {MODEL_REVISION}")


if __name__ == "__main__":
    main()
