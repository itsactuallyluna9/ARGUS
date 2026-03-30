import { useState, useEffect, useRef } from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Spinner } from "@/components/ui/spinner";
import { WebR } from "webr";
import { Button } from "@/components/ui/button";
import { Play, Square, ChartArea, Download, Upload, Cat } from "lucide-react";
import { EditorView, basicSetup } from "codemirror";
import { r } from "codemirror-lang-r";
import { ButtonGroup } from "@/components/ui/button-group";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Terminal } from "@xterm/xterm";
import { FitAddon } from "@xterm/addon-fit";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import "@xterm/xterm/css/xterm.css";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const ENTER_KEY = 13;
const BACKSPACE_KEY = 127;
const FIRST_PRINTABLE_CHAR = 32;

function convertToCSV(data: Record<string, any>[]): string {
  let fields: string[] = [];
  data.forEach((entry) => {
    const current_entry_fields = Object.keys(entry);
    const new_fields = current_entry_fields.filter(
      (val) => !fields.includes(val),
    );
    fields = fields.concat(new_fields);
  });

  // rfc 4180 compliant csv field escaping
  const escapeCSVField = (value: unknown): string => {
    if (value === undefined) {
      return "NA";
    }
    if (value === null) {
      return "";
    }
    const str = typeof value === "string" ? value : JSON.stringify(value);
    // check if the value needs quoting (contains comma, quote, or newline)
    const needsQuoting =
      str.includes(",") ||
      str.includes('"') ||
      str.includes("\n") ||
      str.includes("\r");
    if (needsQuoting) {
      // escape double quotes by doubling them, then wrap in quotes
      return '"' + str.replace(/"/g, '""') + '"';
    }
    return str;
  };

  return [
    fields.join(","),
    ...data.map((entry) =>
      fields.map((fieldName) => escapeCSVField(entry[fieldName])).join(","),
    ),
  ].join("\n");
}

function DataSandboxView() {
  const [rLoaded, setRLoaded] = useState(false);
  const [rInstallingPackages, setRInstallingPackages] = useState(false);
  const [rWorking, setRWorking] = useState(false);

  const [rBusy, setRBusy] = useState(false);
  const [rBusyMessage, setRBusyMessage] = useState("");

  const webRRef = useRef<WebR | null>(null);
  const xtermRef = useRef<Terminal | null>(null);
  const terminalInputBufferRef = useRef("");

  const editorRef = useRef<HTMLDivElement | null>(null);
  const viewRef = useRef<EditorView | null>(null);
  const consoleRef = useRef<HTMLDivElement | null>(null);

  const [canvasImages, setCanvasImages] = useState<string[]>([]);
  const [canvasImageIndex, setCanvasImageIndex] = useState(0); // which canvas is the user viewing?
  const [canvasDrawIndex, setCanvasDrawIndex] = useState(0); // which canvas are we currently drawing on?
  const drawCanvas = useRef<OffscreenCanvas | null>(null);

  const [viewData, setViewData] = useState<Record<string, unknown>[]>([]);
  const [viewTitle, setViewTitle] = useState("");

  const [pagerContent, setPagerContent] = useState("");
  const [pagerTitle, setPagerTitle] = useState("");
  const [pagerMethod, setPagerMethod] = useState("");

  const [currentTab, setCurrentTab] = useState("data-loader");

  useEffect(() => {
    if (!rLoaded) {
      setRBusy(true);
      setRBusyMessage("R is loading...");
    } else if (rInstallingPackages) {
      setRBusy(true);
      setRBusyMessage("R is installing packages...");
    } else if (rWorking) {
      setRBusy(true);
      setRBusyMessage("Processing...");
    } else {
      setRBusy(false);
      setRBusyMessage("");
    }
  }, [rLoaded, rInstallingPackages, rWorking]);

  const fetchData = async () => {
    if (!webRRef.current) return;
    if (!xtermRef.current) return;
    if (rBusy) return;
    setRWorking(true);

    xtermRef.current.writeln(`# Downloading Data (this may take a while)`);

    // TODO: handle existing files
    // await webRRef.current.FS.unlink("/home/web_user/data");
    await webRRef.current.FS.mkdir("/home/web_user/data");

    const response = await fetch("/api/data");
    if (!response.ok) {
      // TODO: panic
      return;
    }
    const data = await response.json();

    await webRRef.current.FS.writeFile(
      "/home/web_user/data/article_data.csv",
      new TextEncoder().encode(convertToCSV(data.articles)),
    );
    await webRRef.current.FS.writeFile(
      "/home/web_user/data/fact_check_data.csv",
      new TextEncoder().encode(convertToCSV(data.fact_checks)),
    );

    xtermRef.current.writeln(
      "# Downloaded data to ~/data/article_data.csv and ~/data/fact_check_data.csv",
    );

    setRWorking(false);
  };

  useEffect(() => {
    let isDisposed = false;
    let resizeObserver: ResizeObserver | null = null;
    let removeFocusListener: (() => void) | null = null;

    const loadR = async () => {
      try {
        setRBusy(true);
        setRBusyMessage("Terminal is loading...");
        const consoleElement = consoleRef.current;
        if (!consoleElement) {
          throw new Error("Terminal container not found");
        }

        const terminalInstance = new Terminal({
          cursorBlink: true,
          convertEol: true,
          fontSize: 12,
        });
        const fitAddon = new FitAddon();
        terminalInstance.loadAddon(fitAddon);
        terminalInstance.open(consoleElement);
        fitAddon.fit();
        requestAnimationFrame(() => fitAddon.fit());
        terminalInstance.focus();

        resizeObserver = new ResizeObserver(() => {
          fitAddon.fit();
        });
        resizeObserver.observe(consoleElement);
        const focusTerminal = () => {
          terminalInstance.focus();
        };
        consoleElement.addEventListener("click", focusTerminal);
        removeFocusListener = () => {
          consoleElement.removeEventListener("click", focusTerminal);
        };
        terminalInstance.onData((data) => {
          if (!webRRef.current) return;

          const code = data.charCodeAt(0);

          // enter: submit the buffered command to webr console.
          if (code === ENTER_KEY) {
            const command = terminalInputBufferRef.current;
            terminalInstance.writeln("");
            terminalInputBufferRef.current = "";
            setRWorking(true);
            webRRef.current.writeConsole(command);
            return;
          }

          // backspace: remove one char from local buffer and terminal view.
          if (code === BACKSPACE_KEY) {
            if (terminalInputBufferRef.current.length > 0) {
              terminalInputBufferRef.current =
                terminalInputBufferRef.current.slice(0, -1);
              terminalInstance.write("\b \b"); // actually delete the character
            }
            return;
          }

          // ignore control characters; print and buffer regular characters.
          if (code < FIRST_PRINTABLE_CHAR) return;
          terminalInputBufferRef.current += data;
          terminalInstance.write(data);
        });
        xtermRef.current = terminalInstance;

        setRBusyMessage("R is loading...");

        // init webr
        const webR = new WebR();
        await webR.init();
        await webR.evalRVoid("webr::viewer_install()");
        await webR.evalRVoid("webr::pager_install()");
        await webR.evalRVoid(`
          webr::canvas_install(
            width = getOption("webr.fig.width", 504),
            height = getOption("webr.fig.height", 504)
          )
        `);
        await webR.evalRVoid("webr::shim_install()");
        // await webR.evalRVoid("options(webr.show_menu = TRUE)") // let the users suffer
        await webR.evalRVoid("webr::global_prompt_install()", {
          withHandlers: false,
        });
        await webR.evalRVoid("options(rgl.printRglwidget = TRUE)");
        webRRef.current = webR;

        setRLoaded(true);
        console.log("WebR loaded successfully");

        // install packages
        setRInstallingPackages(true);
        setRBusyMessage("Installing tidyverse package...");

        // await webR.installPackages(["tidyverse", "plotly", "gapminder"])

        setRInstallingPackages(false);
        console.log("tidyverse installed successfully");

        if (isDisposed) return;

        // start processing WebR events for this mount
        processRStreamEvents(webR, terminalInstance, () => isDisposed);
      } catch (error) {
        console.error("Error loading R or installing packages:", error);
        setRLoaded(false);
        setRInstallingPackages(false);
      }
    };

    void loadR();

    return () => {
      isDisposed = true;
      removeFocusListener?.();
      removeFocusListener = null;
      resizeObserver?.disconnect();
      resizeObserver = null;
      xtermRef.current?.dispose();
      xtermRef.current = null;
    };
  }, []);

  const processRStreamEvents = async (
    webR: WebR,
    terminal: Terminal,
    isDisposed: () => boolean,
  ) => {
    for await (const event of webR.stream()) {
      if (isDisposed()) {
        return;
      }

      switch (event.type) {
        case "stdout":
          console.log("R stdout:", event.data);
          terminal.writeln(event.data);
          break;
        case "stderr":
          console.warn("R stderr:", event.data);
          terminal.writeln(event.data);
          break;
        case "prompt":
          // r is idle and ready for the next command.
          terminal.write(event.data);
          setRWorking(false);
          break;
        case "pager":
          const pager_file = await webR.FS.readFile(event.data.path);
          if (event.data.deleteFile) {
            await webR.FS.unlink(event.data.path);
          }
          setCurrentTab("pager");
          setPagerMethod("pager");
          setPagerTitle(event.data.title);
          setPagerContent(new TextDecoder().decode(pager_file));
          break;
        case "view":
          setCurrentTab("view");
          setViewTitle(event.data.title);
          const to_process = event.data.data;
          // convert Object{col_name: {type: ... names: ... values: []}} to
          // [{col_name: value, ...}, ...]
          let converted = [];
          for (
            let i = 0;
            i < to_process[Object.keys(to_process)[0]].values.length;
            i++
          ) {
            let row = {};
            for (const col_name in to_process) {
              row[col_name] = to_process[col_name].values[i];
            }
            converted.push(row);
          }
          setViewData(converted);
          break;
        case "browse":
          console.log(event);
          let html_source = new TextDecoder().decode(
            await webR.FS.readFile(event.data.url),
          );
          // okay, we need to do the following:
          // 1) replace all <script src=...> tags with inline scripts
          // - should read from /path/to/R/library/plotly/htmlwidgets/{path}
          // 2) make it iframable
          // - either url or just. set the source.
          const root_node = new DOMParser().parseFromString(
            html_source,
            "text/html",
          );

          const htmlDir = event.data.url.substring(
            0,
            event.data.url.lastIndexOf("/"),
          );

          // inline all external scripts
          for (const script of root_node.scripts) {
            if (script.src) {
              const script_src = new URL(script.src).pathname;
              // resolve the script path relative to where we got the html
              const script_path = script_src.startsWith("/")
                ? `${htmlDir}${script_src}`
                : `${htmlDir}/${script_src}`;
              console.log(`Reading script from: ${script_path}`);
              script.textContent = new TextDecoder().decode(
                await webR.FS.readFile(script_path),
              );
              script.removeAttribute("src");
            }
          }

          // inline all external stylesheets
          const links = root_node.querySelectorAll('link[rel="stylesheet"]');
          for (const link of links) {
            const href = link.getAttribute("href");
            if (href) {
              const css_src = new URL(href, "file:///").pathname;
              const css_path = css_src.startsWith("/")
                ? `${htmlDir}${css_src}`
                : `${htmlDir}/${css_src}`;
              console.log(`Reading stylesheet from: ${css_path}`);
              const css_content = new TextDecoder().decode(
                await webR.FS.readFile(css_path),
              );
              // replace the link element with an inline style element
              const style = root_node.createElement("style");
              style.textContent = css_content;
              link.replaceWith(style);
            }
          }

          html_source = root_node.documentElement.outerHTML;

          setCurrentTab("pager");
          setPagerMethod("browse");
          setPagerTitle("Plotly Graph");
          setPagerContent(html_source);
          break;
        case "canvas":
          switch (event.data.event) {
            case "canvasNewPage":
              // alright, we have a new plot coming in
              // if there's an old canvas, save it
              console.debug("R: drawing new canvas page", event.data);
              if (drawCanvas.current) {
                const blob = await drawCanvas.current.convertToBlob();
                const url = URL.createObjectURL(blob);
                setCanvasImages((prev) => [...prev, url]);
                setCanvasDrawIndex((prev) => {
                  const nextIndex = prev + 1;
                  setCanvasImageIndex(nextIndex);
                  return nextIndex;
                });
              }
              drawCanvas.current = new OffscreenCanvas(1008, 1008);
              break;
            case "canvasImage":
              console.debug("R: drawing to canvas", event.data);
              if (!drawCanvas.current) {
                console.error(
                  "Received canvas image data but no canvas exists!",
                );
                break;
              }
              const ctx = drawCanvas.current.getContext("2d");
              if (!ctx) {
                console.error("Could not get 2D context from canvas!");
                break;
              }
              ctx.drawImage(event.data.image, 0, 0); // draw what we got!
              // okay, can we now put that on the screen? reduce the delay
              // also can't promise we'll actually recieve newpage when we're done, so we'll just update the image as we get it and hope for the best
              const blob = await drawCanvas.current.convertToBlob();
              const url = URL.createObjectURL(blob);
              setCanvasImages((prev) => {
                const newImages = [...prev];
                newImages[canvasDrawIndex] = url;
                return newImages;
              });
              break;
          }
          break;
        case "closed":
          console.error("R session closed - this should not happen!!");
          setRLoaded(false);
          setRBusyMessage(
            "R session closed unexpectedly - please refresh the page",
          );
          break;
        default:
          console.warn("Unknown event type:", event);
      }
    }
  };

  useEffect(() => {
    if (viewRef.current) return;
    if (!editorRef.current) return;

    viewRef.current = new EditorView({
      doc: "# hello, world!\n1 + 1\n\nplot(cars)",
      extensions: [basicSetup, r()],
      parent: editorRef.current,
    });
    return () => {
      const view = viewRef.current;
      if (view) {
        view.destroy();
        viewRef.current = null;
      }
    };
  }, []);

  const runCode = async () => {
    if (!webRRef.current) return;
    if (!viewRef.current) return;
    if (!consoleRef.current) return;

    const code = viewRef.current.state.doc.toString();
    console.log("Running code:\n", code);

    // pass it to r
    setRWorking(true);
    await webRRef.current.FS.writeFile(
      "/tmp/.webRtmp-source",
      new TextEncoder().encode(code),
    );
    webRRef.current.writeConsole(
      "source('/tmp/.webRtmp-source', echo = TRUE, max.deparse.length = Inf)",
    );
    setRWorking(false);
    // we'll set this to false when we get the prompt event, which indicates that r is done processing and waiting for more input
    // we don't really have a great way to know this, unfortunately.
  };

  const interruptR = () => {
    if (!webRRef.current) return;
    webRRef.current.interrupt();
  };

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
                      <Button
                        size="icon"
                        disabled={rBusy}
                        variant="outline"
                        onClick={runCode}
                      >
                        {rWorking ? <Spinner /> : <Play />}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" sideOffset={8}>
                      Run code
                    </TooltipContent>
                  </Tooltip>
                  {window.crossOriginIsolated && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          size="icon"
                          disabled={!rWorking}
                          variant="destructive"
                          onClick={interruptR}
                        >
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
            <ResizablePanel className="flex h-full flex-col">
              {(!rLoaded || rInstallingPackages) && (
                <div className="flex items-center space-x-2 justify-center z-50">
                  <Spinner />
                  <p>{rBusyMessage}</p>
                </div>
              )}
              <div
                className="h-full min-h-0 w-full overflow-hidden font-mono text-xs"
                ref={consoleRef}
              ></div>
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel>
          <ResizablePanelGroup orientation="vertical">
            <ResizablePanel>
              <Tabs
                defaultValue="data-loader"
                value={currentTab}
                onValueChange={setCurrentTab}
              >
                <TabsList>
                  <TabsTrigger value="data-loader">Data Loader</TabsTrigger>
                  <TabsTrigger value="documentation">Documentation</TabsTrigger>
                  <TabsTrigger value="view" disabled={viewData.length === 0}>
                    View
                  </TabsTrigger>
                  <TabsTrigger value="pager" disabled={pagerContent === ""}>
                    Pager
                  </TabsTrigger>
                  <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>
                <TabsContent value="data-loader">
                  <Button size="icon" onClick={fetchData}>
                    <Cat />
                  </Button>
                </TabsContent>
                <TabsContent value="view">
                  <Table>
                    <TableCaption>
                      {viewTitle} | {viewData.length} rows
                    </TableCaption>
                    <TableHeader>
                      <TableRow>
                        {viewData[0] &&
                          Object.keys(viewData[0]).map((col_name) => (
                            <TableCell key={col_name}>{col_name}</TableCell>
                          ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {viewData.map((row, index) => (
                        <TableRow key={index}>
                          {Object.values(row).map((value, i) => (
                            <TableCell key={i}>{String(value)}</TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TabsContent>
                <TabsContent value="pager">
                  {pagerMethod === "browse" && (
                    <iframe
                      title={pagerTitle}
                      srcDoc={pagerContent}
                      sandbox="allow-scripts"
                      className="w-full h-96 border"
                    />
                  )}
                  {pagerMethod === "pager" && (
                    <>
                      <h2 className="text-lg font-bold">{pagerTitle}</h2>
                      <pre className="whitespace-pre-wrap">{pagerContent}</pre>
                    </>
                  )}
                </TabsContent>
              </Tabs>
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize="60%">
              {canvasImages.length > 0 ? (
                <>
                  <img
                    src={canvasImages[canvasImageIndex]}
                    alt={`Canvas ${canvasImageIndex + 1}`}
                    className="mx-auto mb-4 h-7/8"
                  />
                  <ButtonGroup className="justify-center">
                    <Button
                      size="icon"
                      variant="outline"
                      disabled={canvasImageIndex === 0}
                      onClick={() => setCanvasImageIndex((prev) => prev - 1)}
                    >
                      Previous
                    </Button>
                    <Button
                      size="icon"
                      variant="outline"
                      disabled={canvasImageIndex === canvasImages.length - 1}
                      onClick={() => setCanvasImageIndex((prev) => prev + 1)}
                    >
                      Next
                    </Button>
                  </ButtonGroup>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full space-y-4">
                  <ChartArea className="mx-auto mb-4" size={48} />
                  <p>
                    No plots to display. Try using{" "}
                    <span className="font-mono text-pink-900 bg-pink-100 dark:text-pink-100 dark:bg-pink-900 rounded">
                      plot()
                    </span>{" "}
                    or{" "}
                    <span className="font-mono text-pink-900 bg-pink-100 dark:text-pink-100 dark:bg-pink-900 rounded">
                      ggplot()
                    </span>
                    .
                  </p>
                </div>
              )}
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
