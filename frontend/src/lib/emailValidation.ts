const INVALID_TLD_PATTERN = /\.(coms|con|cmo|coom|comm)$/i
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validateEmailAddress(email: string): string | null {
  const trimmed = email.trim()
  if (!trimmed) return 'Please enter an email address.'
  if ((trimmed.match(/@/g) ?? []).length !== 1) return 'Please enter a valid email address.'
  if (!EMAIL_PATTERN.test(trimmed)) return 'Please enter a valid email address.'
  if (INVALID_TLD_PATTERN.test(trimmed)) return 'Please check your email address for typos.'
  return null
}
