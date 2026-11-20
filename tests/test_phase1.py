import unittest

from lantern_islands.simulation import Simulation


class Phase1SimulationTests(unittest.TestCase):
    def test_player_moves_six_metres_in_one_second(self):
        sim = Simulation(seed=7, night=1, scenario={"random_motes": False, "random_shades": False})
        for _ in range(60):
            sim.step({"move": [0, 1], "cam_yaw_deg": 0})
        self.assertAlmostEqual(sim.player.pos[2], 6.0, places=3)

    def test_pickup_then_deposit_lights_lantern_and_scores(self):
        sim = Simulation(seed=1, night=1, scenario={
            "player": {"pos": [0, 0, 0], "carried": 9, "flames": 3},
            "random_motes": False,
            "random_shades": False,
            "motes": [[0, 0, 0]],
            "lanterns": [{"id": "L1", "pos": [0, 0, 0], "deposited": 0}],
        })
        pickup_events = sim.step({})
        deposit_events = sim.step({"interact": True})
        self.assertEqual(pickup_events[0]["name"], "mote_picked")
        self.assertEqual([event["name"] for event in deposit_events], ["deposit", "lantern_lit"])
        self.assertTrue(sim.lanterns[0].lit)
        self.assertEqual(sim.score, 200)

    def test_pulse_costs_motes_and_stuns_nearby_shade(self):
        sim = Simulation(seed=1, night=1, scenario={
            "player": {"pos": [0, 0, 0], "carried": 3, "flames": 3},
            "random_motes": False,
            "random_shades": False,
            "motes": [],
            "shades": [{"id": "S9", "pos": [3, 0.8, 0]}],
        })
        events = sim.step({"pulse": True})
        self.assertEqual(events[0]["name"], "pulse")
        self.assertEqual(events[0]["data"]["stunned_ids"], ["S9"])
        self.assertEqual(sim.player.carried, 0)
        self.assertEqual(sim.shades[0].state, "stunned")

    def test_same_seed_and_actions_are_deterministic(self):
        def run():
            sim = Simulation(seed=42, night=1)
            return [sim.step({"move": [1, 0]}) for _ in range(320)], sim.snapshot()
        self.assertEqual(run(), run())


if __name__ == "__main__":
    unittest.main()
