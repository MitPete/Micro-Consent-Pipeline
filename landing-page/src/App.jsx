import React from 'react'
import Hero from './components/Hero'
import Features from './components/Features'
import Docs from './components/Docs'
import Metrics from './components/Metrics'
import Footer from './components/Footer'

function App() {
  return (
    <div className="min-h-screen bg-white">
      <Hero />
      <Features />
      <Docs />
      <Metrics />
      <Footer />
    </div>
  )
}

export default App