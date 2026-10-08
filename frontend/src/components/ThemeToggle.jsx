import useTheme from '../theme/useTheme.js'
import './ThemeToggle.css'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const nextTheme = theme === 'dark' ? 'light' : 'dark'
  const icon = theme === 'dark'
    ? <svg viewBox="0 0 20 20" focusable="false"><circle cx="10" cy="10" r="3.2" /><path d="M10 1.7v2M10 16.3v2M18.3 10h-2M3.7 10h-2m14.16-5.86-1.42 1.42M5.56 14.44l-1.42 1.42m11.72 0-1.42-1.42M5.56 5.56 4.14 4.14" /></svg>
    : <svg viewBox="0 0 20 20" focusable="false"><path d="M16.7 12.2A7.4 7.4 0 0 1 7.8 3.3 7.5 7.5 0 1 0 16.7 12.2Z" /></svg>

  return (
    <button className="theme-toggle" type="button" onClick={toggleTheme} aria-label={`Switch to ${nextTheme} mode`}>
      <span aria-hidden="true">{icon}</span>
      <span>{theme === 'dark' ? 'Light mode' : 'Dark mode'}</span>
    </button>
  )
}
