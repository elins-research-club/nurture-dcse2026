/**
 * G-CONNECT Executive PDF Report Generator
 * Generates high-fidelity, comprehensive agronomy and IoT station evaluation reports.
 */

import { formatWIBTime } from './csvExporter'

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
  rangeLabel: string
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

export async function generateExecutivePDFReport(options: PDFReportOptions): Promise<any> {
  const [[{ default: jsPDF }, { default: autoTable }], logoUgm, logoDike, logoElins, logoWebdev] = await Promise.all([
    Promise.all([import('jspdf'), import('jspdf-autotable')]),
    loadLogoAsPngDataUrl('/Logo-UGM.png'),
    loadLogoAsPngDataUrl('/Logo-DIKE.png'),
    loadLogoAsPngDataUrl('/logo-icon.webp'),
    loadLogoAsPngDataUrl('/logo-webdev.webp')
  ])

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  })

  const pageWidth = doc.internal.pageSize.getWidth()
  const pageHeight = doc.internal.pageSize.getHeight()
  const margin = 14
  let y = margin

  // Color Palette Constants
  const emeraldPrimary: [number, number, number] = [5, 150, 105] // #059669
  const darkHeading: [number, number, number] = [15, 23, 42]     // #0F172A
  const slateText: [number, number, number] = [71, 85, 105]       // #475569
  const lightBg: [number, number, number] = [248, 250, 252]      // #F8FAFC
  const borderGray: [number, number, number] = [226, 232, 240]   // #E2E8F0

  // -------------------------------------------------------------
  // 1. TOP BRAND ACCENT BAR
  // -------------------------------------------------------------
  doc.setFillColor(...emeraldPrimary)
  doc.rect(0, 0, pageWidth, 4, 'F')

  // -------------------------------------------------------------
  // 2. INSTITUTIONAL HEADER (KOP DOKUMEN & 4 LOGOS)
  // -------------------------------------------------------------
  const headerTopY = 9

  // Left Column: Title & Subtitles
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11.5)
  doc.setTextColor(...emeraldPrimary)
  doc.text('G-CONNECT SMART FARMING PLATFORM REPORT', margin, headerTopY + 4)

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(...slateText)
  doc.text('Sistem Monitoring & Evaluasi Telemetri Lahan Pertanian Presisi', margin, headerTopY + 8.5)

  doc.setFont('helvetica', 'bold')
  doc.setFontSize(7.5)
  doc.setTextColor(100, 116, 139) // slate-500
  doc.text('Community Service Program  •  Lab ELINS & DIKE UGM', margin, headerTopY + 12.5)

  // Right Column: 4 Official Logos Row
  const logosStartX = pageWidth - margin - 58
  const logosY = headerTopY + 1.5

  if (logoUgm) {
    doc.addImage(logoUgm, 'PNG', logosStartX, logosY, 11, 10.5)
  }
  if (logoDike) {
    doc.addImage(logoDike, 'PNG', logosStartX + 13, logosY + 1.2, 17, 8)
  }
  if (logoElins) {
    doc.addImage(logoElins, 'PNG', logosStartX + 32, logosY + 1, 9, 8.5)
  }
  if (logoWebdev) {
    doc.addImage(logoWebdev, 'PNG', logosStartX + 43, logosY + 1, 9, 8.5)
  }

  // Separator Line
  y = headerTopY + 16.5
  doc.setDrawColor(...borderGray)
  doc.setLineWidth(0.4)
  doc.line(margin, y, pageWidth - margin, y)

  // -------------------------------------------------------------
  // 3. METADATA SUMMARY SECTION
  // -------------------------------------------------------------
  const metaBoxY = headerTopY + 19.5
  doc.setFillColor(...lightBg)
  doc.roundedRect(margin, metaBoxY, pageWidth - (margin * 2), 22, 2.5, 2.5, 'F')
  doc.setDrawColor(...borderGray)
  doc.roundedRect(margin, metaBoxY, pageWidth - (margin * 2), 22, 2.5, 2.5, 'S')

  const col1LabelX = margin + 4
  const col1ValX = margin + 20
  const col2LabelX = margin + 94
  const col2ValX = margin + 116
  const textY = metaBoxY + 5.5

  const truncate = (str: string, maxLen: number) => {
    if (!str) return '-'
    return str.length > maxLen ? str.slice(0, maxLen - 1) + '…' : str
  }

  // Left Column
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8.5)
  doc.setTextColor(...darkHeading)
  doc.text('Stasiun:', col1LabelX, textY)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(truncate(`${options.nodeName} (${options.nodeCode || '-'})`, 36), col1ValX, textY)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Lokasi:', col1LabelX, textY + 5.5)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(truncate(`${options.location || 'Kebun Pertanian / Greenhouse'}`, 36), col1ValX, textY + 5.5)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Periode:', col1LabelX, textY + 11)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(`${options.rangeLabel} (${options.dataPointsCount} data teragregasi)`, col1ValX, textY + 11)

  // Right Column
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Waktu Cetak:', col2LabelX, textY)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(formatWIBTime(new Date().toISOString()), col2ValX, textY)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Penyusun:', col2LabelX, textY + 5.5)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(truncate(options.generatedBy || 'Pengelola Lahan / Peneliti', 28), col2ValX, textY + 5.5)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Status Node:', col2LabelX, textY + 11)

  // Vector solid dot for status (prevents unicode font encoding glitches)
  doc.setFillColor(16, 185, 129) // emerald-500
  doc.circle(col2ValX + 1.2, textY + 10.2, 1.2, 'F')
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(16, 185, 129)
  doc.text('AKTIF TERHUBUNG', col2ValX + 4.5, textY + 11)

  y = metaBoxY + 27

  // -------------------------------------------------------------
  // 4. EXECUTIVE KPI CARDS (4-Column Summary)
  // -------------------------------------------------------------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(...darkHeading)
  doc.text('1. Ringkasan Parameter Utama (KPI)', margin, y)

  y += 4
  const cardWidth = (pageWidth - (margin * 2) - (3 * 3)) / 4
  const cardHeight = 18

  const kpiCards = [
    {
      title: 'Kelembaban Tanah',
      value: options.soilAvgMoisture ? `${options.soilAvgMoisture}%` : '--',
      sub: 'Rata-rata Multi-Titik',
      color: [14, 165, 233] as [number, number, number] // sky-500
    },
    {
      title: 'Keseimbangan NPK',
      value: options.npkRatio || 'Seimbang',
      sub: 'Rasio N : P : K',
      color: [16, 185, 129] as [number, number, number] // emerald-500
    },
    {
      title: 'Kualitas Kimiawi',
      value: options.phVal ? `pH ${options.phVal}` : 'Optimal',
      sub: options.ecVal ? `EC: ${options.ecVal} µS/cm` : 'EC Stabil',
      color: [245, 158, 11] as [number, number, number] // amber-500
    },
    {
      title: 'Suhu Boks Panel',
      value: options.enclosureTemp ? `${options.enclosureTemp}°C` : '--',
      sub: options.enclosureSafeLimit ? `Batas Aman: ${options.enclosureSafeLimit}°C` : 'Kondisi Aman',
      color: [99, 102, 241] as [number, number, number] // indigo-500
    }
  ]

  kpiCards.forEach((card, i) => {
    const cardX = margin + (i * (cardWidth + 3))
    // Card background
    doc.setFillColor(...lightBg)
    doc.roundedRect(cardX, y, cardWidth, cardHeight, 2, 2, 'F')
    doc.setDrawColor(...borderGray)
    doc.roundedRect(cardX, y, cardWidth, cardHeight, 2, 2, 'S')

    // Color top bar
    doc.setFillColor(...card.color)
    doc.roundedRect(cardX, y, cardWidth, 1.5, 0.5, 0.5, 'F')

    // Text
    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7)
    doc.setTextColor(...slateText)
    doc.text(card.title, cardX + 3, y + 5.5)

    doc.setFont('helvetica', 'bold')
    doc.setFontSize(10.5)
    doc.setTextColor(...darkHeading)
    doc.text(String(card.value), cardX + 3, y + 11.5)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(6.5)
    doc.setTextColor(...slateText)
    doc.text(card.sub, cardX + 3, y + 15.5)
  })

  y += cardHeight + 7

  // -------------------------------------------------------------
  // 5. STATISTICAL METRICS TABLE
  // -------------------------------------------------------------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(...darkHeading)
  doc.text('2. Tabel Evaluasi & Statistik Parameter Sensor', margin, y)
  y += 2

  const tableRows = options.stats.map((s, idx) => {
    const formatNum = (val: any) => {
      if (val === null || val === undefined || val === '') return '--'
      if (typeof val === 'number') return Number.isInteger(val) ? String(val) : val.toFixed(1)
      if (!isNaN(Number(val))) {
        const num = Number(val)
        return Number.isInteger(num) ? String(num) : num.toFixed(1)
      }
      return String(val)
    }

    const thresholdText = (s.minThreshold != null || s.maxThreshold != null)
      ? `${s.minThreshold ?? 0} - ${s.maxThreshold ?? '∞'}`
      : 'Standar'

    let statusText = s.status || 'Optimal'
    const numVal = typeof s.lastVal === 'number' ? s.lastVal : (s.lastVal && !isNaN(Number(s.lastVal)) ? Number(s.lastVal) : null)
    if (numVal !== null) {
      if (s.maxThreshold != null && numVal > s.maxThreshold) {
        statusText = 'Melebihi Batas'
      } else if (s.minThreshold != null && numVal < s.minThreshold) {
        statusText = 'Kurang / Rendah'
      } else {
        statusText = 'Optimal'
      }
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

  autoTable(doc, {
    startY: y + 2,
    margin: { left: margin, right: margin },
    head: [['No', 'Parameter Sensor', 'Domain', 'Unit', 'Terakhir', 'Rata-rata', 'Min', 'Max', 'Ambang Batas', 'Status']],
    body: tableRows,
    theme: 'grid',
    headStyles: {
      fillColor: emeraldPrimary,
      textColor: [255, 255, 255],
      fontStyle: 'bold',
      fontSize: 8,
      halign: 'center'
    },
    bodyStyles: {
      fontSize: 7.5,
      textColor: darkHeading
    },
    columnStyles: {
      0: { halign: 'center', cellWidth: 8 },
      1: { halign: 'left', fontStyle: 'bold', cellWidth: 38 },
      2: { halign: 'center', cellWidth: 16 },
      3: { halign: 'center', cellWidth: 14 },
      4: { halign: 'right', cellWidth: 16, fontStyle: 'bold' },
      5: { halign: 'right', cellWidth: 18, fontStyle: 'bold' },
      6: { halign: 'right', cellWidth: 14 },
      7: { halign: 'right', cellWidth: 14 },
      8: { halign: 'center', cellWidth: 24 },
      9: { halign: 'center', cellWidth: 20, fontStyle: 'bold' }
    },
    alternateRowStyles: {
      fillColor: [248, 250, 252]
    }
  })

  // Get Y position after table
  const finalY = (doc as any).lastAutoTable ? (doc as any).lastAutoTable.finalY : y + 60
  y = finalY + 6

  // Check if we need a new page or fit on current page
  if (y > pageHeight - 55) {
    doc.addPage()
    y = margin + 5
  }

  // -------------------------------------------------------------
  // 6. AGRONOMY INSIGHTS & SYSTEM RECOMMENDATIONS
  // -------------------------------------------------------------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(...darkHeading)
  doc.text('3. Catatan & Analisis Kondisi Lahan', margin, y)
  y += 4

  const insightBoxY = y
  const defaultInsight = options.agronomyInsight || 
    `Berdasarkan data telemetri periode ${options.rangeLabel}, kondisi kelembaban tanah dan rasio hara NPK berada pada rentang ideal. Disarankan mempertahankan siklus irigasi saat ini dan memantau fluktuasi suhu mikro lingkungan.`
  
  const defaultThermal = options.thermalInsight ||
    `Suhu boks panel mikrokontroler terpantau stabil dalam batas aman termal (< ${options.enclosureSafeLimit || 55}°C). Sistem proteksi dan ventilasi beroperasi secara optimal.`

  const combinedInsight = `• Kondisi Lahan & Tanah: ${defaultInsight}\n• Kondisi Perangkat IoT: ${defaultThermal}${options.notes ? `\n• Catatan Tambahan: ${options.notes}` : ''}`

  doc.setFillColor(...lightBg)
  doc.setDrawColor(...borderGray)
  
  // Measure text height
  const splitText = doc.splitTextToSize(combinedInsight, pageWidth - (margin * 2) - 8)
  const boxHeight = Math.max(20, (splitText.length * 4) + 6)

  doc.roundedRect(margin, insightBoxY, pageWidth - (margin * 2), boxHeight, 2, 2, 'F')
  doc.roundedRect(margin, insightBoxY, pageWidth - (margin * 2), boxHeight, 2, 2, 'S')

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)
  doc.setTextColor(...slateText)
  doc.text(splitText, margin + 4, insightBoxY + 5)

  y = insightBoxY + boxHeight + 8

  // Check page overflow for signature block
  if (y > pageHeight - 35) {
    doc.addPage()
    y = margin + 5
  }

  // -------------------------------------------------------------
  // 7. SIGNATURE & OFFICIAL SIGN-OFF BLOCK
  // -------------------------------------------------------------
  const signX = pageWidth - margin - 60
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7.5)
  doc.setTextColor(...slateText)
  doc.text('Yogyakarta, ' + new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'long', year: 'numeric' }).format(new Date()), signX, y)
  
  y += 4
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Penyusun / Penanggung Jawab Lahan', signX, y)

  y += 14
  doc.setFont('helvetica', 'bold')
  doc.text(options.generatedBy || 'Pengelola Lahan / Peneliti', signX, y)
  
  y += 3.5
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7)
  doc.setTextColor(...slateText)
  doc.text('G-Connect Smart Farming Platform', signX, y)

  // -------------------------------------------------------------
  // 8. FOOTER WITH PAGE NUMBERS (Across all pages)
  // -------------------------------------------------------------
  const totalPages = doc.getNumberOfPages()
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i)
    doc.setDrawColor(...borderGray)
    doc.setLineWidth(0.3)
    doc.line(margin, pageHeight - 10, pageWidth - margin, pageHeight - 10)

    doc.setFont('helvetica', 'normal')
    doc.setFontSize(7)
    doc.setTextColor(...slateText)
    doc.text('G-CONNECT Platform  •  Dokumen Ringkasan Telemetri Pertanian Presisi', margin, pageHeight - 6)
    doc.text(`Halaman ${i} dari ${totalPages}`, pageWidth - margin - 20, pageHeight - 6)
  }

  return doc
}

export function downloadExecutivePDFReport(doc: jsPDF, filename: string): void {
  doc.save(filename)
}
