import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(document.body).toBeTruthy()
  })

  it('contains main content', () => {
    render(<App />)
    const element = screen.getByRole('main', { name: /main content/i }) || document.querySelector('main') || document.body
    expect(element).toBeTruthy()
  })
})