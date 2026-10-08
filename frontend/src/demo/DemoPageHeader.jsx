import './DemoUI.css'

export default function DemoPageHeader({ eyebrow, title, description, notice }) {
  return (
    <div className="demo-page-header">
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p>{description}</p>
      {notice && <p className="demo-action-notice" role="status">{notice}</p>}
    </div>
  )
}
