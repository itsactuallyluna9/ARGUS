import { useState, useEffect, useRef } from "react"
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from "@/components/ui/resizable"
import { Spinner } from "@/components/ui/spinner"
import { WebR } from "webr"
import { Button } from "@/components/ui/button"
import { Play, HardDriveDownload, HardDriveUpload, Square, ChartArea, Download, Upload } from "lucide-react"
import { EditorView, basicSetup } from "codemirror"
import { r } from "codemirror-lang-r"
import { ButtonGroup } from "@/components/ui/button-group"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { Separator } from "@/components/ui/separator"
import { Pagination, PaginationContent, PaginationItem, PaginationPrevious, PaginationLink, PaginationEllipsis, PaginationNext } from "@/components/ui/pagination"

function DataSandboxView() {
  const [rLoaded, setRLoaded] = useState(false)
  const [rInstallingPackages, setRInstallingPackages] = useState(false)
  const [rWorking, setRWorking] = useState(false)

  const [rBusy, setRBusy] = useState(false)
  const [rBusyMessage, setRBusyMessage] = useState("")
  
  const webRRef = useRef<WebR | null>(null)
  const isInitialized = useRef(false)
  
  const editorRef = useRef<HTMLDivElement | null>(null)
  const viewRef = useRef<EditorView | null>(null)
  const consoleRef = useRef<HTMLDivElement | null>(null)

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
        await webR.evalRVoid("webr::viewer_install()");
        await webR.evalRVoid("webr::pager_install()");
        await webR.evalRVoid(`
          webr::canvas_install(
            width = getOption("webr.fig.width", 504),
            height = getOption("webr.fig.height", 504)
          )
        `);
        await webR.evalRVoid("webr::shim_install()");
        await webR.evalRVoid("options(webr.show_menu = TRUE)")
        await webR.evalRVoid("webr::global_prompt_install()", {
          withHandlers: false
        })
        await webR.evalRVoid("options(rgl.printRglwidget = TRUE)")
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
    if (!editorRef.current) return
    
    viewRef.current = new EditorView({
      doc: "# hello, world!\n1 + 1\n\nplot(cars)",
      extensions: [basicSetup, r()],
      parent: editorRef.current
    })
    return () => {
      const view = viewRef.current
      if (view) {
        view.destroy()
        viewRef.current = null
      }
    }
  }, [])

  const runCode = async () => {
    if (!webRRef.current) return
    if (!viewRef.current) return
    if (!consoleRef.current) return
    
    const code = viewRef.current.state.doc.toString()
    console.log("Running code:\n", code)

    // pass it to r
    setRWorking(true)
    await webRRef.current.evalRVoid(code)
    setRWorking(false)
  }

  const interruptR = () => {
    if (!webRRef.current) return
    webRRef.current.interrupt()
  }
  
  return (
    <main className="w-full h-screen">
      <ResizablePanelGroup orientation="horizontal">
        <ResizablePanel>
          <ResizablePanelGroup orientation="vertical">
            <ResizablePanel defaultSize="75%">
              <div className="flex items-center justify-end space-x-2 p-2">
                <ButtonGroup>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button size="icon" variant="outline">
                        <Upload />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" sideOffset={8}>
                      Upload file
                    </TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button size="icon" variant="outline">
                        <Download />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" sideOffset={8}>
                      Download file
                    </TooltipContent>
                  </Tooltip>
                </ButtonGroup>
                <ButtonGroup>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button size="icon" disabled={rBusy} variant="outline" onClick={runCode}>
                        {rWorking ? <Spinner /> : <Play />}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" sideOffset={8}>
                      Run code
                    </TooltipContent>
                  </Tooltip>
                  { window.crossOriginIsolated && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button size="icon" disabled={!rWorking} variant="destructive" onClick={interruptR}>
                        <Square />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" sideOffset={8}>
                      Interrupt execution
                    </TooltipContent>
                  </Tooltip>
                  )}
                </ButtonGroup>
              </div>
              <div ref={editorRef} />
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel>
              {((!rLoaded) || rInstallingPackages) && (
                <div className="flex items-center space-x-2 justify-center">
                  <Spinner />
                  <p>{rBusyMessage}</p>
                </div>
              )}
              <div className="font-mono" ref={consoleRef}></div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel>
          <ResizablePanelGroup orientation="vertical">
            <ResizablePanel>
              <p>control panel - to be implemented!</p>
            </ResizablePanel>
            <ResizableHandle withHandle/>
            <ResizablePanel defaultSize="60%">
              <div className="flex flex-col items-center justify-center h-full space-y-4">
                <ChartArea className="mx-auto mb-4" size={48} />
                <p>No plots to display. Try using <span className="font-mono text-pink-900 bg-pink-100 rounded">plot()</span> or <span className="font-mono text-pink-900 bg-pink-100 rounded">ggplot()</span>.</p>
              </div>
              <Tooltip>
                <TooltipTrigger className="flex items-center">
                  <Button size="icon" variant="outline">
                    <Download />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Download Chart</p>
                </TooltipContent>
              </Tooltip>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
      </ResizablePanelGroup>
    </main>
  );
}

export default DataSandboxView;
