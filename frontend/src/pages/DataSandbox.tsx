import { useState, useEffect, useRef } from "react"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { Spinner } from "@/components/ui/spinner"
import { WebR } from "webr"

function DataSandboxView() {
  const [rLoaded, setRLoaded] = useState(false)
  const [rInstallingPackages, setRInstallingPackages] = useState(false)
  const [rWorking, setRWorking] = useState(false)

  const [rBusy, setRBusy] = useState(false)
  const [rBusyMessage, setRBusyMessage] = useState("")
  
  const webRRef = useRef<WebR | null>(null)
  const isInitialized = useRef(false)

  useEffect(() => {
    if (!rLoaded) {
      setRBusy(true)
      setRBusyMessage("R is loading...")
    } else if (rInstallingPackages) {
      setRBusy(true)
      setRBusyMessage("R is installing packages...")
    } else if (rWorking) {
      setRBusy(true)
      setRBusyMessage("Processing...")
    } else {
      setRBusy(false)
      setRBusyMessage("")
    }
  }, [rLoaded, rInstallingPackages, rWorking])

  useEffect(() => {
    // Ensure this only runs once
    if (isInitialized.current) return
    isInitialized.current = true
    
    const loadR = async () => {
      try {
        setRBusy(true)
        setRBusyMessage("R is loading...")
        
        // Initialize WebR
        const webR = new WebR()
        await webR.init()
        webRRef.current = webR
        
        setRLoaded(true)
        console.log("WebR loaded successfully")
        
        // Install tidyverse package
        setRInstallingPackages(true)
        setRBusyMessage("Installing tidyverse package...")
        
        await webR.installPackages(["tidyverse"])
        
        setRInstallingPackages(false)
        console.log("tidyverse installed successfully")
        
      } catch (error) {
        console.error("Error loading R or installing packages:", error)
        setRLoaded(false)
        setRInstallingPackages(false)
      }
    }
    
    loadR()
  }, [])
  
  return (
    <main className="w-full h-screen">
      <ResizablePanelGroup orientation="horizontal">
        <ResizablePanel>
          <ResizablePanelGroup orientation="vertical">
            <ResizablePanel>
              <p>script</p>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel>
              <p>console</p>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel>
          <ResizablePanelGroup orientation="vertical">
            <ResizablePanel>
              <p>control panel</p>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel>
              <p>plots</p>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
      </ResizablePanelGroup>
    </main>
  );
}

export default DataSandboxView;
