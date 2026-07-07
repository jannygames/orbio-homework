import { useEffect, useRef, type DependencyList } from 'react'

const NEAR_BOTTOM_PX = 120

export function useAutoScroll<T extends HTMLElement>(deps: DependencyList) {
  const ref = useRef<T>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
    if (distanceFromBottom <= NEAR_BOTTOM_PX) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return ref
}
