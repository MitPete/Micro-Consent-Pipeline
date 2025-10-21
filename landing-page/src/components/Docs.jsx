import React from 'react'

function Docs() {
  return (
    <section className="bg-gray-50 section-padding">
      <div className="container-max">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          API Documentation
        </h2>
        <div className="bg-white p-8 rounded-lg shadow-sm">
          <h3 className="text-xl font-semibold mb-4">Health Check</h3>
          <pre className="bg-gray-100 p-4 rounded mb-6 overflow-x-auto">
            <code>{`curl https://api.microconsent.dev/health

Response:
{
  "status": "ok",
  "timestamp": "2023-12-07T10:30:00.123456",
  "version": "1.0.0"
}`}</code>
          </pre>

          <h3 className="text-xl font-semibold mb-4">Analyze Consent</h3>
          <pre className="bg-gray-100 p-4 rounded mb-6 overflow-x-auto">
            <code>{`curl -X POST https://api.microconsent.dev/analyze \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: your-api-key" \\
  -d '{
    "source": "<html><body><button>Accept All</button></body></html>",
    "output_format": "json"
  }'`}</code>
          </pre>

          <div className="flex gap-4">
            <a
              href="https://api.microconsent.dev/docs"
              className="btn-primary"
            >
              Interactive API Docs
            </a>
            <a
              href="https://github.com/MitPete/Micro-Consent-Pipeline/blob/main/API_USAGE.md"
              className="btn-secondary"
            >
              Full Documentation
            </a>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Docs