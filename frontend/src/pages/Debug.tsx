import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Bot, Cpu, Database, Eraser, Map, Search } from "lucide-react";
import prettyMilliseconds from "pretty-ms";
import prettyBytes from "pretty-bytes";
import { useState } from "react";
import { useInterval } from "usehooks-ts";
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
import { PrettyDynamicDuration } from "@/components/PrettyDuration";

function Debug() {
  const [resources, setResources] = useState({
    cpu: 0,
    memory_used: 0,
    memory_total: 0,
    gpu: null as number | null,
    gpu_memory_used: null as number | null,
    gpu_memory_total: null as number | null,
    gpu_available: false,
  });
  const [statistics, setStatistics] = useState({
    factChecks: 0,
    activeFactChecks: 0,
    articlesInDatabase: 0,
  });
  const [loadedModels, setLoadedModels] = useState([]);
  const [articleURLs, setArticleURLs] = useState("");
  const [onlySummarize, setOnlySummarize] = useState(false);
  const [bulkImportSubmitting, setBulkImportSubmitting] = useState(false);
  const [activeFactChecks, setActiveFactChecks] = useState<string[]>([]);
  const [autoRoamState, setAutoRoamState] = useState(false);
  const [autoRoamStartTime, setAutoRoamStartTime] = useState<Date | null>(null);

  // resources
  useInterval(async () => {
    const response = await fetch("/api/debug/resources");
    if (response.ok) {
      const data = await response.json();
      setResources(data);
    } else {
      console.error("Failed to fetch debug data");
    }
  }, 5000);

  // statistics
  useInterval(async () => {
    const response = await fetch("/api/debug/statistics");
    if (response.ok) {
      const data = await response.json();
      setStatistics(data);
    } else {
      console.error("Failed to fetch debug data");
    }
  }, 10000);

  // models
  useInterval(async () => {
    const response = await fetch("/api/debug/models");
    if (response.ok) {
      const data = await response.json();
      setLoadedModels(data["models"]);
    }
  }, 10000);

  useInterval(async () => {
    if (autoRoamState) {
      const response = await fetch("/api/create/random");
    }
  }, 10000);

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

  useInterval(async () => {
    const response = await fetch("/api/debug/active_checks");
    if (response.ok) {
      const data = await response.json();
      setActiveFactChecks(data);
    }
  }, 10000);

  return (
    <main className="p-4">
      <h1 className="font-semibold text-2xl">Debug Page</h1>
      <div className="flex gap-4 my-4">
        <Card className="w-1/2">
          <CardHeader>
            <CardTitle>
              <div className="flex items-center gap-2">
                <Cpu />
                Resources
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p>CPU Usage: {resources.cpu}%</p>
            <p>
              Memory Usage: {prettyBytes(resources.memory_used)} /{" "}
              {prettyBytes(resources.memory_total)}
            </p>
            <p>
              GPU Usage:{" "}
              {resources.gpu_available && resources.gpu !== null
                ? `${resources.gpu}%`
                : "N/A"}
            </p>
            <p>
              GPU Memory Usage:{" "}
              {resources.gpu_available &&
              resources.gpu_memory_used !== null &&
              resources.gpu_memory_total !== null
                ? `${prettyBytes(resources.gpu_memory_used)} / ${prettyBytes(resources.gpu_memory_total)}`
                : "N/A"}
            </p>
          </CardContent>
        </Card>
        <Card className="w-1/2">
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
          </CardContent>
        </Card>
        <Card className="w-1/2">
          <CardHeader>
            <CardTitle>
              <div className="flex items-center gap-2">
                <Bot />
                Loaded Models
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadedModels.map((model: any) => (
              <div key={model.name}>
                <p className="font-semibold">{model.name}</p>
                <p>Size: {(model.size / (1024 * 1024 * 1024)).toFixed(2)} GB</p>
                <p>
                  VRAM Usage:{" "}
                  {(model.size_vram / (1024 * 1024 * 1024)).toFixed(2)} GB
                </p>
                <p>
                  CPU/GPU Split:{" "}
                  {(
                    ((model.size - model.size_vram) / model.size) *
                    100
                  ).toFixed(2)}
                  % / {((model.size_vram / model.size) * 100).toFixed(2)}%
                </p>
                <p>Context Length: {model.context_length}</p>
                <Tooltip>
                  <TooltipTrigger>
                    <p>
                      Unloads In:{" "}
                      {prettyMilliseconds(
                        new Date(model.expires_at).getTime() - Date.now(),
                        {
                          verbose: true,
                        },
                      )}
                    </p>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{new Date(model.expires_at).toLocaleString()}</p>
                  </TooltipContent>
                </Tooltip>
              </div>
            ))}
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
            {autoRoamState && (
              <p>
                Running For:{" "}
                <PrettyDynamicDuration
                  date={autoRoamStartTime}
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
              <p>None</p>
            ) : (
              activeFactChecks.map((factCheckId) => (
                <a key={factCheckId} href={`/details/${factCheckId}`}>
                  {factCheckId}
                </a>
              ))
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

export default Debug;
