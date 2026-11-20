import unittest

from lantern_islands.simulation import Simulation


class Phase2ContractTests(unittest.TestCase):
    def test_each_night_uses_standard_lantern_count_and_duration(self):
        expectations = {1: (5, 300), 2: (6, 330), 3: (7, 360)}
        for night, (lantern_count, duration) in expectations.items():
            sim = Simulation(seed=1, night=night, scenario={"random_motes": False, "random_shades": False, "random_drifters": False})
            self.assertEqual(len(sim.lanterns), lantern_count)
            self.assertEqual(sim.time_left_s, duration)

    def test_dash_moves_fourteen_metres_per_second_for_twelve_ticks(self):
        sim = Simulation(seed=1, night=2, scenario={"random_motes": False, "random_shades": False, "random_drifters": False})
        sim.step({"move": [0, 1], "dash": True})
        for _ in range(11):
            sim.step({"move": [0, 1], "dash": False})
        self.assertAlmostEqual(sim.player.pos[2], 2.8, places=3)
        self.assertGreater(sim.player.dash_cd_ticks, 0)

    def test_pause_advances_tick_but_freezes_gameplay_clock(self):
        sim = Simulation(seed=1, night=1)
        events = sim.step({"pause": True})
        time_left = sim.time_left_s
        sim_tick = sim.sim_tick
        sim.step({"pause": False, "move": [1, 0]})
        self.assertEqual(events[0]["name"], "paused")
        self.assertEqual(sim.state, "paused")
        self.assertEqual(sim.sim_tick, sim_tick)
        self.assertEqual(sim.time_left_s, time_left)
        self.assertEqual(sim.player.pos, [0.0, 0.0, 0.0])

    def test_charm_increases_running_speed_and_removes_dash_cooldown(self):
        sim = Simulation(seed=1, night=2, scenario={
            "player": {"pos": [35, 0, 0]}, "random_motes": False,
            "random_shades": False, "random_drifters": False,
        })
        events = sim.step({})
        self.assertIn("charm_picked", [event["name"] for event in events])
        self.assertEqual(sim.player.charm_ticks, 600)
        sim.step({"dash": True, "move": [1, 0]})
        self.assertEqual(sim.player.dash_cd_ticks, 0)

    def test_drifter_steals_three_then_pulse_makes_it_drop_them(self):
        sim = Simulation(seed=1, night=2, scenario={
            "player": {"pos": [0, 0, 0], "carried": 8},
            "random_motes": False, "random_shades": False,
            "motes": [], "drifters": [{"id": "D7", "pos": [0, 0, 0], "state": "chase", "stolen": 0}],
            "charms": [],
        })
        events = sim.step({})
        self.assertEqual(events[0]["name"], "drifter_steal")
        self.assertEqual(sim.player.carried, 5)
        sim.player.carried = 3
        events = sim.step({"pulse": True})
        self.assertIn("drifter_drop", [event["name"] for event in events])
        self.assertFalse(sim.drifters)
        self.assertEqual(len([mote for mote in sim.motes if mote.kind == "dropped"]), 3)

    def test_snapshot_contains_all_v11_fields(self):
        snapshot = Simulation(seed=1, night=3).snapshot()
        for key in ("night", "wind", "motes", "drifters", "charms"):
            self.assertIn(key, snapshot)
        for key in ("vel", "grounded", "invuln", "dash_cd_s", "pulse_cd_s", "charm_s"):
            self.assertIn(key, snapshot["player"])

    def test_scheduled_entities_spawn_on_contract_ticks(self):
        sim = Simulation(seed=3, night=1, scenario={"random_motes": True, "random_shades": True, "motes": []})
        for _ in range(300):
            sim.step({})
        self.assertEqual(len(sim.motes), 1)
        self.assertEqual([shade.id for shade in sim.shades], ["S1", "S2"])

    def test_falling_loses_all_carried_motes_then_respawns(self):
        sim = Simulation(seed=1, night=1, scenario={
            "player": {"pos": [50, -10.1, 0], "carried": 7, "flames": 3},
            "random_motes": False, "random_shades": False,
        })
        events = sim.step({})
        self.assertEqual(events[0]["data"]["lost"], 7)
        self.assertEqual(sim.player.flames, 2)
        for _ in range(60):
            sim.step({})
        self.assertEqual(sim.player.pos, [0.0, 0.0, 0.0])
        self.assertEqual(sim.player.invuln_ticks, 90)

    def test_pulse_pushes_a_shade_four_metres_over_fifteen_ticks(self):
        sim = Simulation(seed=1, night=1, scenario={
            "player": {"carried": 3}, "random_motes": False, "random_shades": False,
            "shades": [{"id": "S1", "pos": [1, 0.8, 0]}],
        })
        sim.step({"pulse": True})
        for _ in range(14):
            sim.step({"pulse": False})
        self.assertAlmostEqual(sim.shades[0].pos[0], 5.0, places=3)


if __name__ == "__main__":
    unittest.main()
