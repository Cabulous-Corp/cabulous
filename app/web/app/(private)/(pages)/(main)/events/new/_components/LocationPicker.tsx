'use client'

import { useEffect } from 'react'
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet'
import { OpenStreetMapProvider, SearchControl } from 'leaflet-geosearch'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet-geosearch/dist/geosearch.css'

const markerIcon = new L.Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  shadowSize: [41, 41],
})

interface Props {
  onLocationSelect: (lat: number, lng: number, address: string) => void
}

function MapEvents({ onLocationSelect }: Props) {
  useMapEvents({
    click(e) {
      const { lat, lng } = e.latlng
      fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
        .then((r) => r.json())
        .then((data: { display_name?: string }) => {
          onLocationSelect(lat, lng, data.display_name ?? `${lat}, ${lng}`)
        })
    },
  })
  return null
}

function SearchMap({ onLocationSelect }: Props) {
  const map = useMap()

  useEffect(() => {
    const provider = new OpenStreetMapProvider()
    const searchControl = SearchControl({
      provider,
      style: 'bar',
      autoComplete: true,
      autoCompleteDelay: 250,
      marker: {
        icon: markerIcon,
        draggable: true,
      },
    })

    map.addControl(searchControl)

    map.on('geosearch/showlocation', (e: unknown) => {
      const loc = e as { location: { x: number; y: number; label: string } }
      onLocationSelect(loc.location.y, loc.location.x, loc.location.label)
    })

    return () => {
      map.removeControl(searchControl)
    }
  }, [map, onLocationSelect])

  return <MapEvents onLocationSelect={onLocationSelect} />
}

export function LocationPicker({ onLocationSelect }: Props) {
  return (
    <div className="mt-4 border rounded-lg overflow-hidden">
      <MapContainer
        center={[-23.5505, -46.6333]}
        zoom={13}
        style={{ height: '300px', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <SearchMap onLocationSelect={onLocationSelect} />
      </MapContainer>
    </div>
  )
}
