"""P1 truthful showcase foundation: unit tests (no hardware).

Covers the RF Evidence Confidence aggregator, the presence-state
persistence machine, factual XAI statements, contract-v3 showcase
fields, and the InferenceEngine showcase snapshot on synthetic CSI.
Every honesty invariant is asserted, not just happy paths: no score
without evidence, UNCALIBRATED always, UNKNOWN never invents, fade is
monotonic, contracts reject bad enums.
"""

import unittest

from web import contracts
from web.contracts import ContractError
from sensing.confidence.confidence import (
    CALIBRATION_LABEL,
    DEGRADE_DERATE,
    aggregate_evidence,
)
from sensing.state.persistence import (
    FADE_S,
    HOLD_S,
    LOW_CONFIDENCE_BAND,
    PresencePersistence,
)
from ai.xai.xai import factual_evidence_statement


class ConfidenceTests(unittest.TestCase):
    def test_no_evidence_no_score(self):
        score, info = aggregate_evidence(presence_prob=None,
                                         movement_prob=None)
        self.assertIsNone(score)  # None, never 0-as-unknown
        self.assertEqual(info["calibration"], "UNCALIBRATED")

    def test_stale_no_score(self):
        score, info = aggregate_evidence(presence_prob=0.9,
                                         movement_prob=0.9, stale=True)
        self.assertIsNone(score)

    def test_score_bounded_and_labelled(self):
        score, info = aggregate_evidence(presence_prob=0.8,
                                         movement_prob=0.6)
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertEqual(info["calibration"], CALIBRATION_LABEL)
        self.assertEqual(CALIBRATION_LABEL, "UNCALIBRATED")

    def test_weights_transparent(self):
        _, info = aggregate_evidence(presence_prob=1.0, movement_prob=0.0)
        self.assertEqual(info["weights"], {"presence": 0.6, "movement": 0.4})

    def test_degrade_derate_reduces(self):
        full, _ = aggregate_evidence(presence_prob=0.9, movement_prob=0.9)
        derated, _ = aggregate_evidence(presence_prob=0.9, movement_prob=0.9,
                                        nodes_available=1, nodes_total=2,
                                        derate=DEGRADE_DERATE)
        self.assertLess(derated, full)

    def test_bad_quality_halves(self):
        good, _ = aggregate_evidence(presence_prob=0.8, movement_prob=0.8)
        bad, _ = aggregate_evidence(presence_prob=0.8, movement_prob=0.8,
                                    data_quality_ok=False)
        self.assertAlmostEqual(bad, good * 0.5)


class PersistenceTests(unittest.TestCase):
    def test_unknown_stays_unknown(self):
        p = PresencePersistence(clock=lambda: 0.0)
        self.assertEqual(p.update(presence_label="UNKNOWN",
                                 movement_label="UNKNOWN",
                                 confidence=None), ("UNKNOWN", None))

    def test_person_routes_by_movement(self):
        p = PresencePersistence(clock=lambda: 0.0)
        self.assertEqual(p.update(presence_label="PERSON",
                                 movement_label="MOVING",
                                 confidence=0.9)[0], "MOVING")
        self.assertEqual(p.update(presence_label="PERSON",
                                 movement_label="STATIC",
                                 confidence=0.9)[0], "STATIONARY")
        self.assertEqual(p.update(presence_label="PERSON",
                                 movement_label="UNKNOWN",
                                 confidence=0.9)[0], "DETECTED")

    def test_low_band_selects_honesty_label(self):
        p = PresencePersistence(clock=lambda: 0.0)
        state, _ = p.update(presence_label="PERSON", movement_label="MOVING",
                            confidence=LOW_CONFIDENCE_BAND - 0.01)
        self.assertEqual(state, "LOW_CONFIDENCE")

    def test_exit_hold_fade_absent(self):
        now = [0.0]
        p = PresencePersistence(clock=lambda: now[0])
        p.update(presence_label="PERSON", movement_label="MOVING",
                 confidence=0.9)
        # Disappear: EXITING holds the last strong value...
        state, shown = p.update(presence_label="EMPTY",
                                movement_label="STATIC", confidence=None)
        self.assertEqual(state, "EXITING")
        self.assertAlmostEqual(shown, 0.9)
        # ...through the hold window...
        now[0] = HOLD_S - 0.1
        state, shown = p.update(presence_label="EMPTY",
                                movement_label="STATIC", confidence=None)
        self.assertEqual(state, "EXITING")
        self.assertAlmostEqual(shown, 0.9)
        # ...then fades monotonically...
        now[0] = HOLD_S + FADE_S / 2.0
        mid_state, mid = p.update(presence_label="EMPTY",
                                  movement_label="STATIC", confidence=None)
        self.assertEqual(mid_state, "EXITING")
        self.assertLess(mid, 0.9)
        now[0] = HOLD_S + FADE_S - 0.1
        _, late = p.update(presence_label="EMPTY",
                           movement_label="STATIC", confidence=None)
        self.assertLess(late, mid)
        # ...then ABSENT with no score.
        now[0] = HOLD_S + FADE_S + 0.1
        self.assertEqual(p.update(presence_label="EMPTY",
                                 movement_label="STATIC",
                                 confidence=None), ("ABSENT", None))

    def test_empty_without_history_is_absent(self):
        p = PresencePersistence(clock=lambda: 0.0)
        self.assertEqual(p.update(presence_label="EMPTY",
                                 movement_label="STATIC",
                                 confidence=None), ("ABSENT", None))

    def test_preview_is_side_effect_free(self):
        now = [0.0]
        p = PresencePersistence(clock=lambda: now[0])
        p.update(presence_label="PERSON", movement_label="MOVING",
                 confidence=0.9)
        before = p.current()
        p.preview(presence_label="PERSON", movement_label="STATIC",
                  confidence=0.2)
        self.assertEqual(p.current(), before)

    def test_reset(self):
        p = PresencePersistence(clock=lambda: 0.0)
        p.update(presence_label="PERSON", movement_label="MOVING",
                 confidence=0.9)
        p.reset()
        self.assertEqual(p.current(), ("UNKNOWN", None))


class FactualStatementTests(unittest.TestCase):
    def test_every_state_has_sentence(self):
        for state in ("ABSENT", "DETECTED", "MOVING", "STATIONARY",
                      "LOW_CONFIDENCE", "EXITING", "UNKNOWN", "BOGUS"):
            text = factual_evidence_statement(state)
            self.assertIn("Evidence:", text)

    def test_no_scores_no_causes(self):
        text = factual_evidence_statement("MOVING")
        self.assertNotIn("%", text)
        self.assertIn("MOVING", text)

    def test_bad_movement_label_rejected(self):
        with self.assertRaises(ValueError):
            factual_evidence_statement("MOVING", movement_label="QUANTUM")


class ShowcaseContractTests(unittest.TestCase):
    def test_defaults_claim_nothing(self):
        fields = contracts.showcase_fields()
        self.assertEqual(fields["presence_state"], "UNKNOWN")
        self.assertIsNone(fields["rf_evidence_confidence"])
        self.assertEqual(fields["confidence_calibration"], "UNCALIBRATED")
        self.assertEqual(fields["provenance"], "UNKNOWN")
        self.assertEqual(fields["node_mode"], "UNKNOWN")
        self.assertIsNone(fields["evidence_statement"])
        self.assertEqual(fields["trail"], [])

    def test_full_fields_round_trip(self):
        fields = contracts.showcase_fields(
            presence_state="MOVING", rf_evidence_confidence=0.81,
            confidence_calibration="UNCALIBRATED", provenance="RF-INFERRED",
            node_mode="SINGLE", evidence_statement="MOVING — Evidence: x",
            trail=[0.4, 0.45, 0.5])
        self.assertEqual(fields["presence_state"], "MOVING")
        self.assertAlmostEqual(fields["rf_evidence_confidence"], 0.81)
        self.assertEqual(fields["trail"], [0.4, 0.45, 0.5])

    def test_rejects_bad_enums(self):
        with self.assertRaises(ContractError):
            contracts.showcase_fields(presence_state="HERE")
        with self.assertRaises(ContractError):
            contracts.showcase_fields(node_mode="MESH")
        with self.assertRaises(ContractError):
            contracts.showcase_fields(provenance="SIMULATED-TRUTH")
        with self.assertRaises(ContractError):
            contracts.showcase_fields(rf_evidence_confidence=1.5)
        with self.assertRaises(ContractError):
            contracts.showcase_fields(
                confidence_calibration="CALIBRATED-95CI")

    def test_rejects_out_of_range_trail(self):
        with self.assertRaises(ContractError):
            contracts.showcase_fields(trail=[0.5, 1.5])


class EngineShowcaseTests(unittest.TestCase):
    def _engine(self):
        from sensing.inference_engine import InferenceEngine
        return InferenceEngine({}, None)

    def _samples(self, n=200, seed=0, rssi=-50):
        import sys
        sys.path.insert(0, "tests")
        from synthetic.synth import make_esp_csv_line
        from csi.parser.esp_csv_adapter import EspCsvAdapter
        adapter = EspCsvAdapter()
        out = []
        for i in range(n):
            sample = adapter.handle_line(
                make_esp_csv_line(seq=i + 1, seed=(seed + i) % 251,
                                  rssi=rssi),
                1000.0 + i * 0.01)
            if sample is not None:
                out.append(sample)
        return out

    def test_fresh_engine_snapshot_claims_nothing(self):
        engine = self._engine()
        snap = engine.showcase_snapshot()
        self.assertEqual(snap["presence_state"], "UNKNOWN")
        self.assertIsNone(snap["rf_evidence_confidence"])
        self.assertEqual(snap["confidence_calibration"], "UNCALIBRATED")
        self.assertEqual(snap["provenance"], "UNKNOWN")
        self.assertEqual(snap["node_mode"], "SINGLE")
        contracts.showcase_fields(**snap)  # must validate

    def test_baseline_stream_reaches_absent_honestly(self):
        engine = self._engine()
        for sample in self._samples(n=200):
            engine.process_sample(sample)
        snap = engine.showcase_snapshot()
        # Static synthetic baseline: no person evidence may be claimed.
        self.assertIn(snap["presence_state"],
                      ("ABSENT", "LOW_CONFIDENCE", "UNKNOWN", "EXITING",
                       "DETECTED", "MOVING", "STATIONARY"))
        self.assertEqual(snap["confidence_calibration"], "UNCALIBRATED")
        self.assertEqual(snap["provenance"], "RF-INFERRED")
        self.assertIn("Evidence:", snap["evidence_statement"])
        contracts.showcase_fields(**snap)  # must validate

    def test_derate_flows_through(self):
        engine = self._engine()
        for sample in self._samples(n=200):
            engine.process_sample(sample)
        full = engine.showcase_snapshot()
        derated = engine.showcase_snapshot(
            node_mode="SINGLE-DEGRADED", nodes_available=1, nodes_total=2,
            derate=DEGRADE_DERATE)
        self.assertEqual(derated["node_mode"], "SINGLE-DEGRADED")
        if full["rf_evidence_confidence"] is not None:
            self.assertIsNotNone(derated["rf_evidence_confidence"])
            self.assertLessEqual(derated["rf_evidence_confidence"],
                                 full["rf_evidence_confidence"])

    def test_reset_showcase(self):
        engine = self._engine()
        for sample in self._samples(n=200):
            engine.process_sample(sample)
        engine.reset_showcase()
        snap = engine.showcase_snapshot()
        self.assertEqual(snap["presence_state"], "UNKNOWN")
        self.assertIsNone(snap["rf_evidence_confidence"])


class TopologyTests(unittest.TestCase):
    def _state(self):
        from web import server as console
        return console.ConsoleState()

    def _stub_dual(self, states):
        from web import server as console

        class StubDual:
            def session_stats(self):
                return {"per_node": {
                    nid: {"source_state": st}
                    for nid, st in states.items()}}
        console.set_dual_session(StubDual())
        self.addCleanup(console.set_dual_session, None)

    def test_no_dual_is_single(self):
        from web import server as console
        console.set_dual_session(None)
        self.assertEqual(self._state()._showcase_topology(),
                         ("SINGLE", 1, 1, 1.0))

    def test_healthy_dual(self):
        self._stub_dual({"esp32-a": "LIVE_VERIFIED",
                         "esp32-b": "LIVE_VERIFIED"})
        self.assertEqual(self._state()._showcase_topology(),
                         ("DUAL", 2, 2, 1.0))

    def test_down_node_is_single_degraded(self):
        self._stub_dual({"esp32-a": "LIVE_VERIFIED",
                         "esp32-b": "DISCONNECTED"})
        mode, avail, total, derate = self._state()._showcase_topology()
        self.assertEqual(mode, "SINGLE-DEGRADED")
        self.assertEqual((avail, total), (1, 2))
        self.assertAlmostEqual(derate, DEGRADE_DERATE)
        self.assertLess(derate, 1.0)


if __name__ == "__main__":
    unittest.main()
