"""Petakan ulang baris sensor yang sudah ada ke field ThingSpeak yang benar.

Template di routers/channels.py cuma dipakai saat kanal BARU dibuat. Baris yang
sudah terlanjur tersimpan tetap salah, dan itulah yang bikin dashboard
menampilkan "Probe Analog 2 = 1507%": field5 kanal pendukung Node 1 sebenarnya
arus terpampat (0 A masuk, 1,507 A keluar), bukan kelembapan.

Jalankan dari folder backend/:

    python -m scripts.remap_sensors --dry-run     # lihat dulu, tidak menulis
    python -m scripts.remap_sensors               # terapkan

Ambang batas ikut dikosongkan, karena ambang lama dipasang terhadap field yang
salah (dan yang di field benar pun jelas angka contekan: suhu tanah 2-10 C,
EC 10-20 uS/cm, kelembapan udara 20-30%). Pakai --keep-thresholds kalau mau
mempertahankannya untuk field yang pemetaannya tidak berubah.
"""

import argparse
import asyncio
import sys
from typing import Any, Dict, List, Tuple


def rencana_remap(
    sensor_lama: List[Any],
    template: List[Dict[str, str]],
    keep_thresholds: bool = False,
) -> Tuple[List[Dict], List[Dict], List[Any]]:
    """Bandingkan sensor yang ada dengan template, tanpa menyentuh database.

    Mengembalikan (dibuat, diperbarui, dihapus). Dipisah dari I/O supaya bisa
    diuji tanpa Postgres.
    """
    per_field = {}
    for s in sensor_lama:
        per_field.setdefault(s.thingspeak_field, []).append(s)

    dibuat: List[Dict] = []
    diperbarui: List[Dict] = []
    terpakai = set()

    for t in template:
        cocok = per_field.get(t["field"], [])
        if cocok:
            s = cocok[0]
            terpakai.add(id(s))
            perubahan = {}
            if s.name != t["name"]:
                perubahan["name"] = (s.name, t["name"])
            if s.unit != t["unit"]:
                perubahan["unit"] = (s.unit, t["unit"])
            if s.type != t["type"]:
                perubahan["type"] = (s.type, t["type"])
            if not keep_thresholds and (s.min_threshold is not None or s.max_threshold is not None):
                perubahan["thresholds"] = ((s.min_threshold, s.max_threshold), (None, None))
            if perubahan:
                diperbarui.append({"sensor": s, "field": t["field"], "perubahan": perubahan})
        else:
            dibuat.append(t)

    dihapus = [s for s in sensor_lama if id(s) not in terpakai]
    return dibuat, diperbarui, dihapus


async def jalankan(dry_run: bool, keep_thresholds: bool) -> int:
    from app.core.database import AsyncSessionLocal
    from app.models.sensor import Sensor
    from app.repositories import channel_repo, node_repo
    from app.routers.channels import pilih_template

    total_buat = total_ubah = total_hapus = 0

    async with AsyncSessionLocal() as db:
        nodes = await node_repo.list_all(db, limit=1000)
        if not nodes:
            print("Tidak ada node di database.")
            return 1

        for node in nodes:
            layout = node.field_layout or "node2_plain"
            print(f"\n=== {node.node_id} — {node.name}  [layout: {layout}] ===")
            if layout == "node2_plain":
                print("    catatan: layout masih default. Kalau ini Node 1 (punya probe")
                print("    analog & arus terpampat), setel dulu field_layout='node1_packed'")
                print("    sebelum remap, kalau tidak field5 tetap dibaca sebagai satu angka.")

            channels = await channel_repo.get_by_node_id(db, node.id)
            if not channels:
                print("    (tidak ada kanal)")
                continue

            for urut, ch in enumerate(channels):
                template = pilih_template(layout, ch.label, urut)
                sensor_lama = [s for s in await _sensors_kanal(db, Sensor, node.id, ch.id)]
                dibuat, diperbarui, dihapus = rencana_remap(
                    sensor_lama, template, keep_thresholds
                )

                print(f"\n  -- kanal {ch.channel_id} (label: {ch.label!r})")
                for t in dibuat:
                    print(f"     + BUAT   {t['field']:12s} {t['name']} [{t['unit']}]")
                for u in diperbarui:
                    bagian = ", ".join(
                        f"{k}: {v[0]!r} -> {v[1]!r}" for k, v in u["perubahan"].items()
                    )
                    print(f"     ~ UBAH   {u['field']:12s} {bagian}")
                for s in dihapus:
                    print(f"     - HAPUS  {s.thingspeak_field:12s} {s.name!r} (tidak ada di peta field)")
                if not (dibuat or diperbarui or dihapus):
                    print("     (sudah sesuai)")

                total_buat += len(dibuat)
                total_ubah += len(diperbarui)
                total_hapus += len(dihapus)

                if dry_run:
                    continue

                for s in dihapus:
                    await db.delete(s)
                for u in diperbarui:
                    s = u["sensor"]
                    p = u["perubahan"]
                    if "name" in p:
                        s.name = p["name"][1]
                    if "unit" in p:
                        s.unit = p["unit"][1]
                    if "type" in p:
                        s.type = p["type"][1]
                    if "thresholds" in p:
                        s.min_threshold = None
                        s.max_threshold = None
                for t in dibuat:
                    db.add(Sensor(
                        node_id=node.id,
                        channel_id=ch.id,
                        type=t["type"],
                        name=t["name"],
                        unit=t["unit"],
                        thingspeak_field=t["field"],
                        enabled=True,
                    ))

        if dry_run:
            print(f"\n[DRY RUN] {total_buat} dibuat, {total_ubah} diubah, {total_hapus} dihapus. "
                  f"Tidak ada yang ditulis.")
        else:
            await db.commit()
            print(f"\nSelesai: {total_buat} dibuat, {total_ubah} diubah, {total_hapus} dihapus.")
    return 0


async def _sensors_kanal(db, Sensor, node_id, channel_id):
    from sqlalchemy import select
    hasil = await db.execute(
        select(Sensor).where(Sensor.node_id == node_id, Sensor.channel_id == channel_id)
    )
    return list(hasil.scalars().all())


def main() -> int:
    p = argparse.ArgumentParser(description="Remap sensor ke field ThingSpeak yang benar")
    p.add_argument("--dry-run", action="store_true", help="tampilkan rencana, jangan menulis")
    p.add_argument("--keep-thresholds", action="store_true",
                   help="pertahankan ambang lama untuk field yang pemetaannya tidak berubah")
    args = p.parse_args()
    return asyncio.run(jalankan(args.dry_run, args.keep_thresholds))


if __name__ == "__main__":
    sys.exit(main())
