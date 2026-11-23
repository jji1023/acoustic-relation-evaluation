"""Run from the candidate root with python -B smoke.py."""

from collections import Counter
from dataclasses import replace
from itertools import product
import json
from pathlib import Path
import unittest
from xml.etree import ElementTree

from p79_protocol.audio import Recipe, crop, normalize, render, sample_digest
from p79_protocol.evaluate import count_endpoints, count_ir, cube_edges, strict_four_answer
from p79_protocol.parser import parse
from p79_protocol.plots import interval_svg
from p79_protocol.questions import CONDITIONS, FACTORS, illustrative_prompt, question_rows
from p79_protocol.stats import paired_component_rates, percentile_interval


class Smoke(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parent / "data" / "SYNTHETIC_FIXTURE.json"
        self.fixture = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(self.fixture["kind"], "SYNTHETIC_TEST_ONLY")

    def test_scene_reconstruction(self):
        recipe = Recipe(**self.fixture["recipe"])
        anchors = self.fixture["anchors"]
        settings = {"sample_rate": self.fixture["sample_rate"], "seconds": self.fixture["seconds"]}
        hashes = set()
        for bits in CONDITIONS:
            samples, placed = render(anchors, bits, recipe, **settings)
            self.assertEqual(len(samples), 80)
            self.assertEqual({v[0] for v in placed.values()}, {10, 50})
            self.assertEqual({v[1] for v in placed.values()}, {4, 8})
            for role, (start, length, gain) in placed.items():
                self.assertAlmostEqual(samples[start], anchors[role][0] * 10 ** (gain / 20))
                self.assertEqual(samples[start + length], 0)
            self.assertEqual(sample_digest(samples), sample_digest(render(anchors, bits, recipe, **settings)[0]))
            hashes.add(sample_digest(samples))
        self.assertEqual(len(hashes), 8)
        self.assertEqual(crop([0, 1, 2], 1, 2), (1, 2))
        self.assertAlmostEqual(normalize([0.1], -20, -26.020599913)[0], 0.05)
        with self.assertRaisesRegex(ValueError, "clip"):
            render({"A": [1.0] * 8, "B": anchors["B"]}, "000", recipe, **settings)
        with self.assertRaisesRegex(ValueError, "clip"):
            render({"A": [1e100] * 8, "B": anchors["B"]}, "000", recipe, float32_mix=True, **settings)
        with self.assertRaisesRegex(ValueError, "nonoverlapping"):
            render(anchors, "001", replace(recipe, late=0.3), **settings)
        with self.assertRaisesRegex(ValueError, "invalid anchor"):
            normalize([float("nan")], -20)

    def test_questions_and_parsers(self):
        rows = list(question_rows("toy", self.fixture["names"]))
        self.assertEqual(len({r["qa_id"] for r in rows}), 48)
        self.assertEqual(Counter(r["gt"] for r in rows), {"A": 24, "B": 24})
        prompt = illustrative_prompt(rows[0], "LETTER")
        self.assertIn("Return the option letter only.", prompt)
        for row in rows:
            roles = tuple(row["order"])
            letter = "AB"[roles.index(row["gt"])]
            for reply, interface in ((letter + ".", "LETTER"),
                                     ("The answer is " + row["options"][roles.index(row["gt"])], "SOUND")):
                result = parse(reply, row["options"], roles, interface)
                self.assertEqual(result[:2], (row["gt"], True))
        self.assertFalse(parse("A because the chime starts", rows[0]["options"], "AB", "LETTER")[1])
        self.assertFalse(parse("Either fictional chime or fictional click", rows[0]["options"], "AB", "SOUND")[1])
        self.assertFalse(parse(None, rows[0]["options"], "AB", "LETTER")[1])
        with self.assertRaisesRegex(ValueError, "distinct"):
            list(question_rows("toy", {"A": "Chime", "B": " chime! "}))
        with self.assertRaisesRegex(ValueError, "role order"):
            parse("A", rows[0]["options"], "AC", "LETTER")

    def test_edge_and_pair_counts(self):
        names = self.fixture["names"]
        qa = {(r["condition"], r["factor"], r["order"]): r for r in question_rows("toy", names)}
        answers = {}
        for (bits, factor, order), row in qa.items():
            desired = row["gt"]
            if (bits, factor, order) == ("000", "DURATION", "BA"):
                desired = "B"
            token = "AB"[order.index(desired)]
            if (bits, factor, order) == ("000", "POSITION", "AB"):
                token = "A with explanation"
            label, valid, _ = parse(token, row["options"], order, "LETTER")
            answers[bits, factor, order] = (row["gt"], label if valid else None)

        def both(bits, factor):
            gt, a = answers[bits, factor, "AB"]
            _, b = answers[bits, factor, "BA"]
            return gt, a, b

        paired = count_endpoints(both(bits, factor) for bits, factor in product(CONDITIONS, FACTORS))
        self.assertEqual(paired, Counter(pairs=24, endpoints=48, correct=46, valid=47,
                                         both_valid=23, agreement=22))
        edges = list(cube_edges())
        self.assertEqual(len(edges), 12)
        ir = count_ir((question, intervention, answers[left, question, order], answers[right, question, order])
                      for intervention, left, right in edges for question in FACTORS for order in ("AB", "BA"))
        self.assertEqual(len(ir), 9)
        self.assertEqual(sum(c["edges"] for c in ir.values()), 72)
        self.assertEqual(sum(c["joint"] for c in ir.values()), 66)
        self.assertEqual(sum(c["joint"] for (q, t), c in ir.items() if q == t), 22)
        self.assertEqual(sum(strict_four_answer(both(l, q), both(r, q)) for q, l, r in edges), 10)
        with self.assertRaisesRegex(ValueError, "semantic GT"):
            count_endpoints([(None, None, None)])
        with self.assertRaisesRegex(ValueError, "GT polarity"):
            count_ir([("DURATION", "DURATION", ("A", "A"), ("A", "A"))])
        with self.assertRaisesRegex(ValueError, "semantic answers"):
            strict_four_answer(("A", "A", "A"), ("B", "INVALID", "B"))

    def test_paired_draw_and_plot(self):
        samples = list(paired_component_rates([(1, 2), (2, 2)], [(2, 2), (1, 2)],
                                               [(0, 0), (0, 1), (1, 1)]))
        self.assertEqual(samples, [(0.5, 1.0, 0.5), (0.75, 0.75, 0.0), (1.0, 0.5, -0.5)])
        low, high = percentile_interval(item[2] for item in samples)
        self.assertAlmostEqual(low, -0.475)
        self.assertAlmostEqual(high, 0.475)
        svg = interval_svg([("Synthetic A", 0.75, 0.5, 1)], "Target-edge joint correctness")
        self.assertEqual(ElementTree.fromstring(svg).tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIn("Target-edge joint correctness", svg)
        with self.assertRaisesRegex(ValueError, "component counts"):
            list(paired_component_rates([(0.5, 1)], [(1, 1)], [(0,)]))
        with self.assertRaisesRegex(ValueError, "component draw"):
            list(paired_component_rates([(0, 1)], [(1, 1)], [(0.5,)]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
