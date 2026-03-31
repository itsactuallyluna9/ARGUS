import { Button } from "@/components/ui/button";
import { ButtonGroup, ButtonGroupText } from "@/components/ui/button-group";
import { Calendar } from "@/components/ui/calendar";
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
import { Tooltip, TooltipContent } from "@/components/ui/tooltip";
import { TooltipTrigger } from "@radix-ui/react-tooltip";
import {
  CalendarIcon,
  Cat,
  Download,
  FlaskConical,
  MoonStar,
  RefreshCw,
  Sun,
  SunMoon,
} from "lucide-react";
import { useState } from "react";
import type { DateRange } from "react-day-picker";
import { Link } from "react-router-dom";
import { useTernaryDarkMode } from "usehooks-ts";

export function TernaryDarkModeButton({ variant }: { variant: string }) {
  const { isDarkMode, ternaryDarkMode, _, toggleTernaryDarkMode } =
    useTernaryDarkMode({ localStorageKey: "argus-theme" });

  const buttonIcon = () => {
    switch (ternaryDarkMode) {
      case "system":
        return <SunMoon />;
      case "dark":
        return <MoonStar />;
      case "light":
        return <Sun />;
    }
  };

  return (
    <Tooltip>
      <TooltipTrigger>
        <Button onClick={toggleTernaryDarkMode} variant={variant}>
          {buttonIcon()}
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        {ternaryDarkMode.replace(/\w/, (char) => char.toUpperCase())}
      </TooltipContent>
    </Tooltip>
  );
}

export default function BasicDataSandboxView() {
  const [currentGraph, setCurrentGraph] = useState("");
  const [dataLoaded, setDataLoaded] = useState(false);
  const [date, setDate] = useState<DateRange | undefined>({
    from: undefined,
    to: undefined,
  });
  const [sources, setSources] = useState<string[]>([]);

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
        <div className="h-screen">
          <ResizablePanelGroup orientation="horizontal">
            <ResizablePanel className="pr-2">
              <ButtonGroup>
                <Button variant="secondary">
                  <Download />
                </Button>
                <TernaryDarkModeButton variant="secondary" />
                <Button variant="secondary">
                  <RefreshCw />
                </Button>
              </ButtonGroup>
              <div className="bg-gray-500 rounded-2xl w-50 h-50"></div>
            </ResizablePanel>
            <ResizableHandle />
            <ResizablePanel className="pl-2">
              <Field>
                <FieldLabel htmlFor="chart-type">Plot Type</FieldLabel>
                <Select value={currentGraph} onValueChange={setCurrentGraph}>
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
                      <SelectItem value="na">
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
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      </main>
    </>
  );
}
