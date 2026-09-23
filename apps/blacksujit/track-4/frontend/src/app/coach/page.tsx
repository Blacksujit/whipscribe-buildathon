import Navbar from '@/components/Navbar';

export default function Coach() {
  const coachingItems = [
    {
      priority: 'high',
      title: 'Address tension in sales calls',
      description: 'Multiple tension signals detected across recent calls. Review call handling strategies.',
      affectedSpeakers: ['John'],
      evidence: '3 calls with tension signals in the last week',
    },
    {
      priority: 'medium',
      title: 'Improve action item clarity',
      description: 'Action items often lack clear ownership or deadlines. Use RACI framework in meetings.',
      affectedSpeakers: ['Mike', 'Sarah'],
      evidence: '12 meetings with unclear action items',
    },
    {
      priority: 'low',
      title: 'Standardize compliance language',
      description: 'Inconsistent compliance terminology across calls. Create a standard glossary.',
      affectedSpeakers: ['All'],
      evidence: 'Varied compliance terms in 8 meetings',
    },
  ];

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      
      <div className="max-w-5xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Coaching Insights</h1>
        <p className="text-slate-600 mb-8">Prescriptive recommendations based on performance patterns</p>

        {/* Priority Summary */}
        <div className="grid md:grid-cols-3 gap-4 mb-12">
          <div className="card border-l-4 border-red-500">
            <div className="text-2xl font-bold text-red-600">1</div>
            <div className="text-sm text-slate-600 mt-1">High Priority</div>
          </div>
          <div className="card border-l-4 border-amber-500">
            <div className="text-2xl font-bold text-amber-600">2</div>
            <div className="text-sm text-slate-600 mt-1">Medium Priority</div>
          </div>
          <div className="card border-l-4 border-blue-500">
            <div className="text-2xl font-bold text-blue-600">1</div>
            <div className="text-sm text-slate-600 mt-1">Low Priority</div>
          </div>
        </div>

        {/* Coaching Items */}
        <div className="space-y-6">
          {coachingItems.map((item, index) => (
            <div
              key={index}
              className={`card border-l-4 ${
                item.priority === 'high'
                  ? 'border-red-500'
                  : item.priority === 'medium'
                  ? 'border-amber-500'
                  : 'border-blue-500'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-slate-900">{item.title}</h3>
                <span
                  className={`badge ${
                    item.priority === 'high'
                      ? 'badge-error'
                      : item.priority === 'medium'
                      ? 'badge-warning'
                      : 'badge-neutral'
                  }`}
                >
                  {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)}
                </span>
              </div>
              
              <p className="text-slate-600 mb-4">{item.description}</p>
              
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="text-slate-500">Affected speakers:</span>
                  <span className="text-slate-900 ml-1">{item.affectedSpeakers.join(', ')}</span>
                </div>
              </div>
              
              <div className="mt-3 pt-3 border-t border-slate-100">
                <p className="text-sm text-slate-500">
                  <span className="font-medium">Evidence:</span> {item.evidence}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Call to Action */}
        <div className="mt-12 card bg-blue-50 border-blue-200">
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Ready to coach?</h3>
          <p className="text-slate-600 mb-4">
            Schedule a 1:1 session to discuss these findings and create an action plan.
          </p>
          <button className="btn-primary">Schedule Coaching Session</button>
        </div>
      </div>
    </div>
  );
}