// Service worker G-Connect.
//
// Berjalan terpisah dari halaman, jadi notifikasi tetap datang walau tab
// ditutup atau browser sedang di belakang. Ini yang membedakannya dari
// Notification API biasa yang butuh halaman terbuka.

self.addEventListener('push', (event) => {
  let data = { judul: 'G-Connect', isi: '', url: '/dashboard' }
  try {
    data = { ...data, ...event.data.json() }
  } catch (e) {
    // Payload bukan JSON. Tetap tampilkan sesuatu daripada diam-diam hilang.
    data.isi = event.data ? event.data.text() : ''
  }

  event.waitUntil(
    self.registration.showNotification(data.judul, {
      body: data.isi,
      icon: '/favicon.svg',
      badge: '/favicon.svg',
      // Notifikasi bertag sama saling menimpa, jadi satu sensor tidak
      // menumpuk banyak baris di panel notifikasi HP.
      tag: data.tag || 'gconnect',
      data: { url: data.url },
    })
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  const tujuan = (event.notification.data && event.notification.data.url) || '/dashboard'

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((daftar) => {
      // Kalau dashboard sudah terbuka di suatu tab, arahkan tab itu dan
      // fokuskan -- jangan membuka jendela baru tiap notifikasi ditekan.
      for (const klien of daftar) {
        if ('focus' in klien) {
          if ('navigate' in klien) klien.navigate(tujuan)
          return klien.focus()
        }
      }
      return self.clients.openWindow(tujuan)
    })
  )
})
