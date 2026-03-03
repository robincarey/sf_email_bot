import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'

type Category = 'suggest_website' | 'report_bug' | 'general'

const categories: { id: Category; label: string; desc: string }[] = [
  { id: 'suggest_website', label: 'Suggest a Website', desc: 'Suggest a website for book stock checking' },
  { id: 'report_bug', label: 'Report a Bug', desc: 'Something not working as expected?' },
  { id: 'general', label: 'General', desc: 'Questions, feedback, or anything else' },
]

export default function Contact() {
  const { user } = useAuth()
  const [category, setCategory] = useState<Category | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [url, setUrl] = useState('')
  const [siteDescription, setSiteDescription] = useState('')

  const [bugPage, setBugPage] = useState('')
  const [bugDescription, setBugDescription] = useState('')
  const [bugSteps, setBugSteps] = useState('')

  const [generalSubject, setGeneralSubject] = useState('')
  const [generalMessage, setGeneralMessage] = useState('')

  const resetFields = () => {
    setUrl('')
    setSiteDescription('')
    setBugPage('')
    setBugDescription('')
    setBugSteps('')
    setGeneralSubject('')
    setGeneralMessage('')
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!category || !user) return

    let description = ''
    let submissionUrl: string | null = null

    if (category === 'suggest_website') {
      submissionUrl = url
      description = siteDescription
    } else if (category === 'report_bug') {
      const parts: string[] = []
      if (bugPage) parts.push(`Page/Feature: ${bugPage}`)
      parts.push(bugDescription)
      if (bugSteps) parts.push(`Steps to reproduce:\n${bugSteps}`)
      description = parts.join('\n\n')
    } else {
      const parts: string[] = []
      if (generalSubject) parts.push(`Subject: ${generalSubject}`)
      parts.push(generalMessage)
      description = parts.join('\n\n')
    }

    setSubmitting(true)
    setError(null)

    const { error: insertError } = await supabase
      .from('contact_submissions')
      .insert({
        user_id: user.id,
        user_email: user.email,
        category,
        url: submissionUrl,
        description,
      })

    setSubmitting(false)

    if (insertError) {
      setError(insertError.message)
    } else {
      setSubmitted(true)
    }
  }

  const handleNewSubmission = () => {
    setSubmitted(false)
    setCategory(null)
    resetFields()
  }

  if (submitted) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold text-text">Contact</h2>
        </div>
        <div className="rounded-xl bg-surface border border-border p-8 shadow-sm text-center">
          <p className="text-base font-medium text-text mb-2">Thanks for reaching out!</p>
          <p className="text-sm text-text-muted mb-6">We'll review your submission.</p>
          <button
            onClick={handleNewSubmission}
            className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark transition-colors cursor-pointer"
          >
            Submit another
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-text">Contact</h2>
        <p className="text-sm text-text-muted mt-1">
          Have a suggestion, found a bug, or just want to get in touch?
        </p>
      </div>

      {/* Category selector */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => { setCategory(cat.id); resetFields() }}
            className={`rounded-xl border p-4 text-left transition-colors cursor-pointer ${
              category === cat.id
                ? 'border-brand bg-brand/5'
                : 'border-border bg-surface hover:border-brand/40'
            }`}
          >
            <p className={`text-sm font-semibold ${
              category === cat.id ? 'text-brand-dark' : 'text-text'
            }`}>
              {cat.label}
            </p>
            <p className="text-xs text-text-muted mt-1">{cat.desc}</p>
          </button>
        ))}
      </div>

      {/* Form */}
      {category && (
        <form onSubmit={handleSubmit} className="rounded-xl bg-surface border border-border p-6 shadow-sm space-y-4">
          {category === 'suggest_website' && (
            <>
              <div>
                <label htmlFor="url" className="block text-sm font-medium text-text mb-1">
                  Website URL
                </label>
                <input
                  id="url"
                  type="url"
                  required
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand"
                />
              </div>
              <div>
                <label htmlFor="site-desc" className="block text-sm font-medium text-text mb-1">
                  Description
                </label>
                <textarea
                  id="site-desc"
                  required
                  rows={3}
                  value={siteDescription}
                  onChange={(e) => setSiteDescription(e.target.value)}
                  placeholder="What does this site sell? Any notes for us."
                  className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand resize-y"
                />
              </div>
            </>
          )}

          {category === 'report_bug' && (
            <>
              <div>
                <label htmlFor="bug-page" className="block text-sm font-medium text-text mb-1">
                  Page or feature affected <span className="text-text-muted font-normal">(optional)</span>
                </label>
                <input
                  id="bug-page"
                  type="text"
                  value={bugPage}
                  onChange={(e) => setBugPage(e.target.value)}
                  placeholder="e.g. Dashboard, Preferences"
                  className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand"
                />
              </div>
              <div>
                <label htmlFor="bug-desc" className="block text-sm font-medium text-text mb-1">
                  What happened?
                </label>
                <textarea
                  id="bug-desc"
                  required
                  rows={3}
                  value={bugDescription}
                  onChange={(e) => setBugDescription(e.target.value)}
                  placeholder="Describe the issue you encountered"
                  className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand resize-y"
                />
              </div>
              <div>
                <label htmlFor="bug-steps" className="block text-sm font-medium text-text mb-1">
                  Steps to reproduce <span className="text-text-muted font-normal">(optional)</span>
                </label>
                <textarea
                  id="bug-steps"
                  rows={3}
                  value={bugSteps}
                  onChange={(e) => setBugSteps(e.target.value)}
                  placeholder="1. Go to...&#10;2. Click on...&#10;3. See error"
                  className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand resize-y"
                />
              </div>
            </>
          )}

          {category === 'general' && (
            <>
              <div>
                <label htmlFor="general-subject" className="block text-sm font-medium text-text mb-1">
                  Subject <span className="text-text-muted font-normal">(optional)</span>
                </label>
                <input
                  id="general-subject"
                  type="text"
                  value={generalSubject}
                  onChange={(e) => setGeneralSubject(e.target.value)}
                  placeholder="What's this about?"
                  className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand"
                />
              </div>
              <div>
                <label htmlFor="general-msg" className="block text-sm font-medium text-text mb-1">
                  Message
                </label>
                <textarea
                  id="general-msg"
                  required
                  rows={4}
                  value={generalMessage}
                  onChange={(e) => setGeneralMessage(e.target.value)}
                  placeholder="Your message"
                  className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand resize-y"
                />
              </div>
            </>
          )}

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-brand px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {submitting ? 'Submitting...' : 'Submit'}
          </button>
        </form>
      )}
    </div>
  )
}
