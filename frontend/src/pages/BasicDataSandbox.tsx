import { useTheme } from "@/components/theme-provider";
import { Button } from "@/components/ui/button";
import { ButtonGroup } from "@/components/ui/button-group";
import { Calendar } from "@/components/ui/calendar";
import {
  Combobox,
  ComboboxChip,
  ComboboxChips,
  ComboboxChipsInput,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxItem,
  ComboboxList,
  ComboboxValue,
  useComboboxAnchor,
} from "@/components/ui/combobox";
import { Field, FieldLabel } from "@/components/ui/field";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Tooltip, TooltipContent } from "@/components/ui/tooltip";
import { TooltipTrigger } from "@radix-ui/react-tooltip";
import {
  CalendarIcon,
  Download,
  FlaskConical,
  MoonStar,
  RefreshCw,
  Sun,
  SunMoon,
} from "lucide-react";
import { useState, useEffect, useRef } from "react";
import type { DateRange } from "react-day-picker";
import { Link } from "react-router-dom";
import { WebR } from "webr";
import { convertToCSV } from "./convertToCSV";
import TernaryThemeButton from "@/components/TernaryThemeButton";


export default function BasicDataSandboxView() {
  const { isDarkMode } = useTheme();
  const [currentGraph, setCurrentGraph] = useState("");
  const [date, setDate] = useState<DateRange | undefined>({
    from: undefined,
    to: undefined,
  });
  const [sources, setSources] = useState<string[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [plotType, setPlotType] = useState<"none" | "image" | "browser">(
    "none",
  );

  const [rLoaded, setRLoaded] = useState(false);
  const [rBusy, setRBusy] = useState(false);
  const [busyMessage, setBusyMessage] = useState("");
  const [plotImage, setPlotImage] = useState<string | null>(null);
  const [plotTheme, setPlotTheme] = useState<string>("auto_light_dark");
  const [actualTheme, setActualTheme] = useState<string>("");

  useEffect(() => {
    switch (plotTheme) {
      case "auto_light_dark":
        setActualTheme(isDarkMode ? "theme_dark()" : "theme_light()");
        break;
      case "auto_gray_inverse":
        setActualTheme(isDarkMode ? "theme_igray()" : "theme_gray()");
        break;
      case "auto_solarized":
        setActualTheme(
          isDarkMode ? "theme_solarized(light=FALSE)" : "theme_solarized()",
        );
        break;
      case "theme_solarized_light":
        setActualTheme("theme_solarized()");
        break;
      case "theme_solarized_dark":
        setActualTheme("theme_solarized(light=FALSE)");
        break;
      default:
        setActualTheme(`${plotTheme}()`);
    }
  }, [plotTheme, isDarkMode]);

  const webRRef = useRef<WebR | null>(null);
  const drawCanvas = useRef<OffscreenCanvas | null>(null);

  const sourcesComboboxAnchor = useComboboxAnchor();

  // init webr
  useEffect(() => {
    let isDisposed = false;

    const loadR = async () => {
      try {
        setRBusy(true);
        setBusyMessage("Loading WebR...");

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

        // Start processing WebR stream events BEFORE doing any operations
        processRStreamEvents(webR, () => isDisposed);

        if (isDisposed) return;

        setBusyMessage("Installing R packages...");
        await webR.installPackages(["tidyverse", "ggdensity"]);

        if (isDisposed) return;

        setBusyMessage("Loading data...");
        await loadData(webR);

        if (isDisposed) return;

        setBusyMessage("Loading R functions...");
        await loadRScript(webR);

        if (isDisposed) return;

        setRLoaded(true);
        setRBusy(false);
        setBusyMessage("");
      } catch (error) {
        console.error("Error loading R:", error);
        setBusyMessage("Error loading R: " + error);
        setRLoaded(false);
        setRBusy(false);
      }
    };

    loadR();

    return () => {
      isDisposed = true;
    };
  }, []);

  // process webr stream events
  const processRStreamEvents = async (
    webR: WebR,
    isDisposed: () => boolean,
  ) => {
    for await (const event of webR.stream()) {
      if (isDisposed()) {
        return;
      }

      switch (event.type) {
        case "stdout":
          console.log("R stdout:", event.data);
          break;
        case "stderr":
          console.warn("R stderr:", event.data);
          break;
        case "prompt":
          // r is idle and ready for the next command.
          setRBusy(false);
          setBusyMessage("");
          break;
        case "canvas":
          switch (event.data.event) {
            case "canvasNewPage":
              console.debug("R: drawing new canvas page", event.data);
              drawCanvas.current = new OffscreenCanvas(1008, 1008);
              setPlotType("none");
              setPlotImage(null);
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
              ctx.drawImage(event.data.image, 0, 0);

              const blob = await drawCanvas.current.convertToBlob();
              const url = URL.createObjectURL(blob);
              setPlotImage(url);
              setPlotType("image");

              setRBusy(false);
              setBusyMessage("");
              break;
          }
          break;
        default:
          console.log("Unknown R event type:", event.type, event);
          break;
      }
    }
  };

  const loadData = async (webR: WebR) => {
    try {
      try {
        await webR.FS.mkdir("/home/web_user/data");
      } catch {
        // Directory already exists
      }

      const response = await fetch("/api/data");
      if (!response.ok) {
        throw new Error("Failed to fetch data");
      }
      const data = await response.json();

      await webR.FS.writeFile(
        "/home/web_user/data/article_data.csv",
        new TextEncoder().encode(convertToCSV(data.articles)),
      );
      await webR.FS.writeFile(
        "/home/web_user/data/fact_check_data.csv",
        new TextEncoder().encode(convertToCSV(data.fact_checks)),
      );

      const uniqueSources = new Set<string>();
      data.fact_checks.forEach((fc: any) => {
        if (fc.sitename) uniqueSources.add(fc.sitename);
        if (fc.site_name) uniqueSources.add(fc.site_name);
        if (fc.site) uniqueSources.add(fc.site);
      });
      setSources(Array.from(uniqueSources).sort());
    } catch (error) {
      console.error("Error loading data:", error);
      throw error;
    }
  };

  const loadRScript = async (webR: WebR) => {
    try {
      const response = await fetch("/r/graphfunctions.R", {
        cache: "no-cache",
      });
      if (!response.ok) {
        throw new Error("Failed to fetch R script");
      }
      const script = await response.text();

      if (!script || script.trim().length === 0) {
        throw new Error("R script is empty - possibly a caching issue");
      }

      console.log("Loading R script, length:", script.length);

      await webR.evalRVoid(script);
    } catch (error) {
      console.error("Error loading R script:", error);
      throw error;
    }
  };

  // Generate plot
  const generatePlot = async () => {
    if (!webRRef.current || !currentGraph || rBusy) return;

    setRBusy(true);
    setBusyMessage("Generating plot...");
    setPlotType("none");
    setPlotImage(null);

    try {
      let rCommand = "";
      const sourcesArg =
        selectedSources.length > 0
          ? `c(${selectedSources.map((s) => `"${s}"`).join(", ")})`
          : "NULL";
      const startDateArg = date?.from
        ? `"${date.from.toISOString().split("T")[0]}"`
        : "NULL";
      const endDateArg = date?.to
        ? `"${date.to.toISOString().split("T")[0]}"`
        : "NULL";

      await webRRef.current.evalRVoid(
        `library("ggplot2")\nlibrary("ggthemes")\ntheme_set(${actualTheme})`,
      );

      switch (currentGraph) {
        case "accuracy_completeness_scores_by_source":
          rCommand = `print(accuracy_completeness_scores_by_source(sources=${sourcesArg}))`;
          break;
        case "bias_scores_by_source":
          rCommand = `print(bias_scores_by_source(sources=${sourcesArg}, start_date=${startDateArg}, end_date=${endDateArg}))`;
          break;
        case "scores_by_time":
          rCommand = `print(scores_by_time(sources=${sourcesArg}, start_date=${startDateArg}, end_date=${endDateArg}))`;
          break;
        case "gathered_articles_by_time":
          rCommand = `print(gathered_articles_by_time(start_date=${startDateArg}, end_date=${endDateArg}))`;
          break;
        case "fact_check_time_breakdown":
          // these plot types are not implemented yet
          setBusyMessage("This plot type is not implemented yet");
          setTimeout(() => {
            setRBusy(false);
            setBusyMessage("");
          }, 2000);
          return;
        default:
          console.warn("Unknown graph type:", currentGraph);
          setRBusy(false);
          setBusyMessage("");
          return;
      }

      console.log("Executing R command:", rCommand);
      webRRef.current.evalRVoid(rCommand);
    } catch (error) {
      console.error("Error generating plot:", error);
      setBusyMessage("Error generating plot");
      setRBusy(false);
    }
  };

  // when graph type changes, generate new plot
  useEffect(() => {
    if (currentGraph && rLoaded) {
      generatePlot();
    }
  }, [currentGraph, rLoaded]);

  // filter changes: refresh the plot (with debounce)
  useEffect(() => {
    if (currentGraph && rLoaded && !rBusy) {
      const timer = setTimeout(() => {
        generatePlot();
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [date, selectedSources, actualTheme]);

  const downloadPlot = () => {
    if (!plotImage) return;

    const link = document.createElement("a");
    link.href = plotImage;
    link.download = `${currentGraph}_${Date.now()}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <>
      <main className="p-2">
        <div className="flex justify-bottom items-bottom">
          <h1 className="font-semibold text-2xl">Data Sandbox</h1>
          <div className="grow"></div>
          <Link to="/sandbox/advanced">
            <Button variant="link">
              <FlaskConical />
              Advanced
            </Button>
          </Link>
        </div>
        <Separator className="my-2" />
        <div className="w-full h-[calc(100vh-80px)] overflow-hidden">
          <ResizablePanelGroup
            orientation="horizontal"
            className="w-full h-full"
          >
            <ResizablePanel className="pr-2 overflow-hidden">
              <ButtonGroup>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="secondary"
                      disabled={plotType === "none"}
                      onClick={downloadPlot}
                    >
                      <Download />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Download Plot (.png)</TooltipContent>
                </Tooltip>
                <TernaryThemeButton variant="secondary" />
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="secondary"
                      disabled={!rLoaded || !currentGraph}
                      onClick={generatePlot}
                    >
                      <RefreshCw />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Refresh Plot</TooltipContent>
                </Tooltip>
              </ButtonGroup>
              <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl w-full h-[calc(100vh-120px)] mt-2 flex items-center justify-center relative overflow-auto p-4">
                {rBusy && (
                  <div className="flex flex-col items-center gap-2">
                    <Spinner className="size-8" />
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {busyMessage}
                    </p>
                  </div>
                )}
                {!rBusy && plotImage && (
                  <img
                    src={plotImage}
                    alt="Plot"
                    className="min-w-full min-h-full object-contain"
                  />
                )}
                {!rBusy && !plotImage && rLoaded && (
                  <p className="text-gray-500 dark:text-gray-400">
                    Select a plot type to begin
                  </p>
                )}
              </div>
            </ResizablePanel>
            <ResizableHandle withHandle={true} />
            <ResizablePanel className="pl-2 overflow-y-auto" defaultSize="20%">
              <Field>
                <FieldLabel htmlFor="chart-type">Plot Type</FieldLabel>
                <Select
                  value={currentGraph}
                  onValueChange={setCurrentGraph}
                  disabled={!rLoaded}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a Plot" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectLabel>By Source</SelectLabel>
                      <SelectItem value="accuracy_completeness_scores_by_source">
                        Accuracy & Completeness Scores
                      </SelectItem>
                      <SelectItem value="bias_scores_by_source">
                        Bias Scores
                      </SelectItem>
                    </SelectGroup>
                    <SelectGroup>
                      <SelectLabel>By Time</SelectLabel>
                      <SelectItem value="scores_by_time">Scores</SelectItem>
                      <SelectItem value="gathered_articles_by_time">
                        Gathered Articles
                      </SelectItem>
                    </SelectGroup>
                    <SelectGroup>
                      <SelectLabel>Misc.</SelectLabel>
                      <SelectItem value="fact_check_time_breakdown">
                        Fact Check Time Breakdown
                      </SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </Field>
              <Field>
                <FieldLabel htmlFor="date-range">Date Range</FieldLabel>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      id="date-range"
                      className="justify-state px-2.5 font-normal"
                      disabled={!rLoaded}
                    >
                      <CalendarIcon />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="range"
                      captionLayout="dropdown"
                      disabled={{ after: new Date() }}
                      defaultMonth={date?.from}
                      selected={date}
                      onSelect={setDate}
                      numberOfMonths={3}
                    />
                  </PopoverContent>
                </Popover>
              </Field>
              <Field>
                <FieldLabel htmlFor="source-picker">Sources</FieldLabel>
                <Combobox
                  multiple
                  autoHighlight
                  items={sources}
                  value={selectedSources}
                  onValueChange={setSelectedSources}
                  disabled={!rLoaded}
                >
                  <ComboboxChips ref={sourcesComboboxAnchor} className="w-full">
                    <ComboboxValue>
                      {(values) => (
                        <>
                          {values.map((value: string) => (
                            <ComboboxChip key={value}>{value}</ComboboxChip>
                          ))}
                          <ComboboxChipsInput />
                        </>
                      )}
                    </ComboboxValue>
                  </ComboboxChips>
                  <ComboboxContent anchor={sourcesComboboxAnchor}>
                    <ComboboxEmpty>No items found.</ComboboxEmpty>
                    <ComboboxList>
                      {(item) => (
                        <ComboboxItem key={item} value={item}>
                          {item}
                        </ComboboxItem>
                      )}
                    </ComboboxList>
                  </ComboboxContent>
                </Combobox>
              </Field>
              <Field>
                <FieldLabel htmlFor="chart-type">Plot Theme</FieldLabel>
                <Select
                  value={plotTheme}
                  onValueChange={setPlotTheme}
                  disabled={!rLoaded}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a Theme" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectLabel>Automatic</SelectLabel>
                      <SelectItem value="auto_light_dark">
                        Light/Dark
                      </SelectItem>
                      <SelectItem value="auto_gray_inverse">
                        Gray/Gray (Inverse)
                      </SelectItem>
                      <SelectItem value="auto_solarized">
                        Solarized Light/Dark
                      </SelectItem>
                    </SelectGroup>
                    <SelectGroup>
                      <SelectLabel>ggplot2</SelectLabel>
                      <SelectItem value="theme_gray">Gray</SelectItem>
                      <SelectItem value="theme_bw">Black & White</SelectItem>
                      <SelectItem value="theme_linedraw">Line Draw</SelectItem>
                      <SelectItem value="theme_light">Light</SelectItem>
                      <SelectItem value="theme_dark">Dark</SelectItem>
                      <SelectItem value="theme_minimal">Minimal</SelectItem>
                      <SelectItem value="theme_classic">Classic</SelectItem>
                    </SelectGroup>
                    <SelectGroup>
                      <SelectLabel>ggthemes</SelectLabel>
                      <SelectItem value="theme_calc">Calc</SelectItem>
                      <SelectItem value="theme_clean">Clean</SelectItem>
                      <SelectItem value="theme_economist">Economist</SelectItem>
                      <SelectItem value="theme_excel">Excel</SelectItem>
                      <SelectItem value="theme_excel_new">
                        Excel (New)
                      </SelectItem>
                      <SelectItem value="theme_igray">
                        Gray (Inverse)
                      </SelectItem>
                      <SelectItem value="theme_fivethirtyeight">
                        FiveThirtyEight
                      </SelectItem>
                      <SelectItem value="theme_few">Few</SelectItem>
                      <SelectItem value="theme_solarized_light">
                        Solarized Light
                      </SelectItem>
                      <SelectItem value="theme_solarized_dark">
                        Solarized Dark
                      </SelectItem>
                      <SelectItem value="theme_tufte">Tufte</SelectItem>
                      <SelectItem value="theme_wsj">
                        Wall Street Journal
                      </SelectItem>
                      <SelectItem value="theme_tableau">Tableau</SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </Field>
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      </main>
    </>
  );
}
