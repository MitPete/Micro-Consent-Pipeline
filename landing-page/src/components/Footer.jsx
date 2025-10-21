import React from 'react'

function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="container-max">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-lg font-semibold mb-4">Micro-Consent Pipeline</h3>
            <p className="text-gray-400">
              AI-powered consent analysis for privacy compliance auditing.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Services</h4>
            <ul className="space-y-2 text-gray-400">
              <li><a href="https://api.microconsent.dev" className="hover:text-white">REST API</a></li>
              <li><a href="https://dashboard.microconsent.dev" className="hover:text-white">Live Dashboard</a></li>
              <li><a href="https://github.com/MitPete/Micro-Consent-Pipeline" className="hover:text-white">GitHub</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Documentation</h4>
            <ul className="space-y-2 text-gray-400">
              <li><a href="https://github.com/MitPete/Micro-Consent-Pipeline/blob/main/README.md" className="hover:text-white">Getting Started</a></li>
              <li><a href="https://github.com/MitPete/Micro-Consent-Pipeline/blob/main/API_USAGE.md" className="hover:text-white">API Guide</a></li>
              <li><a href="https://github.com/MitPete/Micro-Consent-Pipeline/blob/main/DEPLOYMENT.md" className="hover:text-white">Deployment</a></li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold mb-4">Community</h4>
            <ul className="space-y-2 text-gray-400">
              <li><a href="https://github.com/MitPete/Micro-Consent-Pipeline/issues" className="hover:text-white">Issues</a></li>
              <li><a href="https://github.com/MitPete/Micro-Consent-Pipeline/discussions" className="hover:text-white">Discussions</a></li>
              <li><a href="https://github.com/MitPete/Micro-Consent-Pipeline/blob/main/CONTRIBUTING.md" className="hover:text-white">Contributing</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2025 Micro-Consent Pipeline. MIT License.</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer