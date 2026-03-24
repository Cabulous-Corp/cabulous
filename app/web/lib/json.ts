/**
 * Safely attempts to parse a value as JSON.
 * Returns the parsed object if successful, otherwise returns the original value.
 */
export function safeJsonParse<T = unknown>(value: unknown): { parsed: T; success: boolean } {
  // If it's not a string, it can't be parsed as JSON
  if (typeof value !== 'string') {
    return { parsed: value as T, success: false }
  }

  try {
    return { parsed: JSON.parse(value) as T, success: true }
  } catch {
    // If parsing fails (e.g., invalid JSON), return the original string
    return { parsed: value as T, success: false }
  }
}
