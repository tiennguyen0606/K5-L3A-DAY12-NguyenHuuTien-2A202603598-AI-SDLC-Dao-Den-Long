from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any


TICK_RATE = 60


@dataclass
class Player:
    pos: list[float]
    carried: int = 0
    flames: int = 3
    invuln_ticks: int = 0
    pulse_cd_ticks: int = 0


@dataclass
class Lantern:
    id: str
    pos: list[float]
    deposited: int = 0
    lit: bool = False


@dataclass
class Mote:
    id: str
    pos: list[float]
    kind: str = "random"
    ttl_ticks: int | None = None


@dataclass
class Shade:
    id: str
    pos: list[float]
    state: str = "chase"
    state_ticks_left: int = 0


NIGHT1_LANTERNS = [
    ("L1", [0.0, 0.0, 25.0]),
    ("L2", [23.8, 0.0, 7.7]),
    ("L3", [14.7, 0.0, -20.2]),
    ("L4", [-14.7, 0.0, -20.2]),
    ("L5", [-23.8, 0.0, 7.7]),
]


def _xz_distance(a: list[float], b: list[float]) -> float:
    return math.hypot(a[0] - b[0], a[2] - b[2])


def _distance3(a: list[float], b: list[float]) -> float:
    return math.sqrt(sum((a[index] - b[index]) ** 2 for index in range(3)))


def _rounded_pos(pos: list[float]) -> list[float]:
    return [round(value, 3) for value in pos]


class Simulation:
    """Fixed-step, renderer-independent game simulation.

    The renderer is deliberately a consumer of snapshots. Hidden tests can therefore
    exercise exactly the same rules without a window, GPU, or wall-clock timing.
    """

    tuning = {
        "player_speed": 6.0,
        "carry_capacity": 10,
        "lantern_cost": 10,
        "pickup_radius": 1.0,
        "interact_radius": 2.0,
        "pulse_cost": 3,
        "pulse_radius": 5.0,
        "night1_duration_s": 300,
        "flames": 3,
        "invuln_s": 1.5,
        "hit_drop_ratio": 0.5,
        "pulse_stun_s": 2.0,
        "pulse_push_m": 4.0,
        "pulse_cooldown_s": 3.0,
        "safe_radius": 6.0,
        "shade_speed": 4.0,
        "shade_hit_radius": 1.0,
        "score": {
            "per_mote": 10,
            "per_lantern": 100,
            "per_stun": 5,
            "per_second_left": 2,
            "per_flame_left": 50,
        },
    }

    def __init__(self, seed: int, night: int = 1, scenario: dict[str, Any] | None = None):
        if night != 1:
            raise ValueError("Phase 1 supports only night 1")
        self.seed = seed
        self.night = night
        self.rng = random.Random(seed)
        self.tick = 0
        self.sim_tick = 0
        self.state = "playing"
        self.score = 0
        self.time_left_s = float(self.tuning["night1_duration_s"])
        self.player = Player([0.0, 0.0, 0.0], flames=self.tuning["flames"])
        self.lanterns = [Lantern(identifier, pos.copy()) for identifier, pos in NIGHT1_LANTERNS]
        self.motes: list[Mote] = []
        self.shades: list[Shade] = []
        self._next_mote_id = 1
        self._next_shade_id = 1
        self._previous_input = {"interact": False, "pulse": False, "jump": False}
        self._load_defaults()
        self._apply_scenario(scenario or {})

    def _load_defaults(self) -> None:
        points = []
        for radius, count in ((12.0, 8), (33.0, 16)):
            for index in range(count):
                angle = math.tau * index / count
                points.append([radius * math.cos(angle), 0.0, radius * math.sin(angle)])
        self.rng.shuffle(points)
        for pos in points[:20]:
            self._add_mote(pos)

    def _add_mote(self, pos: list[float], kind: str = "random", ttl_ticks: int | None = None) -> None:
        self.motes.append(Mote(f"M{self._next_mote_id}", [float(v) for v in pos], kind, ttl_ticks))
        self._next_mote_id += 1

    def _apply_scenario(self, scenario: dict[str, Any]) -> None:
        player = scenario.get("player", {})
        if "pos" in player:
            self.player.pos = [float(v) for v in player["pos"]]
        self.player.carried = int(player.get("carried", self.player.carried))
        self.player.flames = int(player.get("flames", self.player.flames))
        if "time_left_s" in scenario:
            self.time_left_s = float(scenario["time_left_s"])
        if scenario.get("random_motes") is False or "motes" in scenario:
            self.motes = []
        for pos in scenario.get("motes", []):
            self._add_mote(pos)
        if scenario.get("random_shades") is False or "shades" in scenario:
            self.shades = []
        for item in scenario.get("shades", []):
            identifier = item.get("id", f"S{self._next_shade_id}")
            self.shades.append(Shade(identifier, [float(v) for v in item["pos"]]))
            self._next_shade_id += 1
        by_id = {lantern.id: lantern for lantern in self.lanterns}
        for item in scenario.get("lanterns", []):
            lantern = by_id.get(item["id"])
            if lantern is None:
                continue
            if "pos" in item:
                lantern.pos = [float(v) for v in item["pos"]]
            lantern.deposited = int(item.get("deposited", lantern.deposited))
            lantern.lit = bool(item.get("lit", lantern.deposited >= self.tuning["lantern_cost"]))

    def _pressed(self, action: str, controls: dict[str, Any]) -> bool:
        return bool(controls.get(action, self._previous_input.get(action, False))) and not self._previous_input.get(action, False)

    def _move_player(self, controls: dict[str, Any]) -> None:
        move = controls.get("move", [0.0, 0.0])
        x, z = float(move[0]), float(move[1])
        magnitude = math.hypot(x, z)
        if magnitude > 1:
            x, z = x / magnitude, z / magnitude
        yaw = math.radians(float(controls.get("cam_yaw_deg", 0.0)))
        world_x = x * math.cos(yaw) + z * math.sin(yaw)
        world_z = -x * math.sin(yaw) + z * math.cos(yaw)
        distance = self.tuning["player_speed"] / TICK_RATE
        self.player.pos[0] += world_x * distance
        self.player.pos[2] += world_z * distance

    def _pickup_motes(self, events: list[dict[str, Any]]) -> None:
        for mote in list(self.motes):
            if self.player.carried >= self.tuning["carry_capacity"]:
                break
            if abs(self.player.pos[1] - mote.pos[1]) <= 1.5 and _xz_distance(self.player.pos, mote.pos) <= self.tuning["pickup_radius"]:
                self.motes.remove(mote)
                self.player.carried += 1
                events.append(self._event("mote_picked", {"carried": self.player.carried}))

    def _deposit(self, events: list[dict[str, Any]]) -> None:
        candidates = [lantern for lantern in self.lanterns if not lantern.lit and _xz_distance(self.player.pos, lantern.pos) <= self.tuning["interact_radius"]]
        if not candidates or self.player.carried <= 0:
            return
        lantern = min(candidates, key=lambda item: (_xz_distance(self.player.pos, item.pos), item.id))
        amount = min(self.player.carried, self.tuning["lantern_cost"] - lantern.deposited)
        lantern.deposited += amount
        self.player.carried -= amount
        self.score += amount * self.tuning["score"]["per_mote"]
        events.append(self._event("deposit", {"lantern_id": lantern.id, "amount": amount, "deposited": lantern.deposited}))
        if lantern.deposited >= self.tuning["lantern_cost"]:
            lantern.lit = True
            self.score += self.tuning["score"]["per_lantern"]
            events.append(self._event("lantern_lit", {"lantern_id": lantern.id}))

    def _pulse(self, events: list[dict[str, Any]]) -> None:
        if self.player.carried < self.tuning["pulse_cost"] or self.player.pulse_cd_ticks > 0:
            return
        self.player.carried -= self.tuning["pulse_cost"]
        self.player.pulse_cd_ticks = round(self.tuning["pulse_cooldown_s"] * TICK_RATE)
        centre = [self.player.pos[0], self.player.pos[1] + 0.8, self.player.pos[2]]
        stunned = []
        for shade in sorted(self.shades, key=lambda item: item.id):
            if _distance3(centre, shade.pos) <= self.tuning["pulse_radius"]:
                shade.state = "stunned"
                shade.state_ticks_left = round(self.tuning["pulse_stun_s"] * TICK_RATE)
                stunned.append(shade.id)
        self.score += len(stunned) * self.tuning["score"]["per_stun"]
        events.append(self._event("pulse", {"stunned_ids": stunned}))

    def _update_shades(self, events: list[dict[str, Any]]) -> None:
        for shade in sorted(self.shades, key=lambda item: item.id):
            if shade.state == "stunned":
                shade.state_ticks_left -= 1
                if shade.state_ticks_left <= 0:
                    shade.state = "chase"
                continue
            distance = _xz_distance(shade.pos, self.player.pos)
            if distance > 0:
                step = min(self.tuning["shade_speed"] / TICK_RATE, distance)
                shade.pos[0] += (self.player.pos[0] - shade.pos[0]) / distance * step
                shade.pos[2] += (self.player.pos[2] - shade.pos[2]) / distance * step
            if self.player.invuln_ticks == 0 and _xz_distance(shade.pos, self.player.pos) <= self.tuning["shade_hit_radius"] and abs(shade.pos[1] - self.player.pos[1]) <= 1.5:
                dropped = self.player.carried // 2
                self.player.carried -= dropped
                self.player.flames -= 1
                self.player.invuln_ticks = round(self.tuning["invuln_s"] * TICK_RATE)
                for index in range(dropped):
                    angle = self.rng.random() * math.tau
                    radius = self.rng.uniform(1.5, 2.5)
                    self._add_mote([self.player.pos[0] + math.cos(angle) * radius, self.player.pos[1], self.player.pos[2] + math.sin(angle) * radius], "dropped", 480)
                events.append(self._event("player_hit", {"by": "shade", "flames": self.player.flames, "dropped": dropped}))
                break

    def _event(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"type": "event", "tick": self.tick + 1, "name": name, "data": data}

    def step(self, controls: dict[str, Any]) -> list[dict[str, Any]]:
        if self.state != "playing":
            return []
        events: list[dict[str, Any]] = []
        if self.player.invuln_ticks > 0:
            self.player.invuln_ticks -= 1
        if self.player.pulse_cd_ticks > 0:
            self.player.pulse_cd_ticks -= 1
        self._move_player(controls)
        self._pickup_motes(events)
        if self._pressed("interact", controls):
            self._deposit(events)
        if self._pressed("pulse", controls):
            self._pulse(events)
        self._update_shades(events)
        self.tick += 1
        self.sim_tick += 1
        self.time_left_s = max(0.0, self.time_left_s - 1 / TICK_RATE)
        if self.player.flames <= 0:
            self.state = "lost"
            events.append({"type": "event", "tick": self.tick, "name": "game_over", "data": {"result": "lost", "reason": "no_flames"}})
        elif all(lantern.lit for lantern in self.lanterns):
            self.state = "won"
            self.score += math.floor(self.time_left_s) * 2 + self.player.flames * 50
            events.append({"type": "event", "tick": self.tick, "name": "game_over", "data": {"result": "won", "reason": "all_lit"}})
        elif self.time_left_s <= 0:
            self.state = "lost"
            events.append({"type": "event", "tick": self.tick, "name": "game_over", "data": {"result": "lost", "reason": "dawn"}})
        for action in self._previous_input:
            self._previous_input[action] = bool(controls.get(action, self._previous_input[action]))
        return events

    def snapshot(self) -> dict[str, Any]:
        return {
            "type": "snapshot",
            "tick": self.tick,
            "sim_tick": self.sim_tick,
            "state": self.state,
            "time_left_s": round(self.time_left_s, 3),
            "score": self.score,
            "player": {"pos": _rounded_pos(self.player.pos), "flames": self.player.flames, "carried": self.player.carried},
            "lanterns": [{"id": item.id, "pos": _rounded_pos(item.pos), "lit": item.lit, "deposited": item.deposited} for item in self.lanterns],
            "shades": [{"id": item.id, "pos": _rounded_pos(item.pos), "state": item.state} for item in self.shades],
            "motes_active": len(self.motes),
            "motes": [{"id": item.id, "pos": _rounded_pos(item.pos)} for item in self.motes],
        }
