import React from 'react'
import ReactDOM from 'react-dom/client'

const rootElement = document.getElementById('root')
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement)
  const element = React.createElement('div', {
    style: {
      height: '100vh',
      width: '100vw',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#0d1117',
      color: '#c9d1d9',
      fontFamily: 'Inter, system-ui, sans-serif'
    }
  }, 
    React.createElement('div', {
      style: { textAlign: 'center' }
    },
      React.createElement('h1', {
        style: { fontSize: '32px', marginBottom: '16px', fontWeight: 'bold' }
      }, 'JARVIS AI Assistant'),
      React.createElement('p', {
        style: { fontSize: '16px', color: '#8b949e' }
      }, 'No JSX Test'),
      React.createElement('p', {
        style: { fontSize: '14px', color: '#58a6ff', marginTop: '24px' }
      }, '✓ React.createElement Working')
    )
  )
  root.render(element)
}
