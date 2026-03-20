import { ArrowRight } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useState } from 'react'
import { useNavigate } from 'react-router'

function Home() {
  const navigate = useNavigate()
  const [url, setURL] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errorText, setErrorText] = useState('')

  const submitURL = async () => {
    // update ui - disable field input and button, change icon to Spinner
    setSubmitting(true)

    // basic check: is it a valid url? if not, reset ui and show error
    // we'll do more comprehensive checks on the backend!
    try {
      new URL(url)
    } catch (e) {
      setErrorText("that's not a valid url :c")
      setSubmitting(false)
      return
    }

    // actually try to submit url
    const response = await fetch("http://localhost:5000/api/create", {
      body: JSON.stringify({
        url: url
      }),
      headers: {
        "Content-Type": "application/json"
      },
      method: "POST"
    })

    if (response.ok) {
      // yay! let's go to the details page
      const data = await response.json()
      navigate(`/details/${data.id}`)
    } else {
      // fuck. reset ui, show the error (if we can, of course)
      try {
        const error = await response.json()
        setErrorText(error.message)
      } catch (e) {
        setErrorText("sowwy :c")
      }
      setSubmitting(false)
    }
  }
  
  return (
    <main className="">
      <h1 className="text-5xl font-semibold">ARGUS</h1>
      <p>words here about how this is the best tool ever</p>

      <div className="rounded-full border-2 transition border-red-400 hover:border-red-300 flex pl-2">
        <input autoFocus type="url" placeholder="Enter a URL..." className="grow" onChange={e => setURL(e.target.value)} value={url} disabled={submitting} />
        <Button variant="outline" size="icon" className="rounded-full border-red-400 border-2" onClick={submitURL} disabled={submitting}>
          {submitting ? <Spinner /> : <ArrowRight />}
        </Button>
      </div>
      <div className="text-red-500">{errorText}</div>
    </main>
  )
}

export default Home
