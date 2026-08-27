/**
 * Reverse geocoding helper using OpenStreetMap Nominatim.
 * Resolves latitude and longitude coordinates into a human-readable location name.
 */
export async function reverseGeocode(lat: number, lng: number): Promise<string> {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`
    const res = await fetch(url, {
      headers: {
        'Accept-Language': 'id, en',
        'User-Agent': 'G-Connect-SmartFarming/1.0'
      }
    })

    if (!res.ok) {
      throw new Error(`Geocoding failed with status ${res.status}`)
    }

    const data = await res.json()
    if (!data) return ''

    const addr = data.address || {}
    
    // 1. Highest specificity: Named POI, building, university faculty, laboratory, or farm
    const specificName = data.name 
      || addr.building 
      || addr.amenity 
      || addr.office 
      || addr.leisure 
      || addr.farm 
      || addr.university
      || addr.college

    // 2. Secondary specificity: Road, suburb/village, district, regency/city
    const road = addr.road || addr.pedestrian || addr.footway || ''
    const suburb = addr.suburb || addr.village || addr.neighbourhood || addr.quarter || ''
    const district = addr.city_district || addr.district || ''
    const city = addr.city || addr.town || addr.county || ''

    if (specificName) {
      // e.g. "FMIPA UGM, Sekip Utara" or "Gubug Milenial, Margorejo"
      const area = suburb || district || city
      return area ? `${specificName}, ${area}` : specificName
    }

    if (road && (suburb || city)) {
      return `${road}, ${suburb || city}`
    }

    if (suburb && city) {
      return `${suburb}, ${city}`
    }

    return data.display_name?.split(',').slice(0, 3).join(',').trim() || ''
  } catch (error) {
    console.warn('[Geocoding] Reverse geocode lookup failed:', error)
    return ''
  }
}
