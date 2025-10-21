import React from 'react'

function Hero() {
  return (
    <section className="bg-gradient-to-br from-blue-50 to-indigo-100 section-padding">
      <div className="container-max text-center">
        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
          AI-Powered Consent Auditing Pipeline
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Analyze and categorize privacy consent mechanisms on websites with our open-source,
          production-ready pipeline. Built with FastAPI, machine learning, and modern DevOps.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href="https://dashboard.microconsent.dev"
            className="btn-primary inline-block text-center"
          >
            Try the Live Dashboard
          </a>
          <a
            href="https://github.com/MitPete/Micro-Consent-Pipeline"
            className="btn-secondary inline-block text-center"
          >
            View on GitHub
          </a>
        </div>
        <div className="mt-8 flex justify-center gap-4">
          <img src="https://img.shields.io/github/v/release/MitPete/Micro-Consent-Pipeline?include_prereleases&label=version" alt="Version" />
          <img src="https://github.com/MitPete/Micro-Consent-Pipeline/workflows/Continuous%20Integration/badge.svg" alt="CI" />
          <img src="https://img.shields.io/github/license/MitPete/Micro-Consent-Pipeline" alt="License" />
        </div>
      </div>
    </section>
  )
}

export default Hero