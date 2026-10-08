import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { getRoleDetails, ROLE_PAGES } from '../config/rolePages.js'
import useAuth from '../auth/useAuth.js'
import AccountOverview from './AccountOverview.jsx'
import Alert from './Alert.jsx'
import Brand from './Brand.jsx'
import ThemeToggle from './ThemeToggle.jsx'
import './AccountWorkspace.css'

function getInitials(name) {
  return name.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase()
}

export default function AccountWorkspace({ children }) {
  const { session, logout, logoutNotice, logoutPending, sessionNotice } = useAuth()
  const { pathname } = useLocation()
  const [logoutDialogOpen, setLogoutDialogOpen] = useState(false)
  const logoutDialogRef = useRef(null)
  const cancelLogoutRef = useRef(null)
  const logoutTriggerRef = useRef(null)
  const role = getRoleDetails(session.user.role)
  const pages = ROLE_PAGES[session.user.role] || []
  const currentPage = pages.find((page) => page.path === pathname)
  const pageTitle = currentPage?.title || role.title
  const notice = logoutNotice || sessionNotice
  const isPreview = import.meta.env.DEV && session.isPreview

  useEffect(() => {
    const dialog = logoutDialogRef.current
    if (!logoutDialogOpen || !dialog) return undefined

    dialog.showModal()
    cancelLogoutRef.current?.focus()
    return () => {
      if (dialog.open) dialog.close()
      logoutTriggerRef.current?.focus()
    }
  }, [logoutDialogOpen])

  function requestLogout(event) {
    logoutTriggerRef.current = event.currentTarget
    setLogoutDialogOpen(true)
  }

  async function confirmLogout() {
    setLogoutDialogOpen(false)
    await logout()
  }

  return (
    <div className="signed-in-app">
      <aside className="signed-in-sidebar">
        <Brand />
        <div className="workspace-switch">
          <span className="avatar">{getInitials(session.user.name)}</span>
          <span><strong>{session.user.name}</strong><small>{role.label}</small></span>
        </div>
        <p className="nav-label">ACCOUNT</p>
        <nav className="side-nav" aria-label="Account navigation">
          <NavLink className={({ isActive }) => `nav-item${isActive ? ' nav-item--active' : ''}`} to="/account">
            <span className="nav-item__icon">◫</span>Account overview
          </NavLink>
          {pages.map((page) => (
            <NavLink className={({ isActive }) => `nav-item${isActive ? ' nav-item--active' : ''}`} key={page.id} to={page.path}>
              <span className="nav-item__icon">{page.icon}</span>
              {page.label}
              <span className="nav-unavailable-mark" aria-label="Unavailable">—</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="module-unavailable-note">
            <strong>{isPreview ? 'Fictional demo data' : 'Dashboard APIs'}</strong>
            <p>{isPreview ? 'Temporary sample content; live services are not used.' : 'Not mounted in the current backend.'}</p>
          </div>
          <button className="switch-role-button" type="button" onClick={requestLogout} disabled={logoutPending}>
            {logoutPending ? 'Signing out…' : 'Sign out'}
          </button>
        </div>
      </aside>
      <main className="signed-in-main">
        <header className="workspace-topbar">
          <div className="breadcrumbs"><span>Parkwise</span><b>/</b><strong>{pageTitle}</strong></div>
          <div className="topbar-actions">
            <ThemeToggle />
            <button className="profile-menu__exit" type="button" onClick={requestLogout} disabled={logoutPending}>
              {logoutPending ? 'Signing out…' : 'Sign out'}
            </button>
          </div>
        </header>
        <div className="signed-in-content">
          <Alert>{notice}</Alert>
          {isPreview && (
            <div className="dev-preview-banner" role="status">
              <span><strong>Interactive presentation demo</strong> — fictional accounts and simulated actions; API requests are disabled.</span>
              <Link to="/__preview">Switch preview role</Link>
            </div>
          )}
          {children || <AccountOverview session={session} />}
        </div>
      </main>
      {logoutDialogOpen && (
        <dialog
          aria-describedby="logout-dialog-description"
          aria-labelledby="logout-dialog-title"
          className="logout-dialog"
          onCancel={(event) => {
            event.preventDefault()
            setLogoutDialogOpen(false)
          }}
          ref={logoutDialogRef}
        >
          <div className="logout-dialog__icon" aria-hidden="true">!</div>
          <h2 id="logout-dialog-title">{isPreview ? 'Exit the presentation demo?' : 'Sign out of Parkwise?'}</h2>
          <p id="logout-dialog-description">
            {isPreview
              ? 'Your fictional sample changes will be discarded when you leave this demo.'
              : 'You will be signed out on this tab and returned to the login page.'}
          </p>
          <div className="logout-dialog__actions">
            <button className="logout-dialog__cancel" ref={cancelLogoutRef} type="button" onClick={() => setLogoutDialogOpen(false)}>Stay signed in</button>
            <button className="logout-dialog__confirm" type="button" onClick={confirmLogout} disabled={logoutPending}>
              {isPreview ? 'Exit demo' : 'Sign out'}
            </button>
          </div>
        </dialog>
      )}
    </div>
  )
}
