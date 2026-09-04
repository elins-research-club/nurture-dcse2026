"""Klasifikasi kondisi tanah -- memisahkan yang dikutip dari yang dirancang.

Aturan main modul ini, diambil dari CLAUDE.md dan tidak boleh dilonggarkan
tanpa alasan yang ditulis:

1. BATAS KELAS yang punya sumber terbit ditandai `dasar="pustaka"` lengkap
   dengan sitasinya. Yang tidak punya sumber TIDAK dikarang di sini.
2. PEMETAAN kelas -> status (aman / perlu perhatian / tidak aman) adalah
   keputusan perancangan, bukan kutipan. Semuanya ditandai
   `dasar="peneliti"` dan mengikuti pendekatan SMAF (Andrews dkk., 2004).
   Bab metodologi harus menyebut ini dirancang peneliti, bukan dikutip.
3. Parameter yang satuannya belum setara dengan kriteria pustaka
   (N/P/K, EC, kelembapan probe) TIDAK dipaksa masuk kelas. Ia dilaporkan
   apa adanya dengan alasan kenapa belum bisa diklasifikasi.
4. Vonis memakai kelas terburuk (hukum minimum Liebig), bukan rata-rata.
   Rata-rata membuat NPK yang bagus menutupi pH yang mematikan.
5. Status tanah dan status hara dipisah. NPK rendah berarti "perlu dipupuk",
   bukan "tanah rusak".

Tidak ada skor angka tunggal yang dikeluarkan modul ini. Kalau nanti dibuat,
bobot dan ambangnya wajib ikut ditandai `dasar="peneliti"`.
"""

from typing import Any, Dict, List, Optional

DASAR_PUSTAKA = "pustaka"
DASAR_PENELITI = "peneliti"

STATUS_AMAN = "aman"
STATUS_PERHATIAN = "perlu_perhatian"
STATUS_TIDAK_AMAN = "tidak_aman"
STATUS_TIDAK_DIKETAHUI = "tidak_diketahui"

# Makin besar makin membatasi. Dipakai untuk memilih parameter pembatas.
_URUTAN_STATUS = {
    STATUS_TIDAK_DIKETAHUI: 0,
    STATUS_AMAN: 1,
    STATUS_PERHATIAN: 2,
    STATUS_TIDAK_AMAN: 3,
}

LABEL_STATUS = {
    STATUS_AMAN: "Aman",
    STATUS_PERHATIAN: "Perlu perhatian",
    STATUS_TIDAK_AMAN: "Tidak aman",
    STATUS_TIDAK_DIKETAHUI: "Belum dapat dinilai",
}

SITASI = {
    "ph": "Eviati & Sulaeman (2009), Petunjuk Teknis Analisis Kimia Tanah, "
          "Tanaman, Air, dan Pupuk, Balai Penelitian Tanah",
    "npk": "Eviati & Sulaeman (2009), Balai Penelitian Tanah",
    "ec_kelas": "Soil Survey Division Staff (1993), Soil Survey Manual, "
                "USDA Handbook 18",
    "ec_ambang": "Richards (1954), USDA Handbook 60",
    "lengas": "Linn & Doran (1984), SSSAJ 48(6):1267-1272",
    "pemetaan": "Pemetaan kelas ke status dirancang peneliti mengikuti "
                "pendekatan SMAF (Andrews dkk., 2004); bukan kutipan.",
}

# --- pH: satu-satunya parameter yang saat ini bisa langsung diklasifikasi ----
# Batas kelas dikutip; kolom status adalah pemetaan rancangan peneliti.
_KELAS_PH = [
    (None, 4.5, "sangat masam", STATUS_TIDAK_AMAN),
    (4.5, 5.6, "masam", STATUS_PERHATIAN),
    (5.6, 6.6, "agak masam", STATUS_AMAN),
    (6.6, 7.6, "netral", STATUS_AMAN),
    (7.6, 8.6, "agak alkalis", STATUS_PERHATIAN),
    (8.6, None, "alkalis", STATUS_TIDAK_AMAN),
]

# --- EC: kelas salinitas USDA, dalam dS/m dan mengasumsikan ECe -------------
_KELAS_EC = [
    (None, 2.0, "nonsaline", STATUS_AMAN),
    (2.0, 4.0, "very slightly saline", STATUS_AMAN),
    (4.0, 8.0, "slightly saline", STATUS_PERHATIAN),
    (8.0, 16.0, "moderately saline", STATUS_TIDAK_AMAN),
    (16.0, None, "strongly saline", STATUS_TIDAK_AMAN),
]

# Sensor melaporkan EC ruah in-situ, kriteria memakai ECe (ekstrak pasta jenuh).
# Beda pengukuran, jadi kelasnya indikatif sampai ada kalibrasi laboratorium.
CATATAN_EC = (
    "Sensor mengukur EC ruah in-situ, sedangkan kelas salinitas USDA "
    "mengasumsikan ECe (ekstrak pasta jenuh). Kelas di bawah ini indikatif, "
    "belum setara, dan tidak boleh dilaporkan sebagai salinitas terukur."
)

CATATAN_NPK = (
    "Sensor melaporkan mg/kg hasil turunan konduktivitas, sedangkan kriteria "
    "Balai Penelitian Tanah memakai satuan laboratorium (% N-total, ppm P2O5). "
    "Keduanya tidak setara tanpa kalibrasi terhadap uji laboratorium, sehingga "
    "nilai ini tidak dikelaskan."
)

CATATAN_P_K = (
    "Batas kelas P dan K bergantung metode ekstraksi (Bray I, Olsen, HCl 25%, "
    "NH4OAc). Metode yang dipakai harus ditetapkan dulu sebelum kelas bisa "
    "diterapkan."
)

CATATAN_LENGAS = (
    "Probe analog memetakan ADC secara linear di antara titik kalibrasi basah "
    "dan kering milik operator. Itu bukan kadar air volumetrik dan bukan WFPS. "
    "Konversi ke WFPS memerlukan kerapatan isi (bulk density) setempat."
)

CATATAN_SUHU_TANAH = (
    "Tidak ada klasifikasi kesehatan tanah baku untuk suhu tanah. Nilainya "
    "ditampilkan, tidak diberi status."
)


def _cari_kelas(nilai: float, tabel) -> tuple:
    for bawah, atas, nama, status in tabel:
        if (bawah is None or nilai >= bawah) and (atas is None or nilai < atas):
            return nama, status
    return None, STATUS_TIDAK_DIKETAHUI


def klasifikasi_ph(nilai: Optional[float]) -> Dict[str, Any]:
    """pH tanah -> kelas Eviati & Sulaeman (2009). Satu-satunya yang dikutip penuh."""
    if nilai is None:
        return {
            "parameter": "pH",
            "nilai": None,
            "satuan": "",
            "kelas": None,
            "status": STATUS_TIDAK_DIKETAHUI,
            "dasar_batas": DASAR_PUSTAKA,
            "dasar_status": DASAR_PENELITI,
            "sumber": SITASI["ph"],
            "setara": True,
            "catatan": "Tidak ada pembacaan.",
        }
    kelas, status = _cari_kelas(float(nilai), _KELAS_PH)
    return {
        "parameter": "pH",
        "nilai": round(float(nilai), 2),
        "satuan": "",
        "kelas": kelas,
        "status": status,
        "dasar_batas": DASAR_PUSTAKA,
        "dasar_status": DASAR_PENELITI,
        "sumber": SITASI["ph"],
        "setara": True,
        "catatan": None,
    }


def klasifikasi_ec(nilai_us_cm: Optional[float]) -> Dict[str, Any]:
    """EC sensor (uS/cm) -> kelas salinitas USDA, ditandai belum setara ECe."""
    dasar = {
        "parameter": "EC",
        "satuan": "uS/cm",
        "dasar_batas": DASAR_PUSTAKA,
        "dasar_status": DASAR_PENELITI,
        "sumber": SITASI["ec_kelas"] + "; ambang 4 dS/m: " + SITASI["ec_ambang"],
        "setara": False,
        "catatan": CATATAN_EC,
    }
    if nilai_us_cm is None:
        return {**dasar, "nilai": None, "nilai_ds_m": None, "kelas": None,
                "status": STATUS_TIDAK_DIKETAHUI}

    ds_m = float(nilai_us_cm) / 1000.0
    kelas, status = _cari_kelas(ds_m, _KELAS_EC)
    return {
        **dasar,
        "nilai": round(float(nilai_us_cm), 1),
        "nilai_ds_m": round(ds_m, 3),
        "kelas": kelas,
        "status": status,
    }


def klasifikasi_lengas(
    persen_probe: Optional[float],
    kerapatan_isi: Optional[float] = None,
) -> Dict[str, Any]:
    """Kelembapan probe. Tanpa kerapatan isi, WFPS tidak bisa dihitung."""
    dasar = {
        "parameter": "Kelembapan tanah",
        "satuan": "%",
        "dasar_batas": DASAR_PUSTAKA,
        "dasar_status": DASAR_PENELITI,
        "sumber": SITASI["lengas"],
        "setara": False,
        "catatan": CATATAN_LENGAS,
    }
    nilai = None if persen_probe is None else round(float(persen_probe), 1)

    if nilai is None or kerapatan_isi is None:
        # Tanpa kerapatan isi, angka probe tidak bisa jadi WFPS. Batas 60/80
        # sengaja tidak dipakai di sini supaya tidak terlihat seperti kutipan.
        return {**dasar, "nilai": nilai, "wfps": None, "kelas": None,
                "status": STATUS_TIDAK_DIKETAHUI}

    porositas = 1.0 - (float(kerapatan_isi) / 2.65)
    if porositas <= 0:
        return {**dasar, "nilai": nilai, "wfps": None, "kelas": None,
                "status": STATUS_TIDAK_DIKETAHUI}

    wfps = (float(persen_probe) / 100.0) / porositas * 100.0
    if wfps > 100.0:
        # WFPS di atas 100% mustahil secara fisik. Artinya angka probe memang
        # bukan kadar air volumetrik -- persis ketidaksetaraan satuan yang
        # diperingatkan di CLAUDE.md. Lebih jujur menolak daripada melaporkan.
        return {**dasar, "nilai": nilai, "wfps": None, "kelas": None,
                "status": STATUS_TIDAK_DIKETAHUI,
                "catatan": CATATAN_LENGAS + " Konversi menghasilkan WFPS > 100%, "
                           "jadi pembacaan probe ini belum terkalibrasi sebagai "
                           "kadar air volumetrik."}
    if wfps < 60.0:
        kelas, status = "di bawah optimum aerobik", STATUS_AMAN
    elif wfps < 80.0:
        kelas, status = "optimum mendekati batas denitrifikasi", STATUS_PERHATIAN
    else:
        kelas, status = "jenuh, risiko denitrifikasi", STATUS_TIDAK_AMAN

    return {**dasar, "nilai": nilai, "wfps": round(wfps, 1), "kelas": kelas,
            "status": status, "setara": True}


def laporkan_suhu_tanah(nilai: Optional[float]) -> Dict[str, Any]:
    """Suhu tanah ditampilkan tanpa status -- tidak ada baku klasifikasinya."""
    return {
        "parameter": "Suhu tanah",
        "nilai": None if nilai is None else round(float(nilai), 1),
        "satuan": "C",
        "kelas": None,
        "status": STATUS_TIDAK_DIKETAHUI,
        "dasar_batas": None,
        "dasar_status": None,
        "sumber": None,
        "setara": False,
        "catatan": CATATAN_SUHU_TANAH,
    }


def laporkan_hara(
    nitrogen: Optional[float] = None,
    fosfor: Optional[float] = None,
    kalium: Optional[float] = None,
) -> Dict[str, Any]:
    """N/P/K dilaporkan apa adanya. Tidak dikelaskan -- satuannya belum setara."""
    unsur: List[Dict[str, Any]] = []
    for nama, nilai, catatan in (
        ("Nitrogen", nitrogen, CATATAN_NPK),
        ("Fosfor", fosfor, CATATAN_NPK + " " + CATATAN_P_K),
        ("Kalium", kalium, CATATAN_NPK + " " + CATATAN_P_K),
    ):
        unsur.append({
            "parameter": nama,
            "nilai": None if nilai is None else round(float(nilai), 1),
            "satuan": "mg/kg",
            "kelas": None,
            "status": STATUS_TIDAK_DIKETAHUI,
            "dapat_diklasifikasi": False,
            "sumber": SITASI["npk"],
            "catatan": catatan,
        })

    return {
        "dapat_diklasifikasi": False,
        "alasan": CATATAN_NPK,
        "tindakan": "Kalibrasi terhadap uji laboratorium diperlukan sebelum "
                    "nilai ini bisa dinyatakan rendah atau tinggi.",
        "unsur": unsur,
    }


def nilai_status_tanah(
    ph: Optional[float] = None,
    ec_us_cm: Optional[float] = None,
    lengas_persen: Optional[float] = None,
    suhu_tanah: Optional[float] = None,
    kerapatan_isi: Optional[float] = None,
) -> Dict[str, Any]:
    """Vonis kondisi tanah memakai kelas terburuk, bukan rata-rata.

    Rata-rata membiarkan satu pembacaan bagus menutupi pH yang mematikan, jadi
    yang dipakai hukum minimum Liebig: parameter paling membatasi yang
    menentukan vonis, dan namanya ikut disebut.
    """
    parameter = [
        klasifikasi_ph(ph),
        klasifikasi_ec(ec_us_cm),
        klasifikasi_lengas(lengas_persen, kerapatan_isi),
        laporkan_suhu_tanah(suhu_tanah),
    ]

    dinilai = [p for p in parameter if p["status"] != STATUS_TIDAK_DIKETAHUI]
    if not dinilai:
        return {
            "status": STATUS_TIDAK_DIKETAHUI,
            "label": LABEL_STATUS[STATUS_TIDAK_DIKETAHUI],
            "pembatas": None,
            "ringkasan": "Belum dapat dinilai - tidak ada parameter yang "
                         "memenuhi syarat klasifikasi.",
            "parameter": parameter,
            "metode": "Hukum minimum Liebig (kelas terburuk), bukan rata-rata.",
            "catatan_metodologi": SITASI["pemetaan"],
        }

    pembatas = max(dinilai, key=lambda p: _URUTAN_STATUS[p["status"]])
    status = pembatas["status"]

    if status == STATUS_AMAN:
        ringkasan = ("Aman - parameter paling membatasi: "
                     + str(pembatas["parameter"]) + " " + str(pembatas["kelas"]))
    else:
        ringkasan = (LABEL_STATUS[status] + " - pembatas: "
                     + str(pembatas["parameter"]) + " " + str(pembatas["kelas"])
                     + " (" + str(pembatas["nilai"]) + ")")
    if not pembatas.get("setara", True):
        ringkasan += " [indikatif, satuan belum setara pustaka]"

    return {
        "status": status,
        "label": LABEL_STATUS[status],
        "pembatas": {
            "parameter": pembatas["parameter"],
            "kelas": pembatas["kelas"],
            "nilai": pembatas["nilai"],
            "setara": pembatas.get("setara", True),
            "sumber": pembatas.get("sumber"),
        },
        "ringkasan": ringkasan,
        "parameter": parameter,
        "metode": "Hukum minimum Liebig (kelas terburuk), bukan rata-rata.",
        "catatan_metodologi": SITASI["pemetaan"],
    }


def nilai_kesehatan_tanah(
    ph: Optional[float] = None,
    ec_us_cm: Optional[float] = None,
    lengas_persen: Optional[float] = None,
    suhu_tanah: Optional[float] = None,
    nitrogen: Optional[float] = None,
    fosfor: Optional[float] = None,
    kalium: Optional[float] = None,
    kerapatan_isi: Optional[float] = None,
) -> Dict[str, Any]:
    """Dua vonis terpisah: kondisi tanah dan kecukupan hara.

    Sengaja tidak digabung jadi satu angka. pH 4,2 masalah struktural yang
    tidak selesai dengan pupuk, sedangkan N rendah cuma berarti perlu dipupuk.
    """
    return {
        "status_tanah": nilai_status_tanah(
            ph=ph, ec_us_cm=ec_us_cm, lengas_persen=lengas_persen,
            suhu_tanah=suhu_tanah, kerapatan_isi=kerapatan_isi,
        ),
        "status_hara": laporkan_hara(nitrogen=nitrogen, fosfor=fosfor, kalium=kalium),
        "sitasi": SITASI,
    }
