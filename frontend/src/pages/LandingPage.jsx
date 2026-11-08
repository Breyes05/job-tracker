import { useEffect, useState } from 'react'
import { Link } from 'react-router'

// Everything on this page is static. The boards and cards are illustrations
// with made-up companies, never real user data.

const MOCK_COLUMNS = [
  {
    status: 'applied',
    label: 'Applied',
    cards: [
      { company: 'Acme Corp', role: 'Software Engineering Intern', date: 'Nov 4' },
      { company: 'Globex', role: 'Backend Intern', date: 'Nov 2' },
      { company: 'Umbrella', role: 'Data Engineering Intern', date: 'Oct 30' },
    ],
  },
  {
    status: 'interviewing',
    label: 'Interviewing',
    cards: [{ company: 'Initech', role: 'SWE Intern', date: 'Oct 21', moving: true }],
  },
  {
    status: 'offer',
    label: 'Offer',
    cards: [{ company: 'Hooli', role: 'Platform Intern', date: 'Oct 9' }],
  },
  {
    status: 'rejected',
    label: 'Rejected',
    cards: [{ company: 'Vandelay', role: 'Infra Intern', date: 'Oct 3' }],
  },
]

const STEPS = [
  { title: 'Create a free account', text: 'Sign up with your email. It takes about thirty seconds.' },
  { title: 'Add each application', text: 'Company, role, date, the posting link, and any notes you want to keep.' },
  { title: 'Move it forward', text: 'When you hear back, drag the card to the next stage. Your board updates instantly.' },
]

const SMALL_FEATURES = [
  {
    icon: 'phone',
    title: 'Works on your phone',
    text: 'Update a status between classes. On small screens, the board scrolls and every card has a status menu.',
  },
  {
    icon: 'lock',
    title: 'Private by default',
    text: 'Each account only sees its own applications. Passwords are hashed with bcrypt and never stored.',
  },
  {
    icon: 'bolt',
    title: 'Fast to update',
    text: 'Status changes save in the background, so the board never makes you wait.',
  },
]

const FAQS = [
  {
    question: 'Is it free?',
    answer: 'Yes. There’s no paid plan and no credit card.',
  },
  {
    question: 'Who can see my applications?',
    answer:
      'Only you. Every request is checked against your account, and another user asking for one of your applications gets a “not found” response.',
  },
  {
    question: 'Why not just use a spreadsheet?',
    answer:
      'You can, but a board shows where everything stands at a glance, and moving an application to the next stage is one drag instead of editing cells.',
  },
  {
    question: 'Can I use it on my phone?',
    answer: 'Yes. The layout adapts to small screens, and you can change any status from the menu on each card.',
  },
  {
    question: 'Is the code public?',
    answer: 'Yes. The API and the frontend are on GitHub, linked at the bottom of this page.',
  },
]

// Small line icons for the feature cards.
const ICON_PATHS = {
  phone: <rect x="7" y="2.5" width="10" height="19" rx="2.5" />,
  lock: (
    <>
      <rect x="4.5" y="10.5" width="15" height="10.5" rx="2.5" />
      <path d="M8 10.5V7.5a4 4 0 0 1 8 0v3" />
    </>
  ),
  bolt: <path d="M13 2.5 5 13.5h6l-1 8 8-11h-6l1-8Z" />,
}

function Icon({ name }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {ICON_PATHS[name]}
    </svg>
  )
}

function MockBoard() {
  return (
    <div className="mock-window" aria-hidden="true">
      <div className="mock-titlebar">
        <span className="mock-dot" />
        <span className="mock-dot" />
        <span className="mock-dot" />
        <span className="mock-url">Job Tracker</span>
      </div>
      <div className="mock-app">
        <div className="mock-toolbar">
          <span className="mock-heading">Applications</span>
          <span className="mock-toggle">
            <span className="is-on">Board</span>
            <span>List</span>
          </span>
          <span className="mock-search">Search by company</span>
          <span className="mock-add">+ Add application</span>
        </div>
        <div className="mock-board">
          {MOCK_COLUMNS.map(({ status, label, cards }) => (
            <div key={status} className="mock-column">
              <div className="mock-column-header">
                <span className={`board-dot status-${status}`} />
                {label}
                <span className="mock-count">{cards.length}</span>
              </div>
              {cards.map((card) => (
                <div key={card.company} className={`mock-card${card.moving ? ' is-moving' : ''}`}>
                  <span className="mock-company">{card.company}</span>
                  <span className="mock-role">{card.role}</span>
                  <span className="mock-card-footer">
                    <span className="mock-date">{card.date}</span>
                    {card.moving ? (
                      <span className="mock-badge-swap">
                        <span className="status-badge status-applied">Applied</span>
                        <span className="status-badge status-interviewing">Interviewing</span>
                      </span>
                    ) : (
                      <span className={`status-badge status-${status}`}>{label}</span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function MockList() {
  const rows = [
    ['Acme Corp', 'Software Engineering Intern', 'applied', 'Applied', 'Nov 4'],
    ['Initech', 'SWE Intern', 'interviewing', 'Interviewing', 'Oct 21'],
    ['Hooli', 'Platform Intern', 'offer', 'Offer', 'Oct 9'],
  ]
  return (
    <div className="mock-panel" aria-hidden="true">
      <div className="mock-tabs">
        <span className="is-on">
          All <b>6</b>
        </span>
        <span>
          Applied <b>3</b>
        </span>
        <span>
          Interviewing <b>1</b>
        </span>
        <span>
          Offer <b>1</b>
        </span>
      </div>
      <div className="mock-rows">
        {rows.map(([company, role, status, label, date]) => (
          <div key={company} className="mock-row">
            <span className="mock-company">{company}</span>
            <span className="mock-role mock-row-role">{role}</span>
            <span className={`status-badge status-${status}`}>{label}</span>
            <span className="mock-date">{date}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// The pill above the headline cycles through who the app is for.
const EYEBROW_MESSAGES = [
  'Free for students · Built for internship season',
  'New grads · Keep every offer in one place',
  'Switching careers? · Track every lead',
  'Free for everyone · No ads, no credit card',
]
const EYEBROW_INTERVAL_MS = 3500

function RotatingEyebrow() {
  const [index, setIndex] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => setIndex((i) => (i + 1) % EYEBROW_MESSAGES.length), EYEBROW_INTERVAL_MS)
    return () => clearInterval(timer)
  }, [])

  return (
    <span className="landing-eyebrow">
      {/* The key change remounts the text, which replays the slide-in animation. */}
      <span key={index} className="landing-eyebrow-text">
        {EYEBROW_MESSAGES[index]}
      </span>
    </span>
  )
}

// A looping animation of the main interaction: a cursor drags a card from
// Applied to Interviewing, the badge changes, and both column counts update.
function DragDemo() {
  return (
    <div className="drag-demo" aria-hidden="true">
      <div className="drag-col drag-col-1">
        <div className="drag-col-header">
          <span className="board-dot status-applied" />
          Applied
          <span className="drag-count">
            <span className="drag-count-before">3</span>
            <span className="drag-count-after">2</span>
          </span>
        </div>
      </div>
      <div className="drag-col drag-col-2">
        <div className="drag-col-header">
          <span className="board-dot status-interviewing" />
          Interviewing
          <span className="drag-count">
            <span className="drag-count-before">1</span>
            <span className="drag-count-after">2</span>
          </span>
        </div>
      </div>

      {/* Where the card came from, and where it's about to land */}
      <div className="drag-slot drag-slot-origin" />
      <div className="drag-slot drag-slot-target" />

      <div className="drag-card drag-static drag-c1-s2">
        <span className="mock-company">Globex</span>
        <span className="mock-role">Backend Intern</span>
      </div>
      <div className="drag-card drag-static drag-c1-s3">
        <span className="mock-company">Umbrella</span>
        <span className="mock-role">Data Engineering Intern</span>
      </div>
      <div className="drag-card drag-static drag-c2-s1">
        <span className="mock-company">Initech</span>
        <span className="mock-role">SWE Intern</span>
      </div>

      <div className="drag-mover">
        <div className="drag-card drag-moving">
          <span className="mock-company">Acme Corp</span>
          <span className="mock-role">Software Engineering Intern</span>
          <span className="mock-badge-swap drag-badges">
            <span className="status-badge status-applied">Applied</span>
            <span className="status-badge status-interviewing">Interviewing</span>
          </span>
        </div>
      </div>

      <svg className="drag-cursor" width="22" height="22" viewBox="0 0 24 24">
        <path
          d="M5 3l14 8-6.5 1.5L9 19 5 3z"
          fill="#0f172a"
          stroke="#ffffff"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  )
}

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
          <RotatingEyebrow />
          <h1>
            Your job search, <span className="landing-highlight">finally organized</span>
          </h1>
          <p className="landing-lede">
            Track every application on one board, from the day you apply to the day you get the offer. No more
            spreadsheets or digging through your inbox.
          </p>
          <div className="landing-ctas">
            <Link to="/register" className="button button-large">
              Get started for free
            </Link>
            <Link to="/login" className="button button-quiet button-large">
              Log in
            </Link>
          </div>
          <p className="landing-fine-print">No credit card. No ads.</p>
        </section>

        <section className="landing-showcase">
          <MockBoard />
        </section>

        <section className="landing-section" aria-labelledby="how-it-works">
          <p className="landing-kicker">How it works</p>
          <h2 id="how-it-works" className="landing-section-title">
            Three steps, then it just keeps up with you
          </h2>
          <ol className="landing-steps">
            {STEPS.map(({ title, text }, index) => (
              <li key={title} className="landing-step">
                <span className="landing-step-number">{index + 1}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="landing-section landing-feature-row">
          <div className="landing-feature-copy">
            <p className="landing-kicker">Filters and search</p>
            <h2 className="landing-section-title">Find any application in a second</h2>
            <p>
              Switch to the list view to filter by stage, see a count for each one, search by company, and sort by
              name or date.
            </p>
          </div>
          <MockList />
        </section>

        <section className="landing-section landing-feature-row is-reversed">
          <div className="landing-feature-copy">
            <p className="landing-kicker">One-click updates</p>
            <h2 className="landing-section-title">Heard back? Update it in one move</h2>
            <p>
              Drag a card to the next column, or pick the new stage from its menu. The change saves in the background
              and the counts update right away.
            </p>
          </div>
          <DragDemo />
        </section>

        <section className="landing-section">
          <div className="landing-cards">
            {SMALL_FEATURES.map(({ icon, title, text }) => (
              <div key={title} className="landing-card">
                <span className="landing-card-icon" aria-hidden="true">
                  <Icon name={icon} />
                </span>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="landing-section landing-faq" aria-labelledby="faq">
          <p className="landing-kicker">Questions</p>
          <h2 id="faq" className="landing-section-title">
            Frequently asked questions
          </h2>
          <div className="landing-faq-list">
            {FAQS.map(({ question, answer }) => (
              <details key={question} className="landing-faq-item">
                <summary>{question}</summary>
                <p>{answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="landing-final">
          <h2>Start tracking your applications today</h2>
          <p>It’s free, and you can add your first application in under a minute.</p>
          <Link to="/register" className="button button-large button-on-dark">
            Create your free account
          </Link>
        </section>
      </main>

      <footer className="landing-footer">
        <span className="brand">Job Tracker</span>
        <a href="https://github.com/Breyes05/job-tracker" target="_blank" rel="noopener noreferrer">
          View the code on GitHub
        </a>
      </footer>
    </div>
  )
}
