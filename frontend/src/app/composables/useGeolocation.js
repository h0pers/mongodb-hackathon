import { ref } from 'vue'

const position = ref(null)
const status = ref('idle')

function locate() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      status.value = 'unavailable'
      return resolve(null)
    }
    status.value = 'locating'
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        position.value = { lat: coords.latitude, lng: coords.longitude, accuracy: coords.accuracy }
        status.value = 'ready'
        resolve(position.value)
      },
      (error) => {
        status.value = error.code === error.PERMISSION_DENIED ? 'denied' : 'error'
        resolve(null)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 },
    )
  })
}

export function useGeolocation() {
  return { position, status, locate }
}
