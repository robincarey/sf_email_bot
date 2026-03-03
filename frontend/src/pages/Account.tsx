import { useState } from 'react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../context/AuthContext'

export default function Account() {
  const { user, signOut } = useAuth()
  const [confirming, setConfirming] = useState(false)
  const [deactivating, setDeactivating] = useState(false)

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

      {/* Account info */}
      <div className="rounded-xl bg-surface border border-border p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-text mb-3">Email</h3>
        <p className="text-sm text-text-muted">{user?.email}</p>
      </div>

      {/* Danger zone */}
      <div className="rounded-xl bg-surface border border-red-200 p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-red-700 mb-1">
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
              className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-text hover:bg-gray-50 transition-colors cursor-pointer"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
