import { useEffect, useRef } from 'react'

const DOT_SPACING = 23
const DOT_RADIUS = 1.5
const DEFAULT_COLOR = 'rgba(210, 214, 219, 0.5)'
const HOVER_COLOR = '#06D6A0'
const HOVER_RADIUS = 130

export function DotGridBackground({ className = '' }: { className?: string }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef = useRef<{ x: number; y: number } | null>(null)

  useEffect(() => {
    const container = containerRef.current
    const canvas = canvasRef.current
    if (!container || !canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let dots: { x: number; y: number }[] = []
    let size = { width: 0, height: 0 }
    let raf = 0

    const rebuild = () => {
      const { width, height } = container.getBoundingClientRect()
      if (width === size.width && height === size.height) return
      size = { width, height }
      const dpr = window.devicePixelRatio || 1
      canvas.width = width * dpr
      canvas.height = height * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      dots = []
      for (let y = DOT_RADIUS; y < height; y += DOT_SPACING) {
        for (let x = DOT_RADIUS; x < width; x += DOT_SPACING) dots.push({ x, y })
      }
    }

    const draw = () => {
      rebuild()
      ctx.clearRect(0, 0, size.width, size.height)
      const mouse = mouseRef.current
      const radiusSq = HOVER_RADIUS * HOVER_RADIUS
      for (const dot of dots) {
        let color = DEFAULT_COLOR
        if (mouse) {
          const dx = dot.x - mouse.x
          const dy = dot.y - mouse.y
          if (dx * dx + dy * dy <= radiusSq) color = HOVER_COLOR
        }
        ctx.beginPath()
        ctx.arc(dot.x, dot.y, DOT_RADIUS, 0, Math.PI * 2)
        ctx.fillStyle = color
        ctx.fill()
      }
      raf = requestAnimationFrame(draw)
    }

    const handleMove = (event: MouseEvent) => {
      const rect = container.getBoundingClientRect()
      const x = event.clientX - rect.left
      const y = event.clientY - rect.top
      mouseRef.current = x < 0 || y < 0 || x > rect.width || y > rect.height ? null : { x, y }
    }
    const handleLeave = () => {
      mouseRef.current = null
    }

    window.addEventListener('mousemove', handleMove)
    window.addEventListener('mouseout', handleLeave)
    const observer = new ResizeObserver(rebuild)
    observer.observe(container)
    raf = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(raf)
      observer.disconnect()
      window.removeEventListener('mousemove', handleMove)
      window.removeEventListener('mouseout', handleLeave)
    }
  }, [])

  return (
    <div ref={containerRef} className={`pointer-events-none absolute inset-0 ${className}`} aria-hidden="true">
      <canvas ref={canvasRef} className="h-full w-full" />
    </div>
  )
}
