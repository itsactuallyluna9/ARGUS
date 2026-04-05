import { useState, useEffect, useRef } from "react";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import { Spinner } from "@/components/ui/spinner";
import { WebR } from "webr";
import { Button } from "@/components/ui/button";
import {
  Play,
  Square,
  ChartArea,
  Download,
  Upload,
  FolderDown,
  Trash2,
  FlaskConicalOff,
  ExternalLink,
} from "lucide-react";
import { EditorView, basicSetup } from "codemirror";
import { r } from "codemirror-lang-r";
import { oneDark } from "@codemirror/theme-one-dark";
import { ButtonGroup } from "@/components/ui/button-group";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
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
import { Separator } from "@/components/ui/separator";
import { Link } from "react-router-dom";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { convertToCSV } from "./convertToCSV";

const ENTER_KEY = 13;
const BACKSPACE_KEY = 127;
const FIRST_PRINTABLE_CHAR = 32;

function DataSandboxView() {
  const [rLoaded, setRLoaded] = useState(false);
  const [rInstallingPackages, setRInstallingPackages] = useState(false);
  const [rWorking, setRWorking] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const [rBusy, setRBusy] = useState(false);
  const [rBusyMessage, setRBusyMessage] = useState("");

  const webRRef = useRef<WebR | null>(null);
  const xtermRef = useRef<Terminal | null>(null);
  const terminalInputBufferRef = useRef("");

  const editorRef = useRef<HTMLDivElement | null>(null);
  const viewRef = useRef<EditorView | null>(null);
  const consoleRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handleChange = (e: MediaQueryListEvent) => {
      setDarkMode(e.matches);
    };

    setDarkMode(mediaQuery.matches);

    mediaQuery.addEventListener("change", handleChange);

    return () => {
      mediaQuery.removeEventListener("change", handleChange);
    };
  }, []);

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

    try {
      await webRRef.current.FS.unlink("/home/web_user/data/article_data.csv");
    } catch {
      // File doesn't exist, that's fine
    }
    try {
      await webRRef.current.FS.unlink(
        "/home/web_user/data/fact_check_data.csv",
      );
    } catch {
      // File doesn't exist, that's fine
    }
    // await webRRef.current.FS.unlink("/home/web_user/data");
    try {
      await webRRef.current.FS.mkdir("/home/web_user/data");
    } catch {
      // Directory already exists, that's fine
    }

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

  const downloadData = async () => {
    if (rBusy) return;
    setRWorking(true);

    try {
      const response = await fetch("/api/data");
      if (!response.ok) {
        throw new Error(`Failed to fetch data: ${response.status}`);
      }
      const data = await response.json();

      // download articles data
      const articlesCsv = convertToCSV(data.articles);
      const articlesBlob = new Blob([articlesCsv], { type: "text/csv" });
      const articlesUrl = URL.createObjectURL(articlesBlob);
      const articlesLink = document.createElement("a");
      articlesLink.href = articlesUrl;
      articlesLink.download = "article_data.csv";
      document.body.appendChild(articlesLink);
      articlesLink.click();
      document.body.removeChild(articlesLink);
      URL.revokeObjectURL(articlesUrl);

      // download fact checks data
      const factChecksCsv = convertToCSV(data.fact_checks);
      const factChecksBlob = new Blob([factChecksCsv], { type: "text/csv" });
      const factChecksUrl = URL.createObjectURL(factChecksBlob);
      const factChecksLink = document.createElement("a");
      factChecksLink.href = factChecksUrl;
      factChecksLink.download = "fact_check_data.csv";
      document.body.appendChild(factChecksLink);
      factChecksLink.click();
      document.body.removeChild(factChecksLink);
      URL.revokeObjectURL(factChecksUrl);

      // if we can, show a message
      if (xtermRef.current) {
        xtermRef.current.writeln(
          "# Downloaded article_data.csv and fact_check_data.csv to computer",
        );
      }
    } catch (error) {
      console.error("Error downloading data:", error);
      if (xtermRef.current) {
        xtermRef.current.writeln(`# Error downloading data: ${error.message}`);
      }
    } finally {
      setRWorking(false);
    }
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
            terminalInstance.scrollToBottom();
            return;
          }

          // backspace: remove one char from local buffer and terminal view.
          if (code === BACKSPACE_KEY) {
            if (terminalInputBufferRef.current.length > 0) {
              terminalInputBufferRef.current =
                terminalInputBufferRef.current.slice(0, -1);
              terminalInstance.write("\b \b"); // actually delete the character
              terminalInstance.scrollToBottom();
            }
            return;
          }

          // ignore control characters; print and buffer regular characters.
          if (code < FIRST_PRINTABLE_CHAR) return;
          terminalInputBufferRef.current += data;
          terminalInstance.write(data);
          terminalInstance.scrollToBottom();
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
              console.debug("R: drawing new canvas page", event.data);
              if (drawCanvas.current) {
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
              setCanvasDrawIndex((currentDrawIndex) => {
                setCanvasImages((prev) => {
                  if (currentDrawIndex >= prev.length) {
                    return [...prev, url];
                  }
                  const newImages = [...prev];
                  newImages[currentDrawIndex] = url;
                  return newImages;
                });
                return currentDrawIndex;
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
    if (!editorRef.current) return;

    // get current content
    const currentContent = viewRef.current
      ? viewRef.current.state.doc.toString()
      : "# hello, world!\n1 + 1\n\nplot(cars)";

    if (viewRef.current) {
      viewRef.current.destroy();
      viewRef.current = null;
    }

    // create new view with current content
    viewRef.current = new EditorView({
      doc: currentContent,
      extensions: [basicSetup, r(), darkMode ? oneDark : []],
      parent: editorRef.current,
    });

    // (re-?)focus the editor
    viewRef.current?.focus();
  }, [darkMode]);

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
    // setRWorking(false);
    // we'll set this to false when we get the prompt event, which indicates that r is done processing and waiting for more input
    // we don't really have a great way to know this, unfortunately.
    // (minus just looking for the prompt to come back. it's not as clean as i'd like, but it's what we have)
  };

  const interruptR = () => {
    if (!webRRef.current) return;
    webRRef.current.interrupt();
  };

  return (
    <main className="w-full h-screen">
      <div className="flex justify-bottom items-bottom">
        <h1 className="font-semibold text-2xl">Data Sandbox</h1>
        <div className="grow"></div>
        <Link to="/sandbox">
          <Button variant="link">
            <FlaskConicalOff />
            Basic
          </Button>
        </Link>
      </div>
      <Separator className="my-2" />
      <ResizablePanelGroup orientation="horizontal">
        <ResizablePanel>
          <ResizablePanelGroup orientation="vertical">
            <ResizablePanel defaultSize="75%">
              <div className="flex items-center justify-end space-x-2 p-2">
                <ButtonGroup>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="outline"
                        onClick={() => {
                          const input = document.createElement("input");
                          input.type = "file";
                          input.accept = ".R,.r,.txt";
                          input.onchange = async (e) => {
                            const file = (e.target as HTMLInputElement)
                              .files?.[0];
                            if (file && viewRef.current) {
                              const text = await file.text();
                              viewRef.current.dispatch({
                                changes: {
                                  from: 0,
                                  to: viewRef.current.state.doc.length,
                                  insert: text,
                                },
                              });
                            }
                          };
                          input.click();
                        }}
                      >
                        <Upload />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent side="bottom" sideOffset={8}>
                      Upload file
                    </TooltipContent>
                  </Tooltip>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="icon"
                        variant="outline"
                        onClick={() => {
                          if (!viewRef.current) return;
                          const content = viewRef.current.state.doc.toString();
                          const blob = new Blob([content], {
                            type: "text/plain",
                          });
                          const url = URL.createObjectURL(blob);
                          const link = document.createElement("a");
                          link.href = url;
                          link.download = `ARGUS-DataSandbox-${new Date().toLocaleTimeString().replaceAll(/[:\s]/g, "-")}.R`;
                          link.click();
                          URL.revokeObjectURL(url);
                        }}
                      >
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
                  <Tabs defaultValue="dl-everything">
                    <TabsList>
                      <TabsTrigger value="dl-everything">
                        Everything
                      </TabsTrigger>
                      <TabsTrigger value="dl-articles">Articles</TabsTrigger>
                      <TabsTrigger value="dl-checks">Fact Checks</TabsTrigger>
                    </TabsList>
                    <TabsContent value="dl-everything">
                      <p>This will fetch all the data at once.</p>
                    </TabsContent>
                  </Tabs>
                  <ButtonGroup>
                    <Button onClick={fetchData}>
                      <FolderDown />
                      Fetch Data to Sandbox
                    </Button>
                    <Button variant="secondary" onClick={downloadData}>
                      <Download />
                      Download Data to Computer
                    </Button>
                  </ButtonGroup>
                </TabsContent>
                <TabsContent value="documentation">
                  <DocumentationTab />
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
                            <TableCell
                              key={i}
                              className="max-w-[200px] overflow-hidden text-ellipsis"
                            >
                              {String(value)}
                            </TableCell>
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
                    className="mx-auto mb-4 h-7/8 bg-white"
                  />
                  <div className="flex items-center justify-center gap-4">
                    <Pagination>
                      <PaginationContent>
                        <PaginationItem>
                          <PaginationPrevious
                            onClick={(e) => {
                              e.preventDefault();
                              if (canvasImageIndex > 0) {
                                setCanvasImageIndex((prev) => prev - 1);
                              }
                            }}
                            className={
                              canvasImageIndex === 0
                                ? "pointer-events-none opacity-50"
                                : "cursor-pointer"
                            }
                            href="#"
                          />
                        </PaginationItem>
                        {canvasImages.map((_, index) => (
                          <PaginationItem key={index}>
                            <PaginationLink
                              onClick={(e) => {
                                e.preventDefault();
                                setCanvasImageIndex(index);
                              }}
                              isActive={canvasImageIndex === index}
                              href="#"
                              className="cursor-pointer"
                            >
                              {index + 1}
                            </PaginationLink>
                          </PaginationItem>
                        ))}
                        <PaginationItem>
                          <PaginationNext
                            onClick={(e) => {
                              e.preventDefault();
                              if (canvasImageIndex < canvasImages.length - 1) {
                                setCanvasImageIndex((prev) => prev + 1);
                              }
                            }}
                            className={
                              canvasImageIndex === canvasImages.length - 1
                                ? "pointer-events-none opacity-50"
                                : "cursor-pointer"
                            }
                            href="#"
                          />
                        </PaginationItem>
                      </PaginationContent>
                    </Pagination>
                    <ButtonGroup className="pr-2">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            size="icon"
                            variant="outline"
                            onClick={() => {
                              const link = document.createElement("a");
                              link.href = canvasImages[canvasImageIndex];
                              link.download = `plot-${canvasImageIndex + 1}.png`;
                              link.click();
                            }}
                          >
                            <Download />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Download Plot</p>
                        </TooltipContent>
                      </Tooltip>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            size="icon"
                            variant="destructive"
                            onClick={() => {
                              const urlToRevoke =
                                canvasImages[canvasImageIndex];
                              setCanvasImages((prev) =>
                                prev.filter((_, i) => i !== canvasImageIndex),
                              );
                              setCanvasDrawIndex((prev) =>
                                Math.max(0, prev - 1),
                              );
                              setCanvasImageIndex((prev) =>
                                Math.min(prev, canvasImages.length - 2),
                              );
                              URL.revokeObjectURL(urlToRevoke);
                            }}
                          >
                            <Trash2 />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Remove Plot</p>
                        </TooltipContent>
                      </Tooltip>
                    </ButtonGroup>
                  </div>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-full space-y-4 px-4">
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
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>
      </ResizablePanelGroup>
    </main>
  );
}

function DocumentationTab() {
  const [currentDocumentation, setCurrentDocumentation] =
    useState("data-reference");

  const docUrls: Record<string, string> = {
    "data-reference": "/docs/data-reference",
    "advanced-data-sandbox": "/docs/advanced-data",
    "r-intro": "https://cran.r-project.org/doc/manuals/r-release/R-intro.html",
    "ggplot-reference": "https://ggplot2.tidyverse.org/reference/index.html",
    "ggplot-book": "https://ggplot2-book.org/",
    ggthemes: "https://jrnold.github.io/ggthemes",
    plotly: "https://plotly.com/r/",
    "r-graphics": "https://r-graphics.org/",
  };

  const currentUrl = docUrls[currentDocumentation] || "";

  const openExternal = () => {
    if (currentUrl) {
      window.open(currentUrl, "_blank", "noopener,noreferrer");
    }
  };

  return (
    <>
      <div className="flex gap-2 mb-2">
        <Select
          value={currentDocumentation}
          onValueChange={setCurrentDocumentation}
        >
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem value="data-reference">Data Reference</SelectItem>
              <SelectItem value="advanced-data-sandbox">
                Advanced Data Sandbox
              </SelectItem>
              <SelectItem value="r-intro">An Introduction to R</SelectItem>
              <SelectItem value="ggplot-reference">
                ggplot2 Reference
              </SelectItem>
              <SelectItem value="ggplot-book">
                ggplot2: Elegant Graphics for Data Analysis
              </SelectItem>
              <SelectItem value="ggthemes">ggthemes</SelectItem>
              <SelectItem value="plotly">plotly</SelectItem>
              <SelectItem value="r-graphics">R Graphics Cookbook</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={openExternal}>
          <ExternalLink />
        </Button>
      </div>
      <iframe
        className="w-full h-[calc(100vh-300px)]"
        src={currentUrl}
        title={currentDocumentation}
      />
    </>
  );
}

export default DataSandboxView;
