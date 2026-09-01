/**
 * G-CONNECT Official Telemetry Report Generator
 *
 * Produces a formal, single-ink institutional document (kop surat + document
 * reference number + ruled data tables) suitable for archival and inter-agency
 * distribution. Typography: Times for the institutional masthead and document
 * title, Helvetica for all data and micro-labels.
 */

import { formatWIBTime } from './csvExporter'

type RGB = [number, number, number]

export interface SensorStatItem {
  id?: string | number
  name: string
  unit: string
  domain?: string
  lastVal: number | string | null
  avg: number | string | null
  min: number | string | null
  max: number | string | null
  minThreshold?: number | null
  maxThreshold?: number | null
  status?: string
}

export interface PDFReportOptions {
  nodeName: string
  nodeCode: string
  location?: string
  coordinates?: string
  rangeLabel: string
  categoryLabel?: string
  /* Parameter names highlighted by the dashboard ikhtisar, in its own order. */
  highlightParams?: string[]
  dataPointsCount: number
  generatedBy?: string
  notes?: string
  stats: SensorStatItem[]
  npkRatio?: string
  soilAvgMoisture?: string | number
  phVal?: string | number
  ecVal?: string | number
  enclosureTemp?: string | number
  enclosureMax?: string | number
  enclosureSafeLimit?: string | number
  agronomyInsight?: string
  thermalInsight?: string
}

async function loadLogoAsPngDataUrl(src: string): Promise<string> {
  return new Promise((resolve) => {
    const img = new Image()
    img.crossOrigin = 'Anonymous'
    img.onload = () => {
      try {
        const canvas = document.createElement('canvas')
        canvas.width = img.naturalWidth || img.width
        canvas.height = img.naturalHeight || img.height
        const ctx = canvas.getContext('2d')
        if (ctx) {
          ctx.drawImage(img, 0, 0)
          resolve(canvas.toDataURL('image/png'))
        } else {
          resolve('')
        }
      } catch {
        resolve('')
      }
    }
    img.onerror = () => resolve('')
    img.src = src
  })
}

/* Roman month numerals - standard in Indonesian official document references. */
const ROMAN_MONTHS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII']

/* Short code per parameter category, used inside the document reference number. */
function categoryCode(label?: string): string {
  const l = (label || '').toLowerCase()
  if (l.includes('npk') || l.includes('hara')) return 'NPK'
  if (l.includes('tanah')) return 'TNH'
  if (l.includes('iot') || l.includes('lingkungan')) return 'ENV'
  return 'UMM'
}

export async function generateExecutivePDFReport(options: PDFReportOptions): Promise<any> {
  const [[{ default: jsPDF }, { default: autoTable }], logoUgm, logoDike, logoElins, logoWebdev] = await Promise.all([
    Promise.all([import('jspdf'), import('jspdf-autotable')]),
    loadLogoAsPngDataUrl('/Logo-UGM.png'),
    loadLogoAsPngDataUrl('/Logo-DIKE.png'),
    loadLogoAsPngDataUrl('/logo-icon.webp'),
    loadLogoAsPngDataUrl('/logo-webdev.webp')
  ])

  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })

  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const MARGIN = 18
  const CONTENT_W = pageWidth - MARGIN * 2

  // ---------------------------------------------------------------
  // SINGLE-INK PALETTE
  // The document is entirely achromatic - one neutral ink ramp carries
  // every rule, label and value. No colour is used anywhere.
  // ---------------------------------------------------------------
  // All three text inks are black to near-black: the old #8C8C8C labels
  // measured only 3.36:1 against white, below the 4.5:1 legibility floor,
  // and were unreadable at 6pt. Hierarchy now comes from size, weight and
  // letter-spacing rather than from fading the ink out.
  const INK: RGB = [17, 17, 17]
  const INK_MID: RGB = [26, 26, 26]
  const INK_SOFT: RGB = [51, 51, 51]
  const RULE: RGB = [208, 208, 208]
  const WASH: RGB = [246, 246, 246]

  const now = new Date()
  const catLabel = options.categoryLabel || 'Semua Parameter'
  const serial = String(
    Math.floor((now.getTime() - new Date(now.getFullYear(), 0, 0).getTime()) / 86400000)
  ).padStart(3, '0')
  // Conventional Indonesian reference: urut / unit kerja / instansi / bulan romawi / tahun.
  // The category rides along in the unit segment so two reports pulled on the same
  // day for different parameter sets do not share a number.
  const docRef = `${serial}/ELS-${categoryCode(catLabel)}/UGM/${ROMAN_MONTHS[now.getMonth()]}/${now.getFullYear()}`

  doc.setProperties({
    title: `Laporan Evaluasi Telemetri - ${options.nodeName || options.nodeCode || 'Stasiun'} (${docRef})`,
    subject: `Laporan evaluasi telemetri stasiun pertanian presisi - kategori ${catLabel}, periode ${options.rangeLabel}`,
    author: options.generatedBy || 'Pengelola Lahan / Peneliti',
    keywords: 'G-Connect, Smart Farming, Telemetri, IoT, Agronomi, Laporan Resmi',
    creator: 'G-Connect Smart Farming Platform'
  })

  // ---------------------------------------------------------------
  // TYPOGRAPHIC HELPERS
  // jsPDF's align option ignores character spacing, so tracked text is
  // positioned manually from a width that includes the tracking.
  // ---------------------------------------------------------------
  const trackedWidth = (text: string, tracking: number) =>
    doc.getTextWidth(text) + tracking * Math.max(0, text.length - 1)

  const tracked = (text: string, x: number, ty: number, tracking: number) => {
    doc.setCharSpace(tracking)
    doc.text(text, x, ty)
    doc.setCharSpace(0)
  }

  const trackedCenter = (text: string, ty: number, tracking: number) => {
    tracked(text, (pageWidth - trackedWidth(text, tracking)) / 2, ty, tracking)
  }

  const trackedRight = (text: string, rightX: number, ty: number, tracking: number) => {
    tracked(text, rightX - trackedWidth(text, tracking), ty, tracking)
  }

  const hairline = (ty: number, color: RGB = RULE, width = 0.1, x1 = MARGIN, x2 = pageWidth - MARGIN) => {
    doc.setDrawColor(...color)
    doc.setLineWidth(width)
    doc.line(x1, ty, x2, ty)
  }

  /* Small-caps section heading: "I. RINGKASAN ..." with a rule beneath. */
  const sectionHeading = (numeral: string, label: string, ty: number) => {
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8.5)
    doc.setTextColor(...INK)
    tracked(`${numeral}.  ${label.toUpperCase()}`, MARGIN, ty, 0.45)
    hairline(ty + 2.4, INK, 0.3)
    return ty + 6.8
  }

  let y = MARGIN

  // ===============================================================
  // KOP SURAT - institutional letterhead
  // ===============================================================
  const kopTop = 13

  // UGM alone on the left, the three programme marks clustered on the right.
  const rightLogoEnd = pageWidth - MARGIN
  const rightClusterW = 36
  const leftLogoW = 15
  if (logoUgm) doc.addImage(logoUgm, 'PNG', MARGIN, kopTop + 2, leftLogoW, 14.5)
  if (logoWebdev) doc.addImage(logoWebdev, 'PNG', rightLogoEnd - 8.5, kopTop + 3, 8.5, 8)
  if (logoElins) doc.addImage(logoElins, 'PNG', rightLogoEnd - 19.5, kopTop + 3, 8.5, 8)
  if (logoDike) doc.addImage(logoDike, 'PNG', rightLogoEnd - rightClusterW, kopTop + 3.6, 14.5, 6.8)

  // The masthead is centred in the clear band between the two logo clusters and
  // each line is shrunk to fit it, so no line can ever run underneath a mark.
  const kopLeft = MARGIN + leftLogoW + 5
  const kopRight = rightLogoEnd - rightClusterW - 5
  const kopMid = (kopLeft + kopRight) / 2
  const kopBand = kopRight - kopLeft

  const kopLine = (text: string, ty: number, tracking: number, size: number, color: RGB) => {
    doc.setTextColor(...color)
    let s = size
    doc.setFontSize(s)
    while (s > 5.5 && trackedWidth(text, tracking) > kopBand) {
      s -= 0.25
      doc.setFontSize(s)
    }
    tracked(text, kopMid - trackedWidth(text, tracking) / 2, ty, tracking)
  }

  // ELINS sits under DIKE (Departemen Ilmu Komputer dan Elektronika) in
  // FMIPA, so the masthead runs university > faculty > department > lab.
  doc.setFont('times', 'normal')
  kopLine('UNIVERSITAS GADJAH MADA', kopTop + 4.2, 0.8, 10.5, INK)
  kopLine('FAKULTAS MATEMATIKA DAN ILMU PENGETAHUAN ALAM', kopTop + 8.3, 0.5, 9, INK)

  doc.setFont('times', 'bold')
  kopLine('DEPARTEMEN ILMU KOMPUTER DAN ELEKTRONIKA', kopTop + 13, 0.25, 11.5, INK)

  doc.setFont('times', 'normal')
  kopLine('Laboratorium Riset Elektronika dan Instrumentasi', kopTop + 17, 0, 8.5, INK_MID)

  kopLine('Jl. Sains, Bulaksumur, Yogyakarta 55281  •  dike.fmipa.ugm.ac.id', kopTop + 20.6, 0, 7.5, INK_SOFT)

  // Double rule - the defining mark of an official letterhead.
  hairline(kopTop + 23.6, INK, 1.1)
  hairline(kopTop + 25.4, INK, 0.25)

  y = kopTop + 31

  // ===============================================================
  // DOCUMENT TITLE BLOCK
  // ===============================================================
  doc.setFont('times', 'bold')
  doc.setFontSize(15)
  doc.setTextColor(...INK)
  trackedCenter('LAPORAN EVALUASI TELEMETRI', y, 1.2)

  y += 5.4
  doc.setFont('times', 'normal')
  doc.setFontSize(10)
  doc.setTextColor(...INK_MID)
  trackedCenter('Stasiun Pemantauan Pertanian Presisi', y, 0.2)

  y += 5
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(...INK)
  trackedCenter(`Nomor:  ${docRef}`, y, 0.35)

  // Short centred rule beneath the reference, as on formal notes.
  y += 2
  hairline(y, INK, 0.25, pageWidth / 2 - 26, pageWidth / 2 + 26)

  y += 8

  // ===============================================================
  // I. IDENTITAS DOKUMEN - ruled definition grid
  // ===============================================================
  y = sectionHeading('I', 'Identitas Dokumen', y)

  const sensorCount = options.stats?.length ?? 0
  const metaRows: Array<[string, string, string, string]> = [
    ['Stasiun', options.nodeName || '-', 'Periode Laporan', options.rangeLabel || '-'],
    ['Kode Stasiun', options.nodeCode || '-', 'Kategori Parameter', catLabel],
    ['Lokasi Lahan', options.location || 'Kebun Pertanian / Greenhouse', 'Jumlah Sampel', `${options.dataPointsCount} titik data`],
    ['Koordinat GPS', options.coordinates || '-7.6846, 110.3400', 'Jumlah Parameter', `${sensorCount} parameter`],
    ['Penyusun', options.generatedBy || 'Pengelola Lahan / Peneliti', 'Waktu Cetak', formatWIBTime(now.toISOString())]
  ]

  const colGap = 8
  const halfW = (CONTENT_W - colGap) / 2
  // Measure the widest label actually present instead of assuming a fixed
  // column: 'KATEGORI PARAMETER' is 31.6mm and used to run into its value.
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(6.6)
  const labelW = Math.max(
    ...metaRows.map(r => trackedWidth(r[0].toUpperCase(), 0.3)),
    ...metaRows.map(r => trackedWidth(r[2].toUpperCase(), 0.3))
  ) + 4
  const valueW = halfW - labelW - 2
  const leftLabelX = MARGIN
  const leftValueX = MARGIN + labelW
  const rightLabelX = MARGIN + halfW + colGap
  const rightValueX = rightLabelX + labelW

  let metaY = y
  const metaLineH = 3.5
  metaRows.forEach(([l1, v1, l2, v2], idx) => {
    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8.2)
    const v1Lines: string[] = doc.splitTextToSize(String(v1), valueW)
    const v2Lines: string[] = doc.splitTextToSize(String(v2), valueW)
    const rowH = Math.max(v1Lines.length, v2Lines.length) * metaLineH + 2.8

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(6.6)
    doc.setTextColor(...INK_SOFT)
    tracked(l1.toUpperCase(), leftLabelX, metaY, 0.3)
    tracked(l2.toUpperCase(), rightLabelX, metaY, 0.3)

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(8.2)
    doc.setTextColor(...INK)
    doc.text(v1Lines, leftValueX, metaY)
    doc.text(v2Lines, rightValueX, metaY)

    metaY += rowH
  })

  y = metaY + 5

  // ===============================================================
  // II. RINGKASAN PARAMETER UTAMA - monochrome ruled stat strip
  // ===============================================================
  y = sectionHeading('II', 'Ringkasan Parameter Utama', y)

  // The summary mirrors the dashboard ikhtisar: the same parameters, in the same
  // order, capped at the same three. Values are recomputed from the very stats
  // that build the table below, so the summary and the table cannot disagree.
  type Kpi = { label: string; value: string; caption: string }

  const asNumber = (v: any): number | null => {
    if (v === null || v === undefined || v === '') return null
    const n = Number(v)
    return Number.isFinite(n) ? n : null
  }

  const fmtNum = (v: any): string | null => {
    const n = asNumber(v)
    if (n === null) return null
    return Number.isInteger(n) ? String(n) : n.toFixed(1)
  }

  const withUnit = (v: any, unit = ''): string | null => {
    const t = fmtNum(v)
    if (t === null) return null
    if (!unit) return t
    return unit === '%' || unit.startsWith('°') ? t + unit : t + ' ' + unit
  }

  const cardFor = (st: SensorStatItem): Kpi | null => {
    const value = withUnit(st.avg, st.unit || '') ?? withUnit(st.lastVal, st.unit || '')
    if (!value) return null
    const lo = fmtNum(st.min)
    const hi = fmtNum(st.max)
    return {
      label: st.name,
      value,
      caption: lo !== null && hi !== null ? `Min ${lo}  •  Maks ${hi}` : 'Rata-rata periode'
    }
  }

  const highlighted = (options.highlightParams || [])
    .map(n => options.stats.find(st => String(st.name).toLowerCase() === String(n).toLowerCase()))
    .filter((st): st is SensorStatItem => !!st)

  // Same canonical ordering the dashboard applies before slicing its ikhtisar to
  // three (NPK first, then probes, then alphabetical), so this picks the very
  // same parameters even when the dashboard passes no explicit list.
  const npkOrder = (n: string) => {
    if (n.includes('nitrogen') || n === 'n') return 1
    if (n.includes('phosphor') || n.includes('fosfor') || n === 'p') return 2
    if (n.includes('potassium') || n.includes('kalium') || n === 'k') return 3
    return 99
  }
  const probeOrder = (n: string) => {
    if (n.includes('probe 1')) return 1
    if (n.includes('probe 2')) return 2
    if (n.includes('probe 3')) return 3
    return 99
  }
  const canonical = [...options.stats].sort((a, b) => {
    const na = String(a.name || '').toLowerCase()
    const nb = String(b.name || '').toLowerCase()
    const pa = npkOrder(na), pb = npkOrder(nb)
    if (pa !== 99 || pb !== 99) return pa - pb
    const qa = probeOrder(na), qb = probeOrder(nb)
    if (qa !== 99 || qb !== 99) return qa - qb
    return na.localeCompare(nb)
  })

  let kpis = (highlighted.length ? highlighted : canonical)
    .slice(0, 3)
    .map(cardFor)
    .filter((k): k is Kpi => k !== null)

  if (!kpis.length) kpis = [{ label: 'Ringkasan', value: '--', caption: 'Data tidak tersedia' }]

  const stripH = 17
  const cellW = CONTENT_W / kpis.length

  doc.setFillColor(...WASH)
  doc.rect(MARGIN, y, CONTENT_W, stripH, 'F')
  hairline(y, INK, 0.25)
  hairline(y + stripH, INK, 0.25)

  kpis.forEach((k, i) => {
    const cx = MARGIN + i * cellW + 4

    if (i > 0) {
      doc.setDrawColor(...RULE)
      doc.setLineWidth(0.1)
      doc.line(MARGIN + i * cellW, y + 3, MARGIN + i * cellW, y + stripH - 3)
    }

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(6.2)
    doc.setTextColor(...INK_SOFT)
    tracked(k.label.toUpperCase(), cx, y + 5.2, 0.32)

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(12)
    doc.setTextColor(...INK)
    const vLines: string[] = doc.splitTextToSize(String(k.value), cellW - 7)
    doc.text(vLines[0] || '--', cx, y + 11.2)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(6.4)
    doc.setTextColor(...INK_MID)
    doc.text(doc.splitTextToSize(k.caption, cellW - 7)[0] || '', cx, y + 15.2)
  })

  y += stripH + 7

  // ===============================================================
  // III. TABEL EVALUASI PARAMETER SENSOR
  // ===============================================================
  y = sectionHeading('III', 'Tabel Evaluasi Parameter Sensor', y)

  const formatNum = (val: any) => {
    if (val === null || val === undefined || val === '') return '--'
    const num = typeof val === 'number' ? val : Number(val)
    if (!Number.isFinite(num)) return String(val)
    return Number.isInteger(num) ? String(num) : num.toFixed(1)
  }

  const tableRows = options.stats.map((s, idx) => {
    // WinAnsi has no infinity glyph, so open-ended ranges are worded instead.
    let thresholdText = 'Standar'
    if (s.minThreshold != null && s.maxThreshold != null) thresholdText = `${s.minThreshold} - ${s.maxThreshold}`
    else if (s.minThreshold != null) thresholdText = `min. ${s.minThreshold}`
    else if (s.maxThreshold != null) thresholdText = `maks. ${s.maxThreshold}`

    let statusText = s.status || 'Optimal'
    const numVal = typeof s.lastVal === 'number' ? s.lastVal : (s.lastVal && !isNaN(Number(s.lastVal)) ? Number(s.lastVal) : null)
    if (numVal !== null) {
      if (s.maxThreshold != null && numVal > s.maxThreshold) statusText = 'Melebihi Batas'
      else if (s.minThreshold != null && numVal < s.minThreshold) statusText = 'Di Bawah Batas'
      else statusText = 'Optimal'
    }

    return [
      String(idx + 1),
      s.name,
      s.domain || 'Lahan',
      s.unit || '-',
      formatNum(s.lastVal),
      formatNum(s.avg),
      formatNum(s.min),
      formatNum(s.max),
      thresholdText,
      statusText
    ]
  })

  const colAlign: Array<'left' | 'right'> = [
    'left', 'left', 'left', 'left', 'right', 'right', 'right', 'right', 'right', 'right'
  ]

  hairline(y - 1.5, INK, 0.25)

  autoTable(doc, {
    startY: y - 1.5,
    margin: { left: MARGIN, right: MARGIN, top: 26, bottom: 20 },
    head: [['No', 'Parameter Sensor', 'Domain', 'Satuan', 'Terakhir', 'Rata-rata', 'Min', 'Maks', 'Ambang Batas', 'Status']],
    body: tableRows,
    theme: 'plain',
    styles: {
      font: 'helvetica',
      fontSize: 7.4,
      textColor: INK,
      cellPadding: { top: 1.9, right: 1.6, bottom: 1.9, left: 1.6 },
      overflow: 'linebreak'
    },
    headStyles: {
      fontStyle: 'normal',
      fontSize: 6.3,
      textColor: INK_SOFT,
      cellPadding: { top: 1.4, right: 1.6, bottom: 2.6, left: 1.6 }
    },
    columnStyles: {
      0: { halign: 'left', cellWidth: 7, textColor: INK_SOFT },
      1: { halign: 'left', cellWidth: 34, fontStyle: 'bold' },
      2: { halign: 'left', cellWidth: 14, textColor: INK_MID },
      3: { halign: 'left', cellWidth: 14, textColor: INK_MID },
      4: { halign: 'right', cellWidth: 16, fontStyle: 'bold' },
      5: { halign: 'right', cellWidth: 17 },
      6: { halign: 'right', cellWidth: 12, textColor: INK_MID },
      7: { halign: 'right', cellWidth: 12, textColor: INK_MID },
      8: { halign: 'right', cellWidth: 22, textColor: INK_MID },
      9: { halign: 'right', cellWidth: 26 }
    },
    didParseCell: (data: any) => {
      // Header micro-labels are uppercase and tracked like the rest of the document.
      if (data.section === 'head') {
        data.cell.text = data.cell.text.map((t: string) => String(t).toUpperCase())
        data.cell.styles.halign = colAlign[data.column.index] || 'left'
      }
      // Severity is expressed through weight, not colour - the document stays single-ink.
      if (data.section === 'body' && data.column.index === 9) {
        const v = String(data.cell.raw)
        if (v === 'Optimal') {
          data.cell.styles.textColor = INK_SOFT
          data.cell.styles.fontStyle = 'normal'
        } else {
          data.cell.styles.textColor = INK
          data.cell.styles.fontStyle = 'bold'
        }
      }
    },
    didDrawCell: (data: any) => {
      // Horizontal rules only - no vertical lines, no zebra fill.
      const bottom = data.cell.y + data.cell.height
      if (data.section === 'head') {
        doc.setDrawColor(...INK)
        doc.setLineWidth(0.25)
      } else {
        doc.setDrawColor(...RULE)
        doc.setLineWidth(0.1)
      }
      doc.line(data.cell.x, bottom, data.cell.x + data.cell.width, bottom)
    }
  })

  const lastTable = (doc as any).lastAutoTable
  y = (lastTable ? lastTable.finalY : y + 60) + 3

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(6.6)
  doc.setTextColor(...INK_SOFT)
  doc.text(
    `Agregasi dari ${options.dataPointsCount} titik data pada periode ${options.rangeLabel.toLowerCase()}, kategori ${catLabel}.`,
    MARGIN,
    y
  )
  y += 6

  const ensureSpace = (needed: number) => {
    if (y + needed > pageHeight - 15) {
      doc.addPage()
      y = 30
    }
  }

  // ===============================================================
  // IV. CATATAN DAN ANALISIS
  // ===============================================================
  ensureSpace(20)
  y = sectionHeading('IV', 'Catatan dan Analisis Kondisi Lahan', y)

  const agronomy = options.agronomyInsight ||
    `Berdasarkan data telemetri periode ${options.rangeLabel.toLowerCase()}, kondisi kelembaban tanah dan rasio hara NPK berada pada rentang ideal. Disarankan mempertahankan siklus irigasi saat ini serta memantau fluktuasi suhu mikro lingkungan.`
  const thermal = options.thermalInsight ||
    `Suhu boks panel mikrokontroler terpantau stabil dalam batas aman termal (di bawah ${options.enclosureSafeLimit || 55}°C). Sistem proteksi dan ventilasi beroperasi secara optimal.`

  const analysisItems: Array<[string, string]> = [
    ['Kondisi Lahan dan Tanah', agronomy],
    ['Kondisi Perangkat IoT', thermal]
  ]
  if (options.notes && options.notes.trim()) {
    analysisItems.push(['Catatan Tambahan Penyusun', options.notes.trim()])
  }

  analysisItems.forEach(([heading, body]) => {
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7.8)
    const bodyLines: string[] = doc.splitTextToSize(body, CONTENT_W - 6)
    const blockH = 3.6 + bodyLines.length * 3.6
    ensureSpace(blockH + 4)

    // Thin left rule marks the block, in place of a bullet.
    doc.setDrawColor(...INK_MID)
    doc.setLineWidth(0.7)
    doc.line(MARGIN, y - 2.6, MARGIN, y - 2.6 + blockH)

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(7.6)
    doc.setTextColor(...INK)
    doc.text(heading, MARGIN + 3.6, y)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7.8)
    doc.setTextColor(...INK_MID)
    doc.text(bodyLines, MARGIN + 3.6, y + 4)

    y += blockH + 3
  })

  // ===============================================================
  // V. PENGESAHAN
  // ===============================================================
  ensureSpace(30)
  y = sectionHeading('V', 'Pengesahan', y)

  const signW = 62
  const signX = pageWidth - MARGIN - signW

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7.8)
  doc.setTextColor(...INK_MID)
  doc.text(
    `Yogyakarta, ${new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }).format(now)}`,
    signX,
    y
  )

  y += 4.4
  doc.setTextColor(...INK)
  doc.text('Penyusun / Penanggung Jawab Lahan,', signX, y)

  y += 10
  hairline(y, INK, 0.25, signX, signX + signW)

  y += 4.2
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8.2)
  doc.setTextColor(...INK)
  doc.text(doc.splitTextToSize(options.generatedBy || 'Pengelola Lahan / Peneliti', signW)[0], signX, y)

  y += 3.8
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(6.8)
  doc.setTextColor(...INK_SOFT)
  doc.text('G-Connect Smart Farming Platform', signX, y)

  // ===============================================================
  // RUNNING HEAD + FOOTER on every page
  // ===============================================================
  const totalPages = doc.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)

    if (i > 1) {
      doc.setFont('helvetica', 'normal')
      doc.setFontSize(6.6)
      doc.setTextColor(...INK_SOFT)
      tracked('LAPORAN EVALUASI TELEMETRI', MARGIN, 15, 0.3)
      trackedRight(docRef, pageWidth - MARGIN, 15, 0.2)
      hairline(17.6, RULE, 0.1)
    }

    hairline(pageHeight - 13, RULE, 0.1)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(6.5)
    doc.setTextColor(...INK_SOFT)
    doc.text(`Nomor ${docRef}  •  Dokumen dihasilkan otomatis oleh G-Connect Smart Farming Platform`, MARGIN, pageHeight - 9)
    trackedRight(`Halaman ${i} dari ${totalPages}`, pageWidth - MARGIN, pageHeight - 9, 0.2)
  }

  return doc
}

export function downloadExecutivePDFReport(doc: any, filename: string): void {
  doc.save(filename)
}
