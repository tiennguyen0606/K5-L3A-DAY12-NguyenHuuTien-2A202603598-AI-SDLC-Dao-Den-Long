from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from .simulation import Simulation


class ContractInputError(ValueError):
    pass


def _read_json(path: str | None, label: str) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContractInputError(f"Invalid {label} file: {error}") from error
    if not isinstance(value, dict):
        raise ContractInputError(f"Invalid {label} file: root must be an object")
    return value


def _validate_inputs(data: dict[str, Any]) -> list[dict[str, Any]]:
    frames = data.get("frames", [])
    if not isinstance(frames, list):
        raise ContractInputError("Invalid inputs file: frames must be an array")
    last_tick = -1
    for frame in frames:
        if not isinstance(frame, dict) or not isinstance(frame.get("tick"), int):
            raise ContractInputError("Invalid inputs file: every frame needs an integer tick")
        if frame["tick"] <= last_tick:
            raise ContractInputError("Invalid inputs file: frame ticks must increase strictly")
        move = frame.get("move")
        if move is not None and (not isinstance(move, list) or len(move) != 2 or any(not isinstance(value, (int, float)) or value < -1 or value > 1 for value in move)):
            raise ContractInputError("Invalid inputs file: move must contain two numbers in [-1, 1]")
        for action in ("jump", "interact", "pulse", "dash", "pause"):
            if action in frame and not isinstance(frame[action], bool):
                raise ContractInputError(f"Invalid inputs file: {action} must be boolean")
        last_tick = frame["tick"]
    return frames


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dao Den Long deterministic headless runner")
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--night", required=True, type=int)
    parser.add_argument("--scenario")
    parser.add_argument("--inputs")
    parser.add_argument("--ticks", required=True, type=int)
    parser.add_argument("--out", required=True)
    parser.add_argument("--snapshot-every", type=int, default=10)
    return parser


def run(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.ticks < 0 or args.snapshot_every <= 0:
            raise ContractInputError("ticks must be non-negative and snapshot-every must be positive")
        scenario = _read_json(args.scenario, "scenario")
        frames = _validate_inputs(_read_json(args.inputs, "inputs"))
        simulation = Simulation(args.seed, args.night, scenario)
    except (ContractInputError, ValueError, TypeError, KeyError) as error:
        print(error, file=sys.stderr)
        return 2

    output: list[dict[str, Any]] = [simulation.snapshot()]
    controls: dict[str, Any] = {"move": [0, 0], "cam_yaw_deg": 0, "jump": False, "interact": False, "pulse": False, "dash": False, "pause": False}
    frame_index = 0
    for step_tick in range(args.ticks):
        while frame_index < len(frames) and frames[frame_index]["tick"] == step_tick:
            controls.update({key: value for key, value in frames[frame_index].items() if key != "tick"})
            frame_index += 1
        output.extend(simulation.step(controls))
        if simulation.tick % args.snapshot_every == 0:
            output.append(simulation.snapshot())
        if simulation.state in ("won", "lost"):
            break
    output.append({"type": "end", "ticks": simulation.tick, "state": simulation.state, "score": simulation.score})
    try:
        Path(args.out).write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in output), encoding="utf-8")
    except OSError as error:
        print(f"Could not write output: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
