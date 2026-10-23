from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_SCRIPTS_ROOT = Path(__file__).resolve().parents[1]
_APP_ROOT = Path(__file__).resolve().parents[2]
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))
if str(_APP_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_APP_ROOT / "src"))

from operations.gates import AREAS, STAGES, run_all_areas_stage, run_area_stage
from operations.gates.python_area import ensure_project_python


def main() -> None:
    parser = argparse.ArgumentParser(description="OTRS Google Chat Quality Gate")
    parser.add_argument(
        "--area",
        choices=[*AREAS, "all"],
        default="all",
        help="Area tecnologica (default: all para todas as categorias)",
    )
    parser.add_argument(
        "--stage",
        required=True,
        choices=list(STAGES),
        help="Stage to execute",
    )
    parser.add_argument(
        "--coverage-fail-under",
        type=int,
        default=100,
        help="Minimum coverage percentage",
    )
    parser.add_argument(
        "--light-clean",
        action="store_true",
        help="Limpa apenas caches sem remover artefatos de build",
    )
    args = parser.parse_args()
    area = args.area
    if area in {"python", "all"} and args.stage in {
        "lint",
        "test",
        "pytest",
        "security",
        "clean",
        "validate",
        "build",
    }:
        ensure_project_python(args.stage if args.stage != "pytest" else "test")
    if area == "all" and args.stage != "clean":
        run_all_areas_stage(
            args.stage,
            coverage_fail_under=args.coverage_fail_under,
            app_root=_APP_ROOT,
        )
    else:
        target_area = "python" if area == "all" else area
        os.chdir(_APP_ROOT if target_area == "python" else _APP_ROOT.parent)
        run_area_stage(
            target_area,
            args.stage,
            coverage_fail_under=args.coverage_fail_under,
            light_clean=args.light_clean,
        )
    print("\n[SUCESSO] Estagio concluido com sucesso.")


if __name__ == "__main__":
    main()
