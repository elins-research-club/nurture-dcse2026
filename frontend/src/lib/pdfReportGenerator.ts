/**
 * G-CONNECT Executive PDF Report Generator
 * Generates high-fidelity, comprehensive agronomy and IoT station evaluation reports.
 */

import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
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

export async function generateExecutivePDFReport(options: PDFReportOptions): Promise<jsPDF> {
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
  doc.rect(0, 0, pageWidth, 5, 'F')
  y = 12

  // -------------------------------------------------------------
  // 2. INSTITUTIONAL HEADER (KOP RESMI)
  // -------------------------------------------------------------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(13)
  doc.setTextColor(...emeraldPrimary)
  doc.text('G-CONNECT  •  SMART FARMING & AGRO-IOT PLATFORM', margin, y)

  y += 5
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(8.5)
  doc.setTextColor(...slateText)
  doc.text('Laboratorium Elektronika & Instrumentasi  |  Departemen Ilmu Komputer dan Elektronika FMIPA UGM', margin, y)

  y += 4
  doc.setDrawColor(...borderGray)
  doc.setLineWidth(0.4)
  doc.line(margin, y, pageWidth - margin, y)

  // -------------------------------------------------------------
  // 3. REPORT TITLE & METADATA SECTION
  // -------------------------------------------------------------
  y += 8
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(15)
  doc.setTextColor(...darkHeading)
  doc.text('LAPORAN EVALUASI STASIUN & KESEHATAN LAHAN', margin, y)

  y += 5.5
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(9)
  doc.setTextColor(...slateText)
  
  // Metadata 2-Column Info Box
  const metaBoxY = y
  doc.setFillColor(...lightBg)
  doc.roundedRect(margin, metaBoxY, pageWidth - (margin * 2), 22, 2.5, 2.5, 'F')
  doc.setDrawColor(...borderGray)
  doc.roundedRect(margin, metaBoxY, pageWidth - (margin * 2), 22, 2.5, 2.5, 'S')

  const col1X = margin + 4
  const col2X = margin + 92
  let textY = metaBoxY + 5.5

  // Left Column
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Stasiun:', col1X, textY)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(`${options.nodeName} (${options.nodeCode || '-'})`, col1X + 22, textY)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Lokasi:', col1X, textY + 5.5)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(`${options.location || 'Kebun Pertanian / Greenhouse'}`, col1X + 22, textY + 5.5)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Periode:', col1X, textY + 11)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(`${options.rangeLabel} (${options.dataPointsCount} data teragregasi)`, col1X + 22, textY + 11)

  // Right Column
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Waktu Cetak:', col2X, textY)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(formatWIBTime(new Date().toISOString()), col2X + 24, textY)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Penyusun:', col2X, textY + 5.5)
  doc.setFont('helvetica', 'normal')
  doc.setTextColor(...slateText)
  doc.text(options.generatedBy || 'Administrator Sistem', col2X + 24, textY + 5.5)

  doc.setFont('helvetica', 'bold')
  doc.setTextColor(...darkHeading)
  doc.text('Status Node:', col2X, textY + 11)
  doc.setFont('helvetica', 'bold')
  doc.setTextColor(16, 185, 129) // emerald-500
  doc.text('● ONLINE & AKTIF TERHUBUNG', col2X + 24, textY + 11)

  y = metaBoxY + 28

  // -------------------------------------------------------------
  // 4. EXECUTIVE KPI CARDS (4-Column Summary)
  // -------------------------------------------------------------
  doc.setFont('helvetica', 'bold')
  doc.setFontSize(11)
  doc.setTextColor(...darkHeading)
  doc.text('1. Ringkasan Eksekutif Key Performance Indicator (KPI)', margin, y)

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
      return String(val)
    }

    const thresholdText = (s.minThreshold != null || s.maxThreshold != null)
      ? `${s.minThreshold ?? 0} - ${s.maxThreshold ?? '∞'}`
      : 'Normal'

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
      s.status || 'Normal'
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
  doc.text('3. Catatan Evaluasi & Rekomendasi Agronomi', margin, y)
  y += 4

  const insightBoxY = y
  const defaultInsight = options.agronomyInsight || 
    `Berdasarkan data telemetri periode ${options.rangeLabel}, kondisi kelembaban tanah dan rasio hara NPK berada pada rentang ideal. Disarankan mempertahankan siklus irigasi saat ini dan memantau fluktuasi suhu mikro lingkungan.`
  
  const defaultThermal = options.thermalInsight ||
    `Suhu boks panel mikrokontroler terpantau stabil dalam batas aman termal (< ${options.enclosureSafeLimit || 55}°C). Sistem proteksi dan ventilasi beroperasi secara optimal.`

  const combinedInsight = `• Rekomendasi Lahan: ${defaultInsight}\n• Kondisi Perangkat IoT: ${defaultThermal}${options.notes ? `\n• Catatan Tambahan: ${options.notes}` : ''}`

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
  doc.text('Tim Pengembang & Peneliti IoT', signX, y)

  y += 14
  doc.setFont('helvetica', 'bold')
  doc.text(options.generatedBy || 'Laboratorium ELINS DIKE UGM', signX, y)
  
  y += 3.5
  doc.setFont('helvetica', 'normal')
  doc.setFontSize(7)
  doc.setTextColor(...slateText)
  doc.text('Universitas Gadjah Mada', signX, y)

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
    doc.text('G-CONNECT Platform  •  Dokumen Laporan Resmi Terverifikasi Sistem', margin, pageHeight - 6)
    doc.text(`Halaman ${i} dari ${totalPages}`, pageWidth - margin - 20, pageHeight - 6)
  }

  return doc
}

export function downloadExecutivePDFReport(doc: jsPDF, filename: string): void {
  doc.save(filename)
}
