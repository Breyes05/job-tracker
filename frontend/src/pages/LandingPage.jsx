import { Link } from 'react-router'

// A small, static board shown on the landing page so visitors can see the app
// before signing up. These are example cards, not real data.
const PREVIEW = [
  { status: 'applied', label: 'Applied', cards: [['Acme Corp', 'Software Engineering Intern'], ['Globex', 'Backend Intern']] },
  { status: 'interviewing', label: 'Interviewing', cards: [['Initech', 'SWE Intern']] },
  { status: 'offer', label: 'Offer', cards: [['Hooli', 'Platform Intern']] },
]

const FEATURES = [
  {
    title: 'See your whole search at a glance',
    text: 'A board with a column for each stage: applied, interviewing, offer, and rejected.',
  },
  {
    title: 'Update a status in one move',
    text: 'Drag a card to the next column, or pick the new status from its dropdown on your phone.',
  },
  {
    title: 'Your applications stay private',
    text: 'Each account only sees its own applications. Passwords are hashed and never stored.',
  },
]

export default function LandingPage() {
  return (
    <div className="landing">
      <header className="landing-nav">
        <span className="brand">Job Tracker</span>
        <nav className="landing-nav-links" aria-label="Account">
          <Link to="/login" className="button button-quiet">
            Log in
          </Link>
          <Link to="/register" className="button">
            Sign up
          </Link>
        </nav>
      </header>

      <main>
        <section className="landing-hero">
          <h1>Keep every job application in one place</h1>
          <p className="landing-lede">
            Track where you applied, what stage you're at, and what's next, without a spreadsheet. Free, and built for
            students applying to internships.
          </p>
          <div className="landing-ctas">
            <Link to="/register" className="button button-large">
              Create a free account
            </Link>
            <Link to="/login" className="landing-secondary-link">
              I already have an account
            </Link>
          </div>
        </section>

        <section className="landing-preview" aria-label="Example board">
          <div className="landing-preview-frame">
            {PREVIEW.map(({ status, label, cards }) => (
              <div key={status} className="board-column landing-preview-column">
                <header className="board-column-header">
                  <span className={`board-dot status-${status}`} aria-hidden="true" />
                  <h2>{label}</h2>
                  <span className="board-count">{cards.length}</span>
                </header>
                <div className="board-cards">
                  {cards.map(([company, role]) => (
                    <div key={company} className="board-card landing-preview-card">
                      <p className="landing-preview-company">{company}</p>
                      <p className="board-card-role">{role}</p>
                      <span className={`status-badge status-${status}`}>{label}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <p className="landing-preview-caption">Example board</p>
        </section>

        <section className="landing-features">
          {FEATURES.map(({ title, text }) => (
            <div key={title} className="landing-feature">
              <h2>{title}</h2>
              <p>{text}</p>
            </div>
          ))}
        </section>
      </main>

      <footer className="landing-footer">
        <a href="https://github.com/Breyes05/job-tracker" target="_blank" rel="noopener noreferrer">
          View the code on GitHub
        </a>
      </footer>
    </div>
  )
}
