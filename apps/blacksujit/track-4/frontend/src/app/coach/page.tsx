import Navbar from "@/components/Navbar";

export default function CoachPage() {
  const coachingItems = [
    {
      priority: "high",
      title: "Address tension in sales calls",
      description:
        "Multiple tension signals detected across recent calls. Review call handling strategies.",
      affectedSpeakers: ["John"],
      evidence: "3 calls with tension signals in the last week",
    },
    {
      priority: "medium",
      title: "Improve action item clarity",
      description:
        "Action items often lack clear ownership or deadlines. Use RACI framework in meetings.",
      affectedSpeakers: ["Mike", "Sarah"],
      evidence: "12 meetings with unclear action items",
    },
    {
      priority: "low",
      title: "Standardize compliance language",
      description:
        "Inconsistent compliance terminology across calls. Create a standard glossary.",
      affectedSpeakers: ["All"],
      evidence: "Varied compliance terms in 8 meetings",
    },
  ];

  const priorityLabel = (p: string) => p.charAt(0).toUpperCase() + p.slice(1);

  return (
    <div className="min-h-screen bg-v4-bg">
      <Navbar />
      <section className="container-960 section mx-auto">
        <h1 className="font-display text-h1 mb-2">Coaching Insights</h1>
        <p className="text-v4-ink-muted mb-12" style={{ fontSize: "var(--text-body)" }}>
          Prescriptive recommendations based on performance patterns
        </p>

        {/* Priority Summary - plain cards, no colored badges */}
        <div className="grid md:grid-cols-3 gap-4 mb-16">
          <div className="card text-center">
            <div className="text-2xl font-bold text-v4-ink">1</div>
            <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              High Priority
            </div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-v4-ink">2</div>
            <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              Medium Priority
            </div>
          </div>
          <div className="card text-center">
            <div className="text-2xl font-bold text-v4-ink">1</div>
            <div className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
              Low Priority
            </div>
          </div>
        </div>

        {/* Coaching Items - plain cards, no colored borders */}
        <div className="space-y-6">
          {coachingItems.map((item, index) => (
            <div key={index} className="card">
              <div className="flex items-start justify-between mb-3">
                <h3 className="font-medium text-v4-ink">{item.title}</h3>
                <span className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                  {priorityLabel(item.priority)}
                </span>
              </div>

              <p
                className="text-v4-ink-muted mb-4"
                style={{ fontSize: "var(--text-body)" }}
              >
                {item.description}
              </p>

              <div className="flex gap-4" style={{ fontSize: "var(--text-micro)" }}>
                <div>
                  <span className="text-v4-ink-muted">Affected speakers:</span>
                  <span className="text-v4-ink ml-1">{item.affectedSpeakers.join(", ")}</span>
                </div>
              </div>

              <div className="mt-3 pt-3" style={{ borderTop: "1px solid var(--color-rule)" }}>
                <p className="text-v4-ink-muted" style={{ fontSize: "var(--text-micro)" }}>
                  <span className="font-medium">Evidence:</span> {item.evidence}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Call to Action - light green alt background */}
        <div className="mt-12 card" style={{ backgroundColor: "var(--color-v4-bg-alt)" }}>
          <h3 className="text-v4-ink font-medium mb-2">Ready to coach?</h3>
          <p className="text-v4-ink-muted mb-4" style={{ fontSize: "var(--text-body)" }}>
            Schedule a 1:1 session to discuss these findings and create an action plan.
          </p>
          <button className="btn-primary">Schedule Coaching Session</button>
        </div>
      </section>
    </div>
  );
}
