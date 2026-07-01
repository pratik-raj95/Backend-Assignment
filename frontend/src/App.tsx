import React, { useState } from 'react'
import { Layout } from './components/Layout'
import { DashboardOverview } from './components/DashboardOverview'
import { EventForm } from './components/EventForm'
import { SemanticSearch } from './components/SemanticSearch'
import { SimilarUsers } from './components/SimilarUsers'

const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('dashboard')

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardOverview />
      case 'track':
        return <EventForm />
      case 'search':
        return <SemanticSearch />
      case 'similarity':
        return <SimilarUsers />
      default:
        return <DashboardOverview />
    }
  }

  return (
    <Layout currentTab={currentTab} setCurrentTab={setCurrentTab}>
      {renderContent()}
    </Layout>
  )
}

export default App
