import { Link } from 'react-router-dom'

function NotFound() {
  return (
    <main className="">
      <h1>404 - Page Not Found</h1>
      <p>The page you are looking for does not exist.</p>
      <Link to="/">Go back to home</Link>
    </main>
  )
}

export default NotFound
