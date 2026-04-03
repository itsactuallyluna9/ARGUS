import { Routes, Route, Link } from "react-router-dom";
import Home from "@/pages/Home";
import About from "@/pages/About";
import NotFound from "@/pages/NotFound";
import DetailsView from "@/pages/Details";
import Debug from "./pages/Debug";
import BasicDataSandboxView from "./pages/BasicDataSandbox";
import AdvancedDataSandboxView from "./pages/AdvancedDataSandbox";
import TernaryThemeButton from "./components/TernaryThemeButton";
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "./components/ui/navigation-menu";

function App() {
  return (
    <>
      <NavigationMenu className="w-full">
        <NavigationMenuList>
          <NavigationMenuItem>
            <NavigationMenuLink
              asChild
              className={navigationMenuTriggerStyle()}
            >
              <Link to="/">ARGUS</Link>
            </NavigationMenuLink>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuTrigger>
              <NavigationMenuLink
                asChild
                className={navigationMenuTriggerStyle()}
              >
                <Link to="/sandbox">Data Sandbox</Link>
              </NavigationMenuLink>
            </NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul className="w-64">
                <NavigationMenuLink asChild>
                  <Link to="/sandbox">Basic</Link>
                </NavigationMenuLink>
                <NavigationMenuLink asChild>
                  <Link to="/sandbox/advanced">Advanced</Link>
                </NavigationMenuLink>
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
          <NavigationMenuItem>
            <NavigationMenuLink
              asChild
              className={navigationMenuTriggerStyle()}
            >
              <Link to="/debug">Debug</Link>
            </NavigationMenuLink>
          </NavigationMenuItem>
        </NavigationMenuList>
        <div className="w-screen"></div>
        <TernaryThemeButton variant="ghost" />
      </NavigationMenu>

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
