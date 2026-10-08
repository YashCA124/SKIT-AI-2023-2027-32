import { Link } from 'react-router-dom'
import './Brand.css'

export default function Brand() {
  return (
    <Link className="brand" to="/" aria-label="Parkwise home">
      <span className="brand-mark" aria-hidden="true">P</span>
      <span>Parkwise</span>
    </Link>
  )
}
