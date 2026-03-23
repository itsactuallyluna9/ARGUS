import { useState, useEffect, useRef } from "react"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { Spinner } from "@/components/ui/spinner"
import { WebR } from "webr"
import { Button } from "@/components/ui/button"
import { Play, HardDriveDownload, HardDriveUpload } from "lucide-react"
import { EditorView, basicSetup } from "codemirror"
import { r } from "codemirror-lang-r"

function DataSandboxView() {
  const [rLoaded, setRLoaded] = useState(false)
  const [rInstallingPackages, setRInstallingPackages] = useState(false)
  const [rWorking, setRWorking] = useState(false)

  const [rBusy, setRBusy] = useState(false)
  const [rBusyMessage, setRBusyMessage] = useState("")
  
  const webRRef = useRef<WebR | null>(null)
  const isInitialized = useRef(false)

  const editorRef = useRef(null)
  const viewRef = useRef(null)

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

  useEffect(() => {
    if (viewRef.current) return
    
    viewRef.current = new EditorView({
      doc: "# hello, world!",
      extensions: [basicSetup, r()],
      parent: editorRef.current
    })
    return () => {
      viewRef.current.destroy()
      viewRef.current = null
    }
  }, [])
  
  return (
    <main className="w-full h-screen">
      <ResizablePanelGroup orientation="horizontal">
        <ResizablePanel>
          <ResizablePanelGroup orientation="vertical">
            <ResizablePanel>
              <div>
                <Button size="icon">
                  <Play />
                </Button>
                <Button size="icon">
                  <HardDriveUpload />
                </Button>
                <Button size="icon">
                  <HardDriveDownload />
                </Button>
              </div>
              <div ref={editorRef} />
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel>
              <div className="font-mono"></div>
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
