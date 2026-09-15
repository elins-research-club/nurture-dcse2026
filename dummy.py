"""
dummy_gconnect_writer.py

Writes simulated sensor data to all four Nurture ThingSpeak channels so the
backend and Vue frontend can be tested without the ESP32 nodes attached.

Mirrors the real firmware's behaviour:
  - Main channel and support channel are written 5 seconds apart, matching
    INTERVAL_THINGSPEAK / INTERVAL_THINGSPEAK_PENDUKUNG in the .ino
  - Fields are OMITTED (not zeroed) when a reading is "invalid", exactly like
    the firmware's `if (dataNpk.valid)` and `if (persenSoil[i] >= 0.0)` guards
  - Modbus code (support field3) is ALWAYS sent, including on simulated failure
  - Actuator state is packed into a bitmask on support field8

Channel layout (Verified against firmware .ino)
-----------------------------------------------
Node 1:
  Main (3461921):
    field1 N | field2 P | field3 K | field4 pH | field5 EC
    field6 Rata-rata Kelembapan Tanah % | field7 Suhu Luar C | field8 Lembab Luar %
  Support (3461926):
    field1 Suhu Tanah C | field2 Tegangan Baterai V | field3 Tegangan Load V
    field4 Arus Baterai A | field5 Arus Load A | field6 Suhu Dalam Panel C
    field7 Status Aktuator (bitmask) | field8 Daya Beban Aktual W

Node 2:
  Main (3461925):
    field1 N | field2 P | field3 K | field4 pH | field5 EC
    field6 Suhu Luar C | field7 Lembab Luar % | field8 Daya Beban Aktual W
  Support (3461928):
    field1 Suhu Tanah C | field2 Kelembapan Probe NPK % | field3 Tegangan Baterai V
    field4 Tegangan Load V | field5 Arus Baterai A | field6 Arus Load A
    field7 Suhu Dalam Panel C | field8 Status Aktuator (bitmask)

Usage
-----
    pip install requests
    python dummy_gconnect_writer.py                    # run forever, both nodes
    python dummy_gconnect_writer.py --cycles 5         # 5 rounds then stop
    python dummy_gconnect_writer.py --node node1       # one node only
    python dummy_gconnect_writer.py --interval 20      # faster cycle
    python dummy_gconnect_writer.py --fail-rate 0.5    # simulate flaky Modbus
    python dummy_gconnect_writer.py --dry-run          # print payloads, send nothing
"""

import argparse
import math
import random
import sys
import time
from datetime import datetime

import requests

THINGSPEAK_UPDATE_URL = "https://api.thingspeak.com/update"

# Write keys per node. Main and support channels are separate channels.
NODES = {
    "node1": {
        "device_id": "ESP32-S3-AGRI-01",
        "main_key": "VIV896ZGWAGL5GZ4",
        "support_key": "JGXI77JIORMKCSVI",
    },
    "node2": {
        "device_id": "ESP32-S3-AGRI-02",
        "main_key": "4Q10KA98O9SJRBX2",
        "support_key": "Y9WHRFN4ZDJXCTOR",
    },
}

# Matches the firmware: 30s between main sends, support follows 5s later.
DEFAULT_INTERVAL = 30
SUPPORT_OFFSET = 5

# ModbusMaster status codes. 0x00 = success, 0xE2 = response timed out.
MODBUS_SUCCESS = 0
MODBUS_TIMEOUT = 226


class NodeSimulator:
    """Holds slow-moving state so consecutive readings look plausible rather
    than being fresh random numbers every cycle."""

    def __init__(self, node_key, seed=None):
        self.node_key = node_key
        self.rng = random.Random(seed)

        # Soil chemistry drifts slowly
        self.nitrogen = self.rng.uniform(20, 60)
        self.phosphorus = self.rng.uniform(10, 40)
        self.potassium = self.rng.uniform(15, 50)
        self.ph = self.rng.uniform(5.8, 6.8)
        self.ec = self.rng.uniform(800, 1500)

        # Soil moisture:
        # Node 1 uses 2 active analog probes + NPK probe -> average
        # Node 2 uses NPK probe only (JUMLAH_SOIL_AKTIF = 0)
        self.probes = [self.rng.uniform(35, 55) for _ in range(2)]
        self.npk_moisture = self.rng.uniform(35, 55)
        self.enclosure_temp = self.rng.uniform(30, 34)

        # INA226 power metrics simulation
        self.tegangan_baterai = self.rng.uniform(12.2, 12.8)
        self.tegangan_load = self.rng.uniform(3.28, 3.32)

        self.irrigating = False
        self.irrigation_left = 0

    def _drift(self, value, lo, hi, step):
        value += self.rng.uniform(-step, step)
        return max(lo, min(hi, value))

    @staticmethod
    def _diurnal(hour, base, amplitude, peak_hour=14):
        """Sinusoid peaking at peak_hour, used for air and soil temperature."""
        return base + amplitude * math.sin(2 * math.pi * (hour - peak_hour + 6) / 24)

    def step(self, now, fail_rate, cycle=0, spike_interval=0):
        hour = now.hour + now.minute / 60
        is_node1 = (self.node_key == "node1")

        # --- Environment -------------------------------------------------
        air_temp = self._diurnal(hour, base=27, amplitude=5) + self.rng.uniform(-0.6, 0.6)
        air_humidity = max(40, min(95, 88 - (air_temp - 22) * 3 + self.rng.uniform(-3, 3)))

        # Soil temperature lags air temperature and swings less
        soil_temp = self._diurnal(hour, base=25, amplitude=2.5, peak_hour=17)
        soil_temp += self.rng.uniform(-0.3, 0.3)

        self.enclosure_temp = self._drift(
            air_temp + self.rng.uniform(4, 8), 26, 52, 0.6
        )

        # --- Soil moisture & irrigation (Node 1 only has valve) ----------
        if is_node1:
            if min(self.probes) <= 33 and not self.irrigating:
                self.irrigating = True
                self.irrigation_left = self.rng.randint(3, 6)

            for i in range(2):
                if self.irrigating:
                    self.probes[i] += self.rng.uniform(3, 6)
                else:
                    self.probes[i] -= self.rng.uniform(0.2, 0.7)
                self.probes[i] = max(12, min(75, self.probes[i]))

            if self.irrigating:
                self.irrigation_left -= 1
                if self.irrigation_left <= 0 or min(self.probes) >= 58:
                    self.irrigating = False

            self.npk_moisture = self._drift(
                sum(self.probes) / 2 + self.rng.uniform(-4, 4), 12, 75, 1.5
            )
            # Rata-rata 2 probe analog + probe NPK
            rata_tanah = round((self.probes[0] + self.probes[1] + self.npk_moisture) / 3.0, 1)
        else:
            # Node 2: No analog probes, no irrigation valve
            self.irrigating = False
            self.npk_moisture = self._drift(self.npk_moisture, 25, 75, 0.8)
            rata_tanah = None

        # --- Soil chemistry ----------------------------------------------
        self.nitrogen = self._drift(self.nitrogen, 5, 80, 2.5)
        self.phosphorus = self._drift(self.phosphorus, 5, 60, 1.8)
        self.potassium = self._drift(self.potassium, 5, 70, 2.5)
        self.ph = self._drift(self.ph, 5.0, 7.5, 0.04)
        self.ec = self._drift(self.ec, 400, 2000, 35)

        # --- Simulated Modbus failure ------------------------------------
        npk_ok = self.rng.random() >= fail_rate

        # --- Actuators (Kipas, Lampu, Valve) -----------------------------
        # Node 1: Fan on at >= 34°C, has valve
        # Node 2: Fan on at >= 38°C, no valve
        fan_thresh = 34.0 if is_node1 else 38.0
        kipas = self.enclosure_temp >= fan_thresh
        lampu = hour >= 18 or hour < 6
        valve = self.irrigating if is_node1 else False

        bitmask = 0
        if kipas:
            bitmask |= 0b0001
        if lampu:
            bitmask |= 0b0010
        if valve:
            bitmask |= 0b0100

        # --- INA226 Power Metrics ----------------------------------------
        self.tegangan_baterai = self._drift(self.tegangan_baterai, 11.5, 13.8, 0.04)
        self.tegangan_load = self._drift(self.tegangan_load, 3.25, 3.35, 0.01)

        base_arus_load = 0.18
        if kipas:
            base_arus_load += 0.35
        if lampu:
            base_arus_load += 0.25
        if valve:
            base_arus_load += 0.40
        arus_load = round(base_arus_load + self.rng.uniform(-0.02, 0.02), 3)
        daya_load = round(self.tegangan_load * arus_load, 2)

        # Arus baterai: siang = charging (Node 1 firmware membalik tanda minus), malam = discharging
        is_daylight = 7 <= hour < 17
        if is_daylight:
            i_bat_mag = self.rng.uniform(0.6, 1.5)
            # Firmware Node 1: arus_baterai = -(rawI / 1000.0)
            # Firmware Node 2: arus_baterai = rawI / 1000.0
            arus_baterai = round(-i_bat_mag if is_node1 else i_bat_mag, 3)
        else:
            arus_baterai = round(self.rng.uniform(0.15, 0.45), 3)

        # --- Periodic Threshold Anomaly Injection (Spikes) ----------------
        spike_info = None
        if spike_interval > 0 and cycle > 0 and cycle % spike_interval == 0:
            scenarios = [
                ("Suhu Udara Panas", "air_temp", 36.8, "Max: 34.0°C"),
                ("Kelembapan Tanah Kering", "moisture", 24.5, "Min: 35.0%"),
                ("Nitrogen Berlebih", "nitrogen", 72.5, "Max: 60.0 mg/kg"),
                ("pH Tanah Asam", "ph", 5.15, "Min: 5.8"),
                ("eC Salinitas Tinggi", "ec", 2150, "Max: 1800 µS/cm"),
            ]
            s_name, s_field, s_val, s_threshold = scenarios[(cycle // spike_interval - 1) % len(scenarios)]
            if s_field == "air_temp":
                air_temp = s_val
            elif s_field == "moisture":
                if is_node1:
                    rata_tanah = s_val
                else:
                    self.npk_moisture = s_val
            elif s_field == "nitrogen":
                self.nitrogen = s_val
            elif s_field == "ph":
                self.ph = s_val
            elif s_field == "ec":
                self.ec = s_val
            spike_info = f"[!] [THRESHOLD SPIKE] {s_name} -> {s_val} ({s_threshold})"

        # --- Build payloads according to verified .ino firmware ----------
        main = {}
        support = {}

        if is_node1:
            # NODE 1:
            # Channel 1 (Main):
            # field1..5: NPK
            if npk_ok:
                main["field1"] = round(self.nitrogen, 1)
                main["field2"] = round(self.phosphorus, 1)
                main["field3"] = round(self.potassium, 1)
                main["field4"] = round(self.ph, 2)
                main["field5"] = round(self.ec)
            # field6: Rata-rata Kelembapan Tanah (%)
            if rata_tanah is not None:
                main["field6"] = rata_tanah
            # field7-8: Suhu & Lembab Luar Rata-rata
            main["field7"] = round(air_temp, 2)
            main["field8"] = round(air_humidity, 2)

            # Channel 2 (Support):
            if npk_ok:
                support["field1"] = round(soil_temp, 1)
            support["field2"] = round(self.tegangan_baterai, 2)
            support["field3"] = round(self.tegangan_load, 2)
            support["field4"] = arus_baterai
            support["field5"] = arus_load
            support["field6"] = round(self.enclosure_temp, 1)
            support["field7"] = bitmask
            support["field8"] = daya_load

        else:
            # NODE 2:
            # Channel 1 (Main):
            # field1..5: NPK
            if npk_ok:
                main["field1"] = round(self.nitrogen, 1)
                main["field2"] = round(self.phosphorus, 1)
                main["field3"] = round(self.potassium, 1)
                main["field4"] = round(self.ph, 2)
                main["field5"] = round(self.ec)
            # field6-7: Suhu & Lembab Luar Rata-rata
            main["field6"] = round(air_temp, 2)
            main["field7"] = round(air_humidity, 2)
            # field8: Daya Beban Aktual (Watt)
            main["field8"] = daya_load

            # Channel 2 (Support):
            if npk_ok:
                support["field1"] = round(soil_temp, 1)
                support["field2"] = round(self.npk_moisture, 1)
            support["field3"] = round(self.tegangan_baterai, 2)
            support["field4"] = round(self.tegangan_load, 2)
            support["field5"] = arus_baterai
            support["field6"] = arus_load
            support["field7"] = round(self.enclosure_temp, 1)
            support["field8"] = bitmask

        return main, support, npk_ok, spike_info


def decode_bitmask(value):
    return {
        "kipas": bool(value & 0b0001),
        "lampu": bool(value & 0b0010),
        "valve": bool(value & 0b0100),
    }


def post(write_key, payload, dry_run, timeout=10):
    """Returns the ThingSpeak entry id, or 0 if the write was rejected."""
    if dry_run:
        return -1

    body = {**payload, "api_key": write_key}
    try:
        resp = requests.post(THINGSPEAK_UPDATE_URL, data=body, timeout=timeout)
        resp.raise_for_status()
        return int(resp.text.strip())
    except requests.RequestException as exc:
        print(f"    ! request failed: {exc}")
        return None
    except ValueError:
        print(f"    ! unexpected response: {resp.text[:80]!r}")
        return None


def report(label, payload, entry_id, dry_run):
    stamp = datetime.now().strftime("%H:%M:%S")
    fields = " ".join(f"{k}={v}" for k, v in sorted(payload.items()))

    if dry_run:
        status = "dry-run"
    elif entry_id is None:
        status = "ERROR"
    elif entry_id == 0:
        status = "REJECTED (rate limit or bad key)"
    else:
        status = f"entry #{entry_id}"

    print(f"[{stamp}] {label:<22} {status}")
    print(f"           {fields}")


def main():
    parser = argparse.ArgumentParser(
        description="Write dummy sensor data to all four Nurture ThingSpeak channels"
    )
    parser.add_argument("--node", choices=["node1", "node2", "both"], default="both")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL,
                        help="Seconds between cycles (ThingSpeak floor is 15s per channel)")
    parser.add_argument("--cycles", type=int, default=0,
                        help="Number of cycles to run (0 = forever)")
    parser.add_argument("--fail-rate", type=float, default=0.15,
                        help="Probability of a simulated Modbus failure per cycle (0-1)")
    parser.add_argument("--spike-interval", type=int, default=3,
                        help="Inject a threshold spike anomaly every N cycles for alert testing (default: 3 cycles, 0 = disabled)")
    parser.add_argument("--seed", type=int, default=None,
                        help="Seed for reproducible output")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print payloads without sending anything")
    args = parser.parse_args()

    if args.interval < 15:
        print("Warning: interval below 15s will hit ThingSpeak's write limit.\n",
              file=sys.stderr)

    targets = list(NODES) if args.node == "both" else [args.node]
    sims = {
        name: NodeSimulator(name, seed=None if args.seed is None else args.seed + i)
        for i, name in enumerate(targets)
    }

    print(f"Writing to: {', '.join(targets)}")
    print(f"Interval {args.interval}s, support channel +{SUPPORT_OFFSET}s, "
          f"fail rate {args.fail_rate:.0%}, spike every {args.spike_interval} cycles"
          f"{'  [DRY RUN]' if args.dry_run else ''}\n")

    cycle = 0
    try:
        while args.cycles == 0 or cycle < args.cycles:
            cycle += 1
            now = datetime.now()
            print(f"--- cycle {cycle} ---")

            pending = []
            for name in targets:
                main_payload, support_payload, npk_ok, spike_info = sims[name].step(
                    now, args.fail_rate, cycle=cycle, spike_interval=args.spike_interval
                )
                if spike_info:
                    print(f"           {spike_info}")
                entry = post(NODES[name]["main_key"], main_payload, args.dry_run)
                report(f"{name} main", main_payload, entry, args.dry_run)
                if not npk_ok:
                    print("           (simulated Modbus failure: NPK fields omitted)")
                pending.append((name, support_payload))

            # Mirror the firmware's 5s gap before hitting the support channel
            if not args.dry_run:
                time.sleep(SUPPORT_OFFSET)

            for name, support_payload in pending:
                entry = post(NODES[name]["support_key"], support_payload, args.dry_run)
                report(f"{name} support", support_payload, entry, args.dry_run)
                actuator_key = "field7" if name == "node1" else "field8"
                state = decode_bitmask(support_payload[actuator_key])
                on = [k for k, v in state.items() if v] or ["all off"]
                print(f"           actuators: {', '.join(on)}")

            print()

            if args.cycles == 0 or cycle < args.cycles:
                wait = max(0.0, args.interval - (0 if args.dry_run else SUPPORT_OFFSET))
                time.sleep(wait)

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()