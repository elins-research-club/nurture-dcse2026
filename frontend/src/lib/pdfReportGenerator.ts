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
  coordinates?: string
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

  // Set official PDF document properties so browser tabs show a clean title instead of random blob UUID
  const reportDocTitle = `G-CONNECT REPORT - ${options.nodeName || options.nodeCode || 'Telemetri'}`
  doc.setProperties({
    title: reportDocTitle,
    subject: 'G-CONNECT SMART FARMING PLATFORM REPORT',
    author: options.generatedBy || 'Pengelola Lahan / Peneliti',
    keywords: 'G-Connect, Smart Farming, Telemetri, IoT, Agronomi',
    creator: 'G-Connect Smart Farming Platform'
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
  // 3. METADATA SUMMARY SECTION (Dynamic Multi-Line Text Wrapping)
  // -------------------------------------------------------------
  const metaBoxY = headerTopY + 19.5
  const col1LabelX = margin + 4
  const col1ValX = margin + 25
  const col2LabelX = margin + 95
  const col2ValX = margin + 119
  const col1ValMaxWidth = 58
  const col2ValMaxWidth = 60

  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8)

  // Split texts to fit exact column widths (no truncation, automatic downward wrap)
  const stationLines: string[] = doc.splitTextToSize(`${options.nodeName} (${options.nodeCode || '-'})`, col1ValMaxWidth)
  const timeLines: string[] = doc.splitTextToSize(formatWIBTime(new Date().toISOString()), col2ValMaxWidth)

  const locationLines: string[] = doc.splitTextToSize(options.location || 'Kebun Pertanian / Greenhouse', col1ValMaxWidth)
  const coordLines: string[] = doc.splitTextToSize(options.coordinates || '-7.6846, 110.3400', col2ValMaxWidth)

  const periodLines: string[] = doc.splitTextToSize(`${options.rangeLabel} (${options.dataPointsCount} data teragregasi)`, col1ValMaxWidth)
  const authorLines: string[] = doc.splitTextToSize(options.generatedBy || 'Pengelola Lahan / Peneliti', col2ValMaxWidth)

  const lineHeight = 3.6
  const rowSpacing = 2.0
  const boxPaddingTop = 4.5
  const boxPaddingBottom = 4.0

  const row1Height = Math.max(stationLines.length, timeLines.length) * lineHeight
  const row2Height = Math.max(locationLines.length, coordLines.length) * lineHeight
  const row3Height = Math.max(periodLines.length, authorLines.length) * lineHeight

  const totalBoxHeight = boxPaddingTop + row1Height + rowSpacing + row2Height + rowSpacing + row3Height + boxPaddingBottom

  // Draw dynamic box background & border
  doc.setFillColor(...lightBg)
  doc.roundedRect(margin, metaBoxY, pageWidth - (margin * 2), totalBoxHeight, 2.5, 2.5, 'F')
  doc.setDrawColor(...borderGray)
  doc.roundedRect(margin, metaBoxY, pageWidth - (margin * 2), totalBoxHeight, 2.5, 2.5, 'S')

  let currY = metaBoxY + boxPaddingTop + 3.0

  // Row 1: Stasiun & Waktu Cetak
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(8)
  doc.setTextColor(...darkHeading)
  doc.text('Stasiun:', col1LabelX, currY)
  doc.text('Waktu Cetak:', col2LabelX, currY)

  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(stationLines, col1ValX, currY)
  doc.text(timeLines, col2ValX, currY)

  currY += row1Height + rowSpacing

  // Row 2: Lokasi Lahan & Koordinat GPS
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Lokasi Lahan:', col1LabelX, currY)
  doc.text('Koordinat GPS:', col2LabelX, currY)

  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(locationLines, col1ValX, currY)
  doc.text(coordLines, col2ValX, currY)

  currY += row2Height + rowSpacing

  // Row 3: Periode Data & Penyusun
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Periode Data:', col1LabelX, currY)
  doc.text('Penyusun:', col2LabelX, currY)

  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(periodLines, col1ValX, currY)
  doc.text(authorLines, col2ValX, currY)

  y = metaBoxY + totalBoxHeight + 6.0

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
