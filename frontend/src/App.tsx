import { Routes, Route, Link } from "react-router-dom";
import Home from "@/pages/Home";
import About from "@/pages/About";
import NotFound from "@/pages/NotFound";
import DetailsView from "@/pages/Details";
import Debug from "./pages/Debug";
import BasicDataSandboxView from "./pages/BasicDataSandbox";
import AdvancedDataSandboxView from "./pages/AdvancedDataSandbox";

function App() {
  return (
    <>
      <nav className="p-4">
        <Link to="/" className="mr-4">
          Home
        </Link>
        <Link to="/sandbox">Data Sandbox</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/details/:id" element={<DetailsView />} />
        <Route path="/about" element={<About />} />
        <Route path="/sandbox" element={<BasicDataSandboxView />} />
        <Route path="/sandbox/advanced" element={<AdvancedDataSandboxView />} />
        <Route path="/debug" element={<Debug />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}

export default App;
