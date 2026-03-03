import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'

export default function Account() {
  const { user, signOut } = useAuth()

  const [newEmail, setNewEmail] = useState('')
  const [emailSaving, setEmailSaving] = useState(false)
  const [emailMessage, setEmailMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const [confirming, setConfirming] = useState(false)
  const [deactivating, setDeactivating] = useState(false)

  const handleChangeEmail = async (e: React.FormEvent) => {
    e.preventDefault()
    setEmailMessage(null)
    setEmailSaving(true)

    const { error } = await supabase.auth.updateUser(
      { email: newEmail },
      { emailRedirectTo: window.location.origin },
    )

    setEmailSaving(false)

    if (error) {
      setEmailMessage({ type: 'error', text: error.message })
    } else {
      setEmailMessage({
        type: 'success',
        text: 'Confirmation links have been sent to both your current and new email addresses.',
      })
      setNewEmail('')
    }
  }

  const handleDeactivate = async () => {
    if (!confirming) {
      setConfirming(true)
      return
    }

    setDeactivating(true)
    await supabase
      .from('profiles')
      .update({ is_active: false })
      .eq('id', user!.id)
    await signOut()
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-text">Account</h2>
        <p className="text-sm text-text-muted mt-1">
          Manage your account settings.
        </p>
      </div>

      {/* Current email */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-text mb-1">Current Email</h3>
        <p className="text-sm text-text-muted">{user?.email}</p>
      </div>

      {/* Change email */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-text mb-1">Change Email</h3>
        <p className="text-sm text-text-muted mb-4">
          You'll receive confirmation links at both your current and new email addresses.
        </p>
        <form onSubmit={handleChangeEmail} className="flex gap-3 items-start">
          <div className="flex-1">
            <input
              type="email"
              required
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="new@example.com"
              className="block w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-muted focus:outline-2 focus:outline-brand"
            />
          </div>
          <button
            type="submit"
            disabled={emailSaving || !newEmail}
            className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-brand-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {emailSaving ? 'Sending...' : 'Update'}
          </button>
        </form>
        {emailMessage && (
          <p className={`text-sm mt-3 ${emailMessage.type === 'success' ? 'text-green-700' : 'text-red-600'}`}>
            {emailMessage.text}
          </p>
        )}
      </div>

      {/* Danger zone */}
      <div className="rounded-xl bg-surface border border-red-200 dark:border-red-800 p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-red-700 dark:text-red-400 mb-1">
          Deactivate Account
        </h3>
        <p className="text-sm text-text-muted mb-4">
          This will stop all email alerts. You can sign back in later to
          reactivate your account.
        </p>

        {confirming && !deactivating && (
          <p className="text-sm text-red-600 mb-3 font-medium">
            Are you sure? This will immediately stop all alerts.
          </p>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleDeactivate}
            disabled={deactivating}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {deactivating
              ? 'Deactivating...'
              : confirming
                ? 'Yes, deactivate my account'
                : 'Deactivate account'}
          </button>
          {confirming && !deactivating && (
            <button
              onClick={() => setConfirming(false)}
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors cursor-pointer"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
