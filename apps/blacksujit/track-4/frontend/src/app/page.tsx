export default function Home() {
  return (
    <div style={{ minHeight: '100vh', background: 'white', padding: '20px' }}>
      <h1 style={{ fontSize: '48px', fontWeight: 'bold', color: 'black' }}>
        Stop watching. Start coaching.
      </h1>
      <p style={{ fontSize: '20px', color: '#1e293b' }}>
        Turn your team's call recordings into coaching insights.
      </p>
      <div style={{ marginTop: '20px' }}>
        <span>Private</span>
        <span> · </span>
        <span>Fast</span>
        <span> · </span>
        <span>Actionable</span>
      </div>
      <a 
        href="/settings" 
        style={{ 
          display: 'inline-block', 
          background: '#007AFF', 
          color: 'white', 
          padding: '16px 32px', 
          borderRadius: '8px',
          textDecoration: 'none',
          marginTop: '20px'
        }}
      >
        Connect WhipScribe
      </a>
    </div>
  );
}