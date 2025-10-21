import React from 'react'

function Features() {
  const features = [
    {
      title: 'AI-Powered Analysis',
      description: 'Machine learning models automatically classify consent mechanisms and detect dark patterns.'
    },
    {
      title: 'REST API',
      description: 'FastAPI-based REST API with comprehensive documentation and OpenAPI spec.'
    },
    {
      title: 'Real-time Dashboard',
      description: 'Streamlit-powered dashboard for interactive analysis and visualization.'
    },
    {
      title: 'Production Ready',
      description: 'Docker containers, database persistence, async job processing, and monitoring.'
    },
    {
      title: 'Open Source',
      description: 'MIT licensed, community-driven development with comprehensive documentation.'
    },
    {
      title: 'Privacy Focused',
      description: 'Built specifically for privacy compliance auditing and consent mechanism analysis.'
    }
  ]

  return (
    <section className="bg-white section-padding">
      <div className="container-max">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
          Key Features
        </h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="bg-gray-50 p-6 rounded-lg">
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {feature.title}
              </h3>
              <p className="text-gray-600">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default Features