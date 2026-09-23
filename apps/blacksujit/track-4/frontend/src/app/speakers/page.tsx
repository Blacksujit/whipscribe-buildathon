import Navbar from '@/components/Navbar';

export default function Speakers() {
  const speakers = [
    { name: 'Sarah', role: 'Sales Lead', score: 92, meetings: 8, trend: '+8%' },
    { name: 'Mike', role: 'Product Manager', score: 85, meetings: 6, trend: '+3%' },
    { name: 'John', role: 'Account Executive', score: 78, meetings: 4, trend: '-2%' },
  ];

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      
      <div className="max-w-5xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Speaker Performance</h1>
        <p className="text-slate-600 mb-8">Individual performance analysis and coaching insights</p>

        {/* Speakers Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {speakers.map((speaker) => (
            <div key={speaker.name} className="card">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-slate-900">{speaker.name}</h3>
                  <p className="text-sm text-slate-600">{speaker.role}</p>
                </div>
                <div className="text-3xl font-bold text-blue-600">{speaker.score}</div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <div className="text-sm text-slate-600">Meetings</div>
                  <div className="text-lg font-semibold text-slate-900">{speaker.meetings}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-600">Trend</div>
                  <div className={`text-lg font-semibold ${speaker.trend.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                    {speaker.trend}
                  </div>
                </div>
              </div>

              <button className="btn-secondary w-full text-sm">View Details</button>
            </div>
          ))}
        </div>

        {/* Performance Insights */}
        <h2 className="text-xl font-semibold text-slate-900 mb-4">Performance Insights</h2>
        <div className="space-y-4">
          <div className="card border-l-4 border-green-500">
            <h3 className="font-semibold text-slate-900 mb-2">🎯 Sarah's Strengths</h3>
            <p className="text-slate-600 text-sm">
              Consistently high action item completion rate. Clear communication on compliance topics.
            </p>
          </div>

          <div className="card border-l-4 border-amber-500">
            <h3 className="font-semibold text-slate-900 mb-2">⚠️ Mike's Improvement Areas</h3>
            <p className="text-slate-600 text-sm">
              Action items sometimes lack clear ownership. Consider following up with written summaries.
            </p>
          </div>

          <div className="card border-l-4 border-red-500">
            <h3 className="font-semibold text-slate-900 mb-2">🚨 John's Coaching Priority</h3>
            <p className="text-slate-600 text-sm">
              Tension signals detected in 3 of 4 calls. Recommend training on difficult conversations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}