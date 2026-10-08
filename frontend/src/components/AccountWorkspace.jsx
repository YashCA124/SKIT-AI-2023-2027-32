import { NavLink, useLocation } from 'react-router-dom'
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
  const role = getRoleDetails(session.user.role)
  const pages = ROLE_PAGES[session.user.role] || []
  const currentPage = pages.find((page) => page.path === pathname)
  const pageTitle = currentPage?.title || role.title
  const notice = logoutNotice || sessionNotice

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
          <div className="module-unavailable-note"><strong>Dashboard APIs</strong><p>Not mounted in the current backend.</p></div>
          <button className="switch-role-button" type="button" onClick={logout} disabled={logoutPending}>
            {logoutPending ? 'Signing out…' : 'Sign out'}
          </button>
        </div>
      </aside>
      <main className="signed-in-main">
        <header className="workspace-topbar">
          <div className="breadcrumbs"><span>Parkwise</span><b>/</b><strong>{pageTitle}</strong></div>
          <div className="topbar-actions">
            <ThemeToggle />
            <button className="profile-menu__exit" type="button" onClick={logout} disabled={logoutPending}>
              {logoutPending ? 'Signing out…' : 'Sign out'}
            </button>
          </div>
        </header>
        <div className="signed-in-content">
          <Alert>{notice}</Alert>
          {children || <AccountOverview session={session} />}
        </div>
      </main>
    </div>
  )
}
