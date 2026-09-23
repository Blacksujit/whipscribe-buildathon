import Navbar from "@/components/Navbar";

export default function Speakers() {
  const speakers = [
    { name: "Sarah", role: "Sales Lead", score: 92, meetings: 8, trend: "+8%" },
    { name: "Mike", role: "Product Manager", score: 85, meetings: 6, trend: "+3%" },
    { name: "John", role: "Account Executive", score: 78, meetings: 4, trend: "-2%" },
  ];

  return (
    <div className="min-h-screen bg-v4-bg">
      <Navbar />
      <section className="container-960 section mx-auto">
        <h1 className="font-display text-h1 mb-2">Speaker Performance</h1>
        <p className="text-v4-ink-muted mb-12">
          Individual performance analysis and coaching insights
        </p>

        {/* Speakers Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {speakers.map((speaker) => (
            <div key={speaker.name} className="card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-h3 font-medium text-v4-ink">{speaker.name}</h3>
                  <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                    {speaker.role}
                  </p>
                </div>
                <div className="text-2xl font-bold text-v4-ink">{speaker.score}</div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                    Meetings
                  </div>
                  <div className="text-lg font-medium text-v4-ink">{speaker.meetings}</div>
                </div>
                <div>
                  <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                    Trend
                  </div>
                  <div
                    className={
                      speaker.trend.startsWith("+") ? "text-ok font-medium" : "text-v4-ink-muted font-medium"
                    }
                  >
                    {speaker.trend}
                  </div>
                </div>
              </div>

              <button className="btn-secondary w-full text-sm">View Details</button>
            </div>
          ))}
        </div>

        {/* Performance Insights */}
        <h2 className="text-h3 font-medium text-v4-ink mb-4">Performance Insights</h2>
        <div className="space-y-4">
          <div className="card">
            <h3 className="text-v4-ink font-medium mb-2">Sarah's Strengths</h3>
            <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-body)" }}>
              Consistently high action item completion rate. Clear communication on
              compliance topics.
            </p>
          </div>

          <div className="card">
            <h3 className="text-v4-ink font-medium mb-2">Mike's Improvement Areas</h3>
            <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-body)" }}>
              Action items sometimes lack clear ownership. Consider following up with
              written summaries.
            </p>
          </div>

          <div className="card">
            <h3 className="text-v4-ink font-medium mb-2">John's Coaching Priority</h3>
            <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-body)" }}>
              Tension signals detected in 3 of 4 calls. Recommend training on difficult
              conversations.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
