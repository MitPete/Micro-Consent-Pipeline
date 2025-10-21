import React from 'react'

function Metrics() {
  return (
    <section className="bg-white section-padding">
      <div className="container-max">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Live Metrics & Monitoring
        </h2>
        <div className="bg-gray-100 p-8 rounded-lg text-center">
          <div className="text-gray-500 mb-4">
            📊 Grafana Dashboard Coming Soon
          </div>
          <p className="text-gray-600 mb-6">
            Real-time metrics for API performance, consent analysis throughput,
            and system health monitoring.
          </p>
          <div className="grid md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">1,234</div>
              <div className="text-gray-600">Analyses Today</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">99.9%</div>
              <div className="text-gray-600">Uptime</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">&lt;50ms</div>
              <div className="text-gray-600">Avg Response Time</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Metrics