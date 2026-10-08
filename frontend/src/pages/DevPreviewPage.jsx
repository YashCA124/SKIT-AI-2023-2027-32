import { useNavigate } from 'react-router-dom'
import { ROLE_DETAILS } from '../config/rolePages.js'
import useAuth from '../auth/useAuth.js'
import AuthLayout from './AuthLayout.jsx'
import { createDemoData } from '../demo/data.js'
import './DevPreviewPage.css'

const PREVIEW_ROLES = ['U', 'M', 'A']

export default function DevPreviewPage() {
  const { beginPreview } = useAuth()
  const navigate = useNavigate()

  function openPreview(role) {
    beginPreview(role, createDemoData())
    navigate('/account', { replace: true })
  }

  return (
    <AuthLayout>
      <p className="eyebrow">Development only</p>
      <h2 id="auth-title">Preview frontend pages</h2>
      <p className="form-intro">Choose a role to inspect the account page and its routes without connecting to the backend.</p>
      <p className="dev-preview-warning" role="note">
        Preview accounts are fictional and kept only in memory. No sign-in, health, or dashboard API requests are made.
      </p>
      <div className="dev-preview-options">
        {PREVIEW_ROLES.map((role) => (
          <button className="dev-preview-option" key={role} type="button" onClick={() => openPreview(role)}>
            <span><strong>{ROLE_DETAILS[role].label}</strong><small>{ROLE_DETAILS[role].title}</small></span>
            <span aria-hidden="true">→</span>
          </button>
        ))}
      </div>
      <button className="dev-preview-exit" type="button" onClick={() => navigate('/login', { replace: true })}>
        Exit preview
      </button>
    </AuthLayout>
  )
}
