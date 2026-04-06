'use client'

import { useEffect, useState } from 'react'

type TriangleType = {
  id: number
  position: number
  duration: number
  size: number
  rotation: number
}

type TriangleProps = {
  position: number
  duration: number
  size: number
  rotation: number
}

function Triangle({ position, duration, size, rotation }: TriangleProps) {
  return (
    <div
      className="absolute top-[-250px] lg:top-[-120px] floatUp pointer-events-none"
      style={{
        left: `${position}%`,
        animationDuration: `${duration}s`,
        transform: `rotate(${rotation}deg)`,
      }}
    >
      <div
        style={{
          width: 0,
          height: 0,
          borderLeft: `${size}px solid transparent`,
          borderRight: `${size}px solid transparent`,
          borderBottom: `${size * 1.6}px solid var(--secondary)`,
          filter: 'blur(0.5px)',
        }}
      />
    </div>
  )
}

export default function AnimatedTrianglesBackground() {
  const [triangles, setTriangles] = useState<TriangleType[]>([])

  useEffect(() => {
    let isMounted = true

    const spawn = () => {
      if (!isMounted) return

      const id = Math.random()

      const newTriangle: TriangleType = {
        id,
        position: Math.random() * 100,
        duration: 8 + Math.random() * 2,
        size: 20 + Math.random() * 60,
        rotation: Math.random() * 360,
      }

      setTriangles((prev) => [...prev, newTriangle])

      // remove after animation ends
      setTimeout(() => {
        setTriangles((prev) => prev.filter((t) => t.id !== id))
      }, newTriangle.duration * 1000)

      // random spawn timing
      const delay = 300 + Math.random() * 800
      setTimeout(spawn, delay)
    }

    spawn()

    return () => {
      isMounted = false
    }
  }, [])

  return (
    <div className="absolute inset-0 md:left-1/2 overflow-hidden">
      {triangles.map((t) => (
        <Triangle key={t.id} {...t} />
      ))}
    </div>
  )
}
