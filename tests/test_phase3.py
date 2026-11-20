import unittest

from lantern_islands.simulation import Simulation


class Phase3FuelRulesTests(unittest.TestCase):
    def test_lit_lantern_decays_and_goes_out_at_zero_fuel(self):
        sim = Simulation(seed=1, night=1, scenario={
            "random_motes": False, "random_shades": False,
            "lanterns": [{"id": "L1", "lit": True, "fuel": 0.1, "ever_lit": True}],
        })
        events = []
        for _ in range(6):
            events.extend(sim.step({}))
        lantern = sim.lanterns[0]
        self.assertFalse(lantern.lit)
        self.assertEqual(lantern.deposited, 0)
        self.assertIn("lantern_out", [event["name"] for event in events])

    def test_interact_refuels_nearest_lit_lantern_and_scores_motes(self):
        sim = Simulation(seed=1, night=1, scenario={
            "player": {"pos": [0, 0, 0], "carried": 2},
            "random_motes": False, "random_shades": False,
            "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 83, "ever_lit": True}],
        })
        events = sim.step({"interact": True})
        lantern = sim.lanterns[0]
        self.assertEqual(lantern.fuel, 100.0)
        self.assertEqual(sim.player.carried, 0)
        self.assertEqual(sim.score, 10)
        self.assertEqual(events[0]["name"], "refuel")
        self.assertEqual(events[0]["data"]["amount"], 2)

    def test_relighting_costs_five_and_increases_dynamic_capacity(self):
        sim = Simulation(seed=1, night=1, scenario={
            "player": {"pos": [0, 0, 0], "carried": 5},
            "random_motes": False, "random_shades": False,
            "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": False, "ever_lit": True}],
        })
        events = sim.step({"interact": True})
        self.assertTrue(sim.lanterns[0].lit)
        self.assertEqual(sim.lanterns[0].relit_count, 1)
        self.assertEqual(sim.player.successful_lights, 1)
        self.assertEqual(sim.player.capacity, 12)
        self.assertEqual(sim.score, 65)
        lit_event = next(event for event in events if event["name"] == "lantern_lit")
        self.assertTrue(lit_event["data"]["relight"])

    def test_all_lit_does_not_win_early_but_threshold_wins_at_dawn(self):
        lanterns = [{"id": f"L{i}", "lit": i <= 3, "fuel": 100, "ever_lit": i <= 3} for i in range(1, 6)]
        sim = Simulation(seed=1, night=1, scenario={
            "random_motes": False, "random_shades": False,
            "lanterns": lanterns, "time_left_s": 1 / 60,
        })
        events = sim.step({})
        self.assertEqual(sim.state, "won")
        game_over = next(event for event in events if event["name"] == "game_over")
        self.assertEqual(game_over["data"]["reason"], "dawn_survived")

    def test_wander_shade_drains_low_fuel_lantern_and_emits_each_second(self):
        sim = Simulation(seed=1, night=1, scenario={
            "player": {"pos": [20, 0, 0]},
            "random_motes": False, "random_shades": False,
            "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 20, "ever_lit": True}],
            "shades": [{"id": "S1", "pos": [1, 0, 0], "state": "wander", "target_lantern_id": "L1"}],
        })
        events = []
        for _ in range(61):
            events.extend(sim.step({}))
        self.assertEqual(sim.shades[0].state, "drain")
        self.assertAlmostEqual(sim.lanterns[0].fuel, 14.0, places=1)
        drains = [event for event in events if event["name"] == "fuel_drain"]
        self.assertEqual(len(drains), 1)

    def test_v12_snapshot_exposes_fuel_capacity_and_relight_state(self):
        snapshot = Simulation(seed=1, night=1).snapshot()
        self.assertEqual(snapshot["player"]["capacity"], 10)
        for key in ("fuel", "ever_lit", "relit_count"):
            self.assertIn(key, snapshot["lanterns"][0])

    def test_refuel_restores_safe_zone_and_recoils_shade_without_damage(self):
        sim = Simulation(seed=1, night=1, scenario={
            "player": {"pos": [0, 0, 0], "carried": 1, "flames": 3},
            "random_motes": False, "random_shades": False,
            "lanterns": [{"id": "L1", "pos": [0, 0, 0], "lit": True, "fuel": 29, "ever_lit": True}],
            "shades": [{"id": "S1", "pos": [3, 0, 0], "state": "drain", "target_lantern_id": "L1"}],
        })
        sim.step({"interact": True})
        self.assertEqual(sim.shades[0].state, "recoil")
        self.assertEqual(sim.player.flames, 3)
        self.assertGreater(sim.shades[0].pos[0], 3)


if __name__ == "__main__":
    unittest.main()
