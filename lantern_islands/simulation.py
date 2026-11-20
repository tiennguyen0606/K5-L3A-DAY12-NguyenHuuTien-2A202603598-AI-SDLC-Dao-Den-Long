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
    vel: list[float] | None = None
    grounded: bool = True
    dash_cd_ticks: int = 0
    dash_ticks: int = 0
    charm_ticks: int = 0
    facing: list[float] | None = None
    respawn_ticks: int = 0


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
    push_ticks: int = 0
    push_dir: list[float] | None = None


@dataclass
class Drifter:
    id: str
    pos: list[float]
    state: str = "idle"
    stolen: int = 0
    state_ticks_left: int = 0


@dataclass
class Charm:
    id: str
    pos: list[float]
    available: bool = True
    respawn_ticks: int = 0


NIGHT1_LANTERNS = [
    ("L1", [0.0, 0.0, 25.0]),
    ("L2", [23.8, 0.0, 7.7]),
    ("L3", [14.7, 0.0, -20.2]),
    ("L4", [-14.7, 0.0, -20.2]),
    ("L5", [-23.8, 0.0, 7.7]),
]

NIGHT2_LANTERNS = [
    ("L1", [0.0, 0.0, 20.0]), ("L2", [17.0, 0.0, -10.0]),
    ("L3", [-17.0, 0.0, -10.0]), ("L4", [70.0, 0.0, 20.0]),
    ("L5", [87.0, 0.0, -10.0]), ("L6", [53.0, 0.0, -10.0]),
]
NIGHT3_LANTERNS = [
    ("L1", [0.0, 6.0, 6.0]), ("L2", [18.0, 3.0, 10.0]),
    ("L3", [-18.0, 3.0, 10.0]), ("L4", [35.0, 0.0, -10.0]),
    ("L5", [-35.0, 0.0, -10.0]), ("L6", [20.0, 0.0, -35.0]),
    ("L7", [-20.0, 0.0, -35.0]),
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
        "dash_speed": 14.0,
        "dash_duration_s": 0.2,
        "dash_cooldown_s": 1.5,
        "carry_capacity": 10,
        "lantern_cost": 10,
        "pickup_radius": 1.0,
        "interact_radius": 2.0,
        "pulse_cost": 3,
        "pulse_radius": 5.0,
        "night1_duration_s": 300,
        "night2_duration_s": 330,
        "night3_duration_s": 360,
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
        if night not in (1, 2, 3):
            raise ValueError("night must be 1, 2, or 3")
        self.seed = seed
        self.night = night
        self.rng = random.Random(seed)
        self.tick = 0
        self.sim_tick = 0
        self.state = "playing"
        self.paused = False
        self.score = 0
        self.time_left_s = float(self.tuning[f"night{night}_duration_s"])
        self.player = Player([0.0, 0.0, 0.0], flames=self.tuning["flames"], vel=[0.0, 0.0, 0.0], facing=[0.0, 1.0])
        layouts = {1: NIGHT1_LANTERNS, 2: NIGHT2_LANTERNS, 3: NIGHT3_LANTERNS}
        self.lanterns = [Lantern(identifier, pos.copy()) for identifier, pos in layouts[night]]
        self.motes: list[Mote] = []
        self.shades: list[Shade] = []
        self.drifters: list[Drifter] = []
        charm_layouts = {1: [], 2: [("C1", [35.0, 0.0, 0.0])], 3: [("C1", [30.0, 0.0, 25.0]), ("C2", [-30.0, 0.0, 25.0])]}
        self.charms = [Charm(identifier, pos) for identifier, pos in charm_layouts[night]]
        self.wind = {"active": False, "dir_deg": 0.0}
        self._next_mote_id = 1
        self._next_shade_id = 1
        self._next_drifter_id = 1
        self.random_motes = True
        self.random_shades = True
        self.random_drifters = night in (2, 3)
        self._previous_input = {"interact": False, "pulse": False, "jump": False, "dash": False, "pause": False}
        self._load_defaults()
        self._apply_scenario(scenario or {})

    def _load_defaults(self) -> None:
        points: list[list[float]] = []
        rings = {1: ((12.0, 8, 0.0, 0.0), (33.0, 16, 0.0, 0.0)), 2: ((10.0, 4, 0.0, 0.0), (22.0, 8, 0.0, 0.0)), 3: ((34.0, 18, 0.0, 0.0), (18.0, 8, 3.0, 20.0), (5.0, 4, 6.0, 45.0))}[self.night]
        for radius, count, height, offset_deg in rings:
            for index in range(count):
                angle = math.radians(offset_deg) + math.tau * index / count
                points.append([radius * math.cos(angle), height, radius * math.sin(angle)])
                if self.night == 2:
                    points.append([70.0 + radius * math.cos(angle), height, radius * math.sin(angle)])
        self.mote_spawn_points = points
        initial = points.copy()
        self.rng.shuffle(initial)
        for pos in initial[:20]:
            self._add_mote(pos)
        if self.night == 1:
            self.shade_spawn_points = [[37 * math.cos(math.radians(15 + 30 * index)), 0.0, 37 * math.sin(math.radians(15 + 30 * index))] for index in range(12)]
        elif self.night == 2:
            self.shade_spawn_points = [[centre + 26 * math.cos(math.radians(22.5 + 45 * index)), 0.0, 26 * math.sin(math.radians(22.5 + 45 * index))] for centre in (0.0, 70.0) for index in range(8)]
        else:
            self.shade_spawn_points = [[43 * math.cos(math.radians(22.5 * index)), 0.0, 43 * math.sin(math.radians(22.5 * index))] for index in range(16)]

    def _add_mote(self, pos: list[float], kind: str = "random", ttl_ticks: int | None = None) -> None:
        self.motes.append(Mote(f"M{self._next_mote_id}", [float(v) for v in pos], kind, ttl_ticks))
        self._next_mote_id += 1

    def _apply_scenario(self, scenario: dict[str, Any]) -> None:
        self.random_motes = bool(scenario.get("random_motes", self.random_motes))
        self.random_shades = bool(scenario.get("random_shades", self.random_shades))
        self.random_drifters = bool(scenario.get("random_drifters", self.random_drifters))
        player = scenario.get("player", {})
        if "pos" in player:
            self.player.pos = [float(v) for v in player["pos"]]
        self.player.carried = int(player.get("carried", self.player.carried))
        self.player.flames = int(player.get("flames", self.player.flames))
        self.player.invuln_ticks = int(player.get("invuln_ticks", self.player.invuln_ticks))
        self.player.dash_cd_ticks = int(player.get("dash_cd_ticks", self.player.dash_cd_ticks))
        self.player.pulse_cd_ticks = int(player.get("pulse_cd_ticks", self.player.pulse_cd_ticks))
        self.player.charm_ticks = int(player.get("charm_ticks", self.player.charm_ticks))
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
            self.shades.append(Shade(identifier, [float(v) for v in item["pos"]], item.get("state", "chase"), int(item.get("state_ticks_left", 0))))
            self._next_shade_id += 1
        if scenario.get("random_drifters") is False or "drifters" in scenario:
            self.drifters = []
        for index, item in enumerate(scenario.get("drifters", []), 1):
            self.drifters.append(Drifter(item.get("id", f"D{index}"), [float(v) for v in item["pos"]], item.get("state", "idle"), int(item.get("stolen", 0)), int(item.get("state_ticks_left", 0))))
        if "charms" in scenario:
            self.charms = []
            for index, item in enumerate(scenario["charms"], 1):
                self.charms.append(Charm(item.get("id", f"C{index}"), [float(v) for v in item["pos"]], bool(item.get("available", True)), int(item.get("respawn_ticks", 0))))
        if scenario.get("wind_enabled") is False:
            self.wind["active"] = False
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
        if self.player.respawn_ticks > 0:
            return
        move = controls.get("move", [0.0, 0.0])
        x, z = float(move[0]), float(move[1])
        magnitude = math.hypot(x, z)
        if magnitude > 1:
            x, z = x / magnitude, z / magnitude
        yaw = math.radians(float(controls.get("cam_yaw_deg", 0.0)))
        world_x = x * math.cos(yaw) + z * math.sin(yaw)
        world_z = -x * math.sin(yaw) + z * math.cos(yaw)
        if magnitude > 0:
            self.player.facing = [world_x, world_z]
        if self._pressed("dash", controls) and self.player.dash_ticks == 0 and (self.player.dash_cd_ticks == 0 or self.player.charm_ticks > 0):
            self.player.dash_ticks = round(self.tuning["dash_duration_s"] * TICK_RATE)
            self.player.dash_cd_ticks = 0 if self.player.charm_ticks > 0 else round(self.tuning["dash_cooldown_s"] * TICK_RATE)
        speed = self.tuning["dash_speed"] if self.player.dash_ticks > 0 else (7.2 if self.player.charm_ticks > 0 else self.tuning["player_speed"])
        direction = self.player.facing if self.player.dash_ticks > 0 else [world_x, world_z]
        distance = speed / TICK_RATE
        self.player.pos[0] += direction[0] * distance
        self.player.pos[2] += direction[1] * distance
        vertical_velocity = (self.player.vel or [0.0, 0.0, 0.0])[1]
        self.player.vel = [direction[0] * speed, vertical_velocity, direction[1] * speed]
        if self._pressed("jump", controls) and self.player.grounded:
            self.player.vel[1] = 7.0
            self.player.grounded = False
        if not self.player.grounded:
            if self.player.dash_ticks == 0:
                self.player.vel[1] -= 20.0 / TICK_RATE
                self.player.pos[1] += self.player.vel[1] / TICK_RATE
            ground = self._ground_height(self.player.pos[0], self.player.pos[2])
            if ground is not None and self.player.pos[1] <= ground:
                self.player.pos[1] = ground
                self.player.vel[1] = 0.0
                self.player.grounded = True
        else:
            ground = self._ground_height(self.player.pos[0], self.player.pos[2])
            if ground is None or ground < self.player.pos[1] - 0.1:
                self.player.grounded = False

    def _ground_height(self, x: float, z: float) -> float | None:
        if self.night == 1:
            return 0.0 if math.hypot(x, z) <= 40 else None
        if self.night == 2:
            on_island = math.hypot(x, z) <= 28 or math.hypot(x - 70, z) <= 28
            on_bridge = 26 <= x <= 44 and -2 <= z <= 2
            return 0.0 if on_island or on_bridge else None
        radius = math.hypot(x, z)
        if radius <= 8:
            return 6.0
        if 12 <= radius <= 24 and z > 0:
            return 3.0
        return 0.0 if radius <= 45 else None

    def _pickup_motes(self, events: list[dict[str, Any]]) -> None:
        for mote in list(self.motes):
            if self.player.carried >= self.tuning["carry_capacity"]:
                break
            if abs(self.player.pos[1] - mote.pos[1]) <= 1.5 and _xz_distance(self.player.pos, mote.pos) <= self.tuning["pickup_radius"]:
                self.motes.remove(mote)
                self.player.carried += 1
                events.append(self._event("mote_picked", {"carried": self.player.carried}))

    def _pickup_charms(self, events: list[dict[str, Any]]) -> None:
        for charm in self.charms:
            if charm.available and abs(self.player.pos[1] - charm.pos[1]) <= 1.5 and _xz_distance(self.player.pos, charm.pos) <= self.tuning["pickup_radius"]:
                charm.available = False
                charm.respawn_ticks = 2700
                self.player.charm_ticks = 600
                events.append(self._event("charm_picked", {"charm_id": charm.id, "charm_ticks": 600}))

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
                dx, dz = shade.pos[0] - self.player.pos[0], shade.pos[2] - self.player.pos[2]
                length = math.hypot(dx, dz)
                shade.push_dir = [1.0, 0.0] if length == 0 else [dx / length, dz / length]
                shade.push_ticks = 15
                stunned.append(shade.id)
        self.score += len(stunned) * self.tuning["score"]["per_stun"]
        events.append(self._event("pulse", {"stunned_ids": stunned}))
        for drifter in list(self.drifters):
            if drifter.state not in ("chase", "flee") or _distance3(centre, drifter.pos) > self.tuning["pulse_radius"]:
                continue
            if drifter.state == "flee" and drifter.stolen:
                for _ in range(drifter.stolen):
                    self._add_mote(drifter.pos.copy(), "dropped", 120)
                events.append(self._event("drifter_drop", {"drifter_id": drifter.id, "amount": drifter.stolen}))
                self.drifters.remove(drifter)
            else:
                drifter.state = "flee"
                drifter.state_ticks_left = 240

    def _update_drifters(self, events: list[dict[str, Any]]) -> None:
        for drifter in list(sorted(self.drifters, key=lambda item: item.id)):
            distance = _xz_distance(drifter.pos, self.player.pos)
            if drifter.state == "idle" and self.player.carried >= 5 and distance <= 15:
                drifter.state = "chase"
            elif drifter.state == "chase" and (self.player.carried < 5 or distance > 15):
                drifter.state = "idle"
            speed = 7.0 if drifter.state in ("chase", "flee") else 2.0
            if distance > 0:
                sign = -1 if drifter.state == "flee" else 1
                drifter.pos[0] += (self.player.pos[0] - drifter.pos[0]) / distance * speed / TICK_RATE * sign
                drifter.pos[2] += (self.player.pos[2] - drifter.pos[2]) / distance * speed / TICK_RATE * sign
            if drifter.state == "chase" and _xz_distance(drifter.pos, self.player.pos) <= 1.2:
                amount = min(3, self.player.carried)
                self.player.carried -= amount
                drifter.stolen = amount
                drifter.state = "flee"
                drifter.state_ticks_left = 240
                events.append(self._event("drifter_steal", {"drifter_id": drifter.id, "amount": amount, "carried": self.player.carried}))
            elif drifter.state == "flee":
                drifter.state_ticks_left -= 1
                if drifter.state_ticks_left <= 0:
                    self.drifters.remove(drifter)

    def _update_shades(self, events: list[dict[str, Any]]) -> None:
        for shade in sorted(self.shades, key=lambda item: item.id):
            if shade.state == "spawning":
                shade.state_ticks_left -= 1
                if shade.state_ticks_left <= 0:
                    shade.state = "wander"
                continue
            if shade.state == "stunned":
                if shade.push_ticks > 0:
                    shade.pos[0] += (shade.push_dir or [1.0, 0.0])[0] * self.tuning["pulse_push_m"] / 15
                    shade.pos[2] += (shade.push_dir or [1.0, 0.0])[1] * self.tuning["pulse_push_m"] / 15
                    shade.push_ticks -= 1
                shade.state_ticks_left -= 1
                if shade.state_ticks_left <= 0:
                    shade.state = "chase"
                continue
            distance = _xz_distance(shade.pos, self.player.pos)
            if distance > 0:
                step = min(self.tuning["shade_speed"] / TICK_RATE, distance)
                candidate = [shade.pos[0] + (self.player.pos[0] - shade.pos[0]) / distance * step, shade.pos[1], shade.pos[2] + (self.player.pos[2] - shade.pos[2]) / distance * step]
                blocked = [lantern for lantern in self.lanterns if lantern.lit and _xz_distance(candidate, lantern.pos) < self.tuning["safe_radius"] <= _xz_distance(shade.pos, lantern.pos)]
                if not blocked:
                    shade.pos = candidate
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

    def _spawn_scheduled(self, events: list[dict[str, Any]]) -> None:
        resulting_tick = self.sim_tick + 1
        if self.random_motes and resulting_tick % 240 == 0 and len(self.motes) < 30:
            occupied = {(round(mote.pos[0], 3), round(mote.pos[1], 3), round(mote.pos[2], 3)) for mote in self.motes}
            available = [point for point in self.mote_spawn_points if tuple(round(value, 3) for value in point) not in occupied]
            if available:
                self._add_mote(self.rng.choice(available))
        intervals = {1: 480, 2: 420, 3: 360}
        maxima = {1: 6, 2: 8, 3: 10}
        should_spawn_shade = resulting_tick == 300 or (resulting_tick > 300 and (resulting_tick - 300) % intervals[self.night] == 0)
        amount = 2 if resulting_tick == 300 else 1
        if self.random_shades and should_spawn_shade:
            for _ in range(amount):
                if len(self.shades) >= maxima[self.night]:
                    break
                valid = [point for point in self.shade_spawn_points if _xz_distance(point, self.player.pos) >= 15]
                if not valid:
                    break
                pos = self.rng.choice(valid).copy()
                shade = Shade(f"S{self._next_shade_id}", pos, "spawning", 1)
                self._next_shade_id += 1
                self.shades.append(shade)
                events.append(self._event("shade_spawned", {"id": shade.id}))
        if self.random_drifters and self.night in (2, 3) and resulting_tick % 1200 == 0 and len(self.drifters) < 2:
            angle = self.rng.random() * math.tau
            radius = 24 if self.night == 2 else 40
            centre = 70.0 if self.night == 2 and self.rng.random() < 0.5 else 0.0
            self.drifters.append(Drifter(f"D{self._next_drifter_id}", [centre + math.cos(angle) * radius, 0.0, math.sin(angle) * radius]))
            self._next_drifter_id += 1

    def _update_wind(self) -> None:
        if self.night != 3:
            return
        cycle = self.sim_tick % 1800
        if cycle == 0 and self.sim_tick > 0:
            self.wind["dir_deg"] = round(self.rng.random() * 360, 3)
        self.wind["active"] = cycle < 300 and self.sim_tick >= 1800
        if self.wind["active"]:
            angle = math.radians(self.wind["dir_deg"])
            self.player.pos[0] += math.cos(angle) * 2 / TICK_RATE
            self.player.pos[2] += math.sin(angle) * 2 / TICK_RATE

    def _event(self, name: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"type": "event", "tick": self.tick + 1, "name": name, "data": data}

    def _handle_fall(self, events: list[dict[str, Any]]) -> None:
        if self.player.pos[1] >= -10 or self.player.respawn_ticks > 0:
            return
        lost = self.player.carried
        self.player.carried = 0
        self.player.flames -= 1
        events.append(self._event("player_hit", {"by": "fall", "flames": self.player.flames, "dropped": 0, "lost": lost}))
        if self.player.flames > 0:
            self.player.respawn_ticks = 60

    def _tick_respawn(self) -> None:
        if self.player.respawn_ticks <= 0:
            return
        self.player.respawn_ticks -= 1
        if self.player.respawn_ticks == 0:
            self.player.pos = [0.0, 0.0, 0.0]
            self.player.vel = [0.0, 0.0, 0.0]
            self.player.grounded = True
            self.player.invuln_ticks = 90

    def step(self, controls: dict[str, Any]) -> list[dict[str, Any]]:
        if self.state in ("won", "lost"):
            return []
        events: list[dict[str, Any]] = []
        if self._pressed("pause", controls):
            self.paused = not self.paused
            self.state = "paused" if self.paused else "playing"
            events.append(self._event("paused" if self.paused else "resumed", {}))
            self.tick += 1
            for action in self._previous_input:
                self._previous_input[action] = bool(controls.get(action, self._previous_input[action]))
            return events
        if self.paused:
            self.tick += 1
            for action in self._previous_input:
                self._previous_input[action] = bool(controls.get(action, self._previous_input[action]))
            return events
        if self.player.invuln_ticks > 0:
            self.player.invuln_ticks -= 1
        if self.player.pulse_cd_ticks > 0:
            self.player.pulse_cd_ticks -= 1
        if self.player.dash_cd_ticks > 0:
            self.player.dash_cd_ticks -= 1
        if self.player.dash_ticks > 0:
            self.player.dash_ticks -= 1
        if self.player.charm_ticks > 0:
            self.player.charm_ticks -= 1
        self._tick_respawn()
        for charm in self.charms:
            if not charm.available:
                charm.respawn_ticks -= 1
                if charm.respawn_ticks <= 0:
                    charm.available = True
        for mote in list(self.motes):
            if mote.ttl_ticks is not None:
                mote.ttl_ticks -= 1
                if mote.ttl_ticks <= 0:
                    self.motes.remove(mote)
        self._move_player(controls)
        self._handle_fall(events)
        self._pickup_motes(events)
        self._pickup_charms(events)
        if self._pressed("interact", controls):
            self._deposit(events)
        if self._pressed("pulse", controls):
            self._pulse(events)
        self._update_drifters(events)
        self._update_shades(events)
        self._spawn_scheduled(events)
        self._update_wind()
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
            "night": self.night,
            "wind": self.wind.copy(),
            "time_left_s": round(self.time_left_s, 3),
            "score": self.score,
            "player": {
                "pos": _rounded_pos(self.player.pos), "vel": _rounded_pos(self.player.vel or [0, 0, 0]),
                "grounded": self.player.grounded, "flames": self.player.flames, "carried": self.player.carried,
                "invuln": self.player.invuln_ticks > 0, "dash_cd_s": round(self.player.dash_cd_ticks / TICK_RATE, 3),
                "pulse_cd_s": round(self.player.pulse_cd_ticks / TICK_RATE, 3), "charm_s": round(self.player.charm_ticks / TICK_RATE, 3),
            },
            "lanterns": [{"id": item.id, "pos": _rounded_pos(item.pos), "lit": item.lit, "deposited": item.deposited} for item in self.lanterns],
            "shades": [{"id": item.id, "pos": _rounded_pos(item.pos), "state": item.state} for item in self.shades],
            "motes_active": len(self.motes),
            "motes": [{"id": item.id, "pos": _rounded_pos(item.pos), "kind": item.kind, "ttl_s": None if item.ttl_ticks is None else round(item.ttl_ticks / TICK_RATE, 3)} for item in self.motes],
            "drifters": [{"id": item.id, "pos": _rounded_pos(item.pos), "state": item.state, "stolen": item.stolen} for item in self.drifters],
            "charms": [{"id": item.id, "available": item.available, "respawn_s": round(item.respawn_ticks / TICK_RATE, 3)} for item in self.charms],
        }
