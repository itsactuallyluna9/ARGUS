import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import {
  Bot,
  BrushCleaning,
  Clock,
  Database,
  Eraser,
  Map,
  Search,
} from "lucide-react";
import { useEffect, useState } from "react";
import useSWR from "swr";
import { ButtonGroup } from "@/components/ui/button-group";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  PrettyDuration,
  PrettyDynamicDuration,
} from "@/components/PrettyDuration";
import { statusFetcher } from "./Details";
import { Skeleton } from "@/components/ui/skeleton";
import { type CheckMetadata, type AgentMetadata } from "../DetailsResponse";

type DebugStatistics = {
  factChecks: number;
  activeFactChecks: number;
  articlesInDatabase: number;
};

const fetcher = async <T,>(url: string): Promise<T> => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
};

function Debug() {
  const [articleURLs, setArticleURLs] = useState("");
  const [onlySummarize, setOnlySummarize] = useState(false);
  const [bulkImportSubmitting, setBulkImportSubmitting] = useState(false);
  const [autoRoamState, setAutoRoamState] = useState(false);
  const [autoRoamStartTime, setAutoRoamStartTime] = useState<Date | null>(null);

  const statistics = useSWR<DebugStatistics>("/api/debug/statistics", fetcher, {
    refreshInterval: 10000,
  }).data ?? {
    factChecks: 0,
    activeFactChecks: 0,
    articlesInDatabase: 0,
  };

  const activeFactChecks =
    useSWR<string[]>("/api/debug/active_checks", fetcher, {
      refreshInterval: 10000,
    }).data ?? [];

  // TODO: look into making this /api/create/random
  useEffect(() => {
    if (!autoRoamState) {
      return;
    }

    let cancelled = false;
    let sleepTimeout: ReturnType<typeof setTimeout> | null = null;

    const sleep = (ms: number) =>
      new Promise<void>((resolve) => {
        sleepTimeout = setTimeout(resolve, ms);
      });

    const runAutoRoam = async () => {
      while (!cancelled) {
        try {
          await fetch("/api/createrandom");
        } catch (error) {
          if (!cancelled) {
            console.error("Auto-roam create random failed", error);
          }
        }

        if (cancelled) {
          break;
        }

        await sleep(30000);
      }
    };

    runAutoRoam();

    return () => {
      cancelled = true;
      if (sleepTimeout) {
        clearTimeout(sleepTimeout);
      }
    };
  }, [autoRoamState]);

  const handleBulkImport = async () => {
    setBulkImportSubmitting(true);
    const urls = articleURLs
      .split("\n")
      .map((url) => url.trim())
      .filter((url) => url.length > 0);
    const response = await fetch("/api/debug/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        urls,
        summarizeOnly: onlySummarize,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      alert(data.message);
      setArticleURLs("--Invalid URLS--\n" + data.invalid_urls.join("\n"));
    }
    setBulkImportSubmitting(false);
  };

  function startDBClean() {
    fetch("/api/cleandb");
  }

  return (
    <main className="p-4">
      <h1 className="font-semibold text-2xl">Debug Page</h1>
      <div className="flex gap-4 my-4">
        <Card className="w-full">
          <CardHeader>
            <CardTitle>
              <div className="flex items-center gap-2">
                <Database />
                Statistics
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p>FactChecks: {statistics.factChecks}</p>
            <p>Active FactChecks: {statistics.activeFactChecks}</p>
            <p>Articles in Database: {statistics.articlesInDatabase}</p>
            <Button variant="destructive" onClick={startDBClean}>
              <BrushCleaning />
              Clean Database
            </Button>
          </CardContent>
        </Card>
      </div>
      <Separator className="my-4" />
      <div className="grid grid-cols-1 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Bulk Import</CardTitle>
          </CardHeader>
          <CardContent>
            {/* large textbox, then "only summarize" checkbox and submit on same line */}
            <Textarea
              placeholder="Article URLs (separated by newlines)..."
              value={articleURLs}
              onChange={(e) => setArticleURLs(e.target.value)}
            />
            <div className="flex items-center gap-4 mt-2">
              {/* checkbox - use shadcn ui */}
              <div className="flex items-center gap-2">
                <Checkbox
                  id="only-summarize"
                  checked={onlySummarize}
                  disabled={bulkImportSubmitting}
                  onCheckedChange={(checked) =>
                    setOnlySummarize(checked as boolean)
                  }
                />
                <label htmlFor="only-summarize">Just Summarize</label>
              </div>
              <Button
                onClick={handleBulkImport}
                disabled={bulkImportSubmitting}
              >
                {bulkImportSubmitting ? <Spinner /> : <Bot />}
                Submit
              </Button>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Auto-Roam</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Roaming: {autoRoamState ? "Yes" : "No"}</p>
            <p>
              System State: {activeFactChecks.length === 0 ? "Idle" : "Active"}
            </p>
            {autoRoamState && autoRoamStartTime && (
              <p>
                Running For:{" "}
                <PrettyDynamicDuration
                  date={autoRoamStartTime}
                  timeResolution={1000}
                  msOpts={{ verbose: true, secondsDecimalDigits: 0 }}
                />
              </p>
            )}{" "}
            <Button
              onClick={() => {
                setAutoRoamStartTime(autoRoamState ? null : new Date());
                setAutoRoamState(!autoRoamState);
              }}
              variant={autoRoamState ? "destructive" : "default"}
            >
              {autoRoamState ? <Spinner /> : <Map />}
              {autoRoamState ? "Stop" : "Start"} Auto-Roam
            </Button>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Active Fact Checks</CardTitle>
          </CardHeader>
          <CardContent>
            {activeFactChecks.length === 0 ? (
              <p className="text-muted-foreground">None</p>
            ) : (
              <ul className="space-y-2">
                {activeFactChecks.map((factCheckId) => (
                  <li key={factCheckId}>
                    <DebugFactCheck factCheckId={factCheckId} />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>ChromaDB Viewer</CardTitle>
          </CardHeader>
          <CardContent>
            <ChromaViewer />
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

function ChromaViewer() {
  const [collection, setCollection] = useState("");
  const [queryText, setQueryText] = useState("");
  const [ids, setIDs] = useState("");
  const [limit, setLimit] = useState(10);

  const [searching, setSearching] = useState(false);
  const [deleting, setDeleting] = useState(false);
  // doingNetwork is true when either searching or deleting is true
  const doingNetwork = searching || deleting;
  const [results, setResults] = useState(null);
  const [error, setError] = useState<string | null>(null);

  const getParams = (method: string) => {
    return {
      method,
      collection,
      query_texts: queryText.split(";;").filter((str) => str.trim() !== ""),
      ids: ids.split(",").filter((str) => str.trim() !== ""),
      limit: limit,
    };
  };

  const onSearch = async () => {
    setSearching(true);
    setError(null);
    try {
      const params = getParams("search");
      const response = await fetch("/api/debug/chroma", {
        method: "POST",
        body: JSON.stringify(params),
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unknown error occurred",
      );
      console.error("ChromaDB search error:", err);
    } finally {
      setSearching(false);
    }
  };

  const onDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      const params = getParams("delete");
      const response = await fetch("/api/debug/chroma", {
        method: "POST",
        body: JSON.stringify(params),
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
      // Clear inputs after successful deletion
      setIDs("");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "An unknown error occurred",
      );
      console.error("ChromaDB delete error:", err);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      <Select
        disabled={doingNetwork}
        value={collection}
        onValueChange={setCollection}
      >
        <SelectTrigger>
          <SelectValue placeholder="Collection" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem value="articles">Articles</SelectItem>
            <SelectItem value="fact_checks">Fact Checks</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <Input
        disabled={doingNetwork}
        value={queryText}
        onChange={(e) => setQueryText(e.target.value)}
        placeholder="Query Text (separated by ;;)"
      />
      <Input
        disabled={doingNetwork}
        value={ids}
        onChange={(e) => setIDs(e.target.value)}
        placeholder="IDs (separated by commas)"
      />
      <Input
        disabled={doingNetwork}
        value={limit.toString()}
        onChange={(e) => {
          const num = parseInt(e.target.value);
          if (!isNaN(num) && num > 0) setLimit(num);
        }}
        placeholder="Limit"
        type="number"
        min="1"
      />
      <ButtonGroup>
        <Button disabled={doingNetwork} onClick={onSearch}>
          {searching ? <Spinner /> : <Search />}
          Search
        </Button>
        <Button
          disabled={doingNetwork}
          onClick={onDelete}
          variant="destructive"
        >
          {deleting ? <Spinner /> : <Eraser />}
          Delete
        </Button>
      </ButtonGroup>

      {error && (
        <div className="p-4 mb-4 bg-red-50 border border-red-200 text-red-800 rounded">
          Error: {error}
        </div>
      )}

      {results && (
        <div className="mt-4">
          <h2 className="font-semibold mb-2">Results:</h2>
          <pre className="bg-gray-50 p-4 rounded overflow-auto dark:bg-gray-950 dark:text-white">
            {JSON.stringify(results, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

function DebugFactCheck({ factCheckId }: { factCheckId: string }) {
  const { data, isLoading, error } = useSWR<CheckMetadata>(
    ["/api/status", factCheckId],
    statusFetcher,
    {
      refreshInterval: 5000,
    },
  );

  if (error) {
    return <div className="text-red-500">Error loading fact check status</div>;
  }

  if (isLoading) {
    return <Skeleton className="h-4 w-1/3" />;
  }

  function AgentDuration({
    agent,
    agentName,
  }: {
    agent: AgentMetadata | undefined;
    agentName: string;
  }) {
    if (!agent) {
      return <div>{agentName} Not Started</div>;
    }
    return (
      <div>
        {agentName}:{" "}
        {agent.started && agent.finished ? (
          <>
            <PrettyDuration
              milliseconds={
                Date.parse(agent.finished) - Date.parse(agent.started)
              }
            />{" "}
            (Completed)
          </>
        ) : (
          <PrettyDynamicDuration date={new Date(agent.started) || new Date()} />
        )}{" "}
        ({agent.total_tool_calls} tool calls)
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2">
      <a href={`/details/${factCheckId}`} className="hover:underline">
        {factCheckId}
        {data?.article_metadata.title
          ? ` - ${data.article_metadata.title}`
          : ""}
      </a>
      <div>
        Total:{" "}
        {data ? (
          <PrettyDynamicDuration
            date={
              new Date(data.fact_check_metadata.check_started) ||
              new Date(data.fact_check_metadata.check_submitted)
            }
          />
        ) : (
          "Loading..."
        )}
        {data?.fact_check_metadata.scraper_duration && (
          <div>
            Scraper:{" "}
            <PrettyDuration
              milliseconds={data.fact_check_metadata.scraper_duration || -1}
            />
          </div>
        )}
        {data?.fact_check_metadata.summary_duration && (
          <div>
            Summary:{" "}
            <PrettyDuration
              milliseconds={data.fact_check_metadata.summary_duration || -1}
            />
          </div>
        )}
        <AgentDuration
          agent={data?.fact_check_metadata.accuracy_agent}
          agentName="Accuracy"
        />
        <AgentDuration
          agent={data?.fact_check_metadata.completeness_agent}
          agentName="Completeness"
        />
        <AgentDuration
          agent={data?.fact_check_metadata.bias_agent}
          agentName="Bias"
        />
      </div>
    </div>
  );
}

export default Debug;
