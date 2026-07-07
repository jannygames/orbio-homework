export function summarizeToolPayload(content: string): string {
  try {
    const parsed = JSON.parse(content)
    if (parsed && typeof parsed === 'object') {
      const obj = parsed as Record<string, unknown>

      if ('error' in obj) return String(obj.error)
      if (Array.isArray(obj.products)) return `${obj.products.length} product(s)`
      if (Array.isArray(obj.recommendations)) return `${obj.recommendations.length} recommendation(s)`
      if (Array.isArray(obj.categories)) return `${obj.categories.length} categor${obj.categories.length === 1 ? 'y' : 'ies'}`

      const entries = Object.entries(obj)
      if (entries.length === 0) return 'no arguments'
      return entries
        .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
        .join(', ')
    }
    return String(parsed)
  } catch {
    return content
  }
}

export function humanizeToolName(name: string): string {
  const spaced = name.replace(/_/g, ' ')
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}
