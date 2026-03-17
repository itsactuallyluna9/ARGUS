import { useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'

function App() {
  const [message, setMessage] = useState('Click the button to call Flask.')
  const [loading, setLoading] = useState(false)

  const apiBaseUrl = useMemo(() => import.meta.env.VITE_API_URL ?? '', [])

  const handlePingApi = async () => {
    setLoading(true)

    try {
      const apiUrl = apiBaseUrl ? `${apiBaseUrl}/api/hello` : '/api/hello'
      const response = await fetch(apiUrl)
      const data = (await response.json()) as { message?: string }

      setMessage(data.message ?? 'Backend replied with no message.')
    } catch {
      setMessage('Could not reach backend. Is Flask running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-6">
      <section className="w-full max-w-xl rounded-xl border bg-white p-8 text-center shadow-sm">
        <h1 className="mb-3 text-3xl font-semibold tracking-tight">ARGUS</h1>
        <p className="mb-6 text-slate-600">React + Tailwind + Flask hello world</p>

        <Button onClick={handlePingApi} disabled={loading}>
          {loading ? 'Calling API...' : 'Call Flask API'}
        </Button>

        <p className="mt-6 text-sm text-slate-700">{message}</p>
      </section>
    </main>
  )
}

export default App
