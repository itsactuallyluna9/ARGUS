import { Routes, Route, Link } from 'react-router-dom'
import Home from '@/pages/Home'
import About from '@/pages/About'
import NotFound from '@/pages/NotFound'
import DetailsView from '@/pages/Details'

function App() {
  return (
    <>
      <nav className="p-4">
        <Link to="/" className="mr-4">Home</Link>
        <Link to="/about">About</Link>
      </nav>
      
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/details/:id" element={<DetailsView />} />
        <Route path="/about" element={<About />} />
        <Route path="/sandbox" element={<></>} />
        <Route path="/debug" element={<></>} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  )
}

export default App
