import { ArrowRight } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { useState } from 'react'
import { useNavigate } from 'react-router'

function Home() {
  const navigate = useNavigate()
  const [url, setURL] = useState('')
  const submitURL = async () => {
    // update ui - disable field input and button, change icon to Spinner

    // actually try to submit url
    const response = await fetch(".../api/create", {
      body: JSON.stringify({
        url: "http://example.com"
      }),
      headers: {
        "Content-Type": "application/json"
      },
      method: "POST"
    })

    if (response.ok) {
      // yay! let's go to the details page
      const data = await response.json()
    } else {
      // fuck. reset ui, show the error (if we can, of course)
    }
    navigate("/details/123")
  }
  
  return (
    <main className="">
      <h1 className="text-5xl font-semibold">ARGUS</h1>
      <p>words here about how this is the best tool ever</p>

      <div className="rounded-full border-2 transition border-red-400 hover:border-red-300 flex pl-2">
        <input autoFocus type="url" placeholder="Enter a URL..." className="grow" onChange={e => setURL(e.target.value)} value={url} />
        <Button variant="outline" size="icon" className="rounded-full border-red-400 border-2" onClick={submitURL}>
          <ArrowRight />
        </Button>
      </div>
      <div className="text-red-500">sowwy :c</div>
    </main>
  )
}

export default Home
