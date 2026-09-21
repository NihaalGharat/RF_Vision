"""Unit tests: ESP32 ``CSI_DATA`` CSV adapter."""

import time
import unittest

from csi.parser.csi_parser import PacketError, parse_line
from csi.parser.esp_csv_adapter import (
    EspCsvAdapter,
    parse_esp_csv_line,
)
from tests.synthetic.synth import make_esp_csv_line


class TestEspCsvAdapter(unittest.TestCase):
    def test_good_line_parses(self):
        sample = parse_esp_csv_line(make_esp_csv_line(seq=7, seed=3))
        self.assertEqual(sample.seq, 7)
        self.assertEqual(sample.rssi, -50)
        self.assertEqual(sample.channel, 6)
        self.assertEqual(sample.mac, "AABBCCDDEEFF")
        self.assertEqual(sample.n_subcarriers, 64)
        self.assertFalse(sample.first_word_invalid)
        self.assertEqual(sample.sig_mode, 1)
        self.assertEqual(sample.cwb, 0)

    def test_adapter_matches_json_path(self):
        # Same I/Q seed through both wire formats must give identical
        # amplitude vectors (adapter changes transport, not signal).
        from tests.synthetic.synth import make_json_line
        csv_sample = parse_esp_csv_line(make_esp_csv_line(seq=1, seed=11))
        json_sample = parse_line(make_json_line(seq=1, seed=11)
                                 .split("#CSI ", 1)[1], time.time())
        import numpy as np
        np.testing.assert_allclose(
            abs(csv_sample.csi.astype(float)[0::2]
                + 1j * csv_sample.csi.astype(float)[1::2]),
            abs(json_sample.csi.astype(float)[0::2]
                + 1j * json_sample.csi.astype(float)[1::2]))

    def test_field_mapping(self):
        line = make_esp_csv_line(seq=42, rssi=-61, channel=11)
        s = parse_esp_csv_line(line, local_ts=1700000000.0)
        self.assertEqual((s.seq, s.rssi, s.channel), (42, -61, 11))
        self.assertEqual(s.ts_local, 1700000000.0)
        self.assertEqual(s.ts_esp32_us, 123456789)

    def test_first_word_flag(self):
        s = parse_esp_csv_line(make_esp_csv_line(first_word_invalid=1))
        self.assertTrue(s.first_word_invalid)

    def test_bad_tag(self):
        with self.assertRaises(PacketError):
            parse_esp_csv_line("LOG,something,else")

    def test_wrong_column_count(self):
        with self.assertRaises(PacketError):
            parse_esp_csv_line("CSI_DATA,1,2,3")

    def _head(self, line):
        # Split before the quoted payload field (payload itself has commas).
        return line.rsplit(',"[', 1)[0]

    def test_len_mismatch(self):
        line = make_esp_csv_line()
        with self.assertRaises(PacketError):
            parse_esp_csv_line(self._head(line) + ',"[1,2,3]"')

    def test_out_of_range_payload(self):
        line = make_esp_csv_line()
        bad = '"[' + ",".join(["0"] * 127 + ["999"]) + ']"'
        with self.assertRaises(PacketError):
            parse_esp_csv_line(self._head(line) + "," + bad)

    def test_adapter_stats(self):
        adapter = EspCsvAdapter()
        self.assertIsNone(adapter.handle_line(""))
        self.assertIsNone(adapter.handle_line("I (123) wifi: something"))
        adapter.handle_line(make_esp_csv_line())
        self.assertEqual(adapter.stats.parsed, 1)
        with self.assertRaises(PacketError):
            adapter.handle_line("CSI_DATA,1,2,3")
        self.assertEqual(adapter.stats.rejected_total, 1)
        self.assertEqual(adapter.stats.lines_seen, 2)


if __name__ == "__main__":
    unittest.main()
