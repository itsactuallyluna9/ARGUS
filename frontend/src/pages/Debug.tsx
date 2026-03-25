import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { Textarea } from "@/components/ui/textarea";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Bot, Cpu, Database } from "lucide-react";
import prettyMilliseconds from "pretty-ms";
import prettyBytes from 'pretty-bytes';
import { useState } from "react";
import { useInterval } from "usehooks-ts";

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
  const [loadedModels, setLoadedModels] = useState([])
  const [articleURLs, setArticleURLs] = useState("");
  const [onlySummarize, setOnlySummarize] = useState(false);
  const [bulkImportSubmitting, setBulkImportSubmitting] = useState(false);
  const [activeFactChecks, setActiveFactChecks] = useState<string[]>([]);
  

  // resources
  useInterval(async () => {
    const response = await fetch("/api/debug/resources");
    if (response.ok) {
      const data = await response.json();
      setResources(data);
    } else {
      console.error("Failed to fetch debug data");
    }
  }, 5000)

  // statistics
  useInterval(async () => {
    const response = await fetch("/api/debug/statistics");
    if (response.ok) {
      const data = await response.json();
      setStatistics(data);
    } else {
      console.error("Failed to fetch debug data");
    }
  }, 10000)

  // models
  useInterval(async () => {
    const response = await fetch("/api/debug/models");
    if (response.ok) {
      const data = await response.json();
      setLoadedModels(data["models"]);
    }
  }, 10000)

  const handleBulkImport = async () => {
    setBulkImportSubmitting(true);
    const urls = articleURLs.split("\n").map(url => url.trim()).filter(url => url.length > 0);
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
      setArticleURLs("--Invalid URLS--\n" + data.invalid_urls.join("\n"))
    }
    setBulkImportSubmitting(false);
  }

  useInterval(async () => {
    const response = await fetch("/api/debug/active_checks");
    if (response.ok) {
      const data = await response.json();
      setActiveFactChecks(data);
    }
  }, 10000)

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
            <p>Memory Usage: {prettyBytes(resources.memory_used)} / {prettyBytes(resources.memory_total)}</p>
            <p>GPU Usage: {resources.gpu_available && resources.gpu !== null ? `${resources.gpu}%` : "N/A"}</p>
            <p>
              GPU Memory Usage: {resources.gpu_available && resources.gpu_memory_used !== null && resources.gpu_memory_total !== null
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
                <p>VRAM Usage: {(model.size_vram / (1024 * 1024 * 1024)).toFixed(2)} GB</p>
                <p>CPU/GPU Split: {((model.size - model.size_vram) / model.size * 100).toFixed(2)}% / {((model.size_vram) / model.size * 100).toFixed(2)}%</p>
                <p>Context Length: {model.context_length}</p>
                <Tooltip>
                  <TooltipTrigger>
                    <p>Unloads In: {prettyMilliseconds(new Date(model.expires_at).getTime() - Date.now(), {
                      verbose: true,
                    })}</p>
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
            <Textarea placeholder="Article URLs..." value={articleURLs} onChange={(e) => setArticleURLs(e.target.value)} />
            <div className="flex items-center gap-4 mt-2">
              {/* checkbox - use shadcn ui */}
              <div className="flex items-center gap-2">
                <Checkbox id="only-summarize" checked={onlySummarize} disabled={bulkImportSubmitting} onCheckedChange={(checked) => setOnlySummarize(checked as boolean)} />
                <label htmlFor="only-summarize">Just Summarize</label>
              </div>
              <Button onClick={handleBulkImport} disabled={bulkImportSubmitting}>
                {bulkImportSubmitting ? <Spinner /> : <Bot />}
                Submit
              </Button>
            </div>
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
              activeFactChecks.map((factCheckId) => <a key={factCheckId} href={`/details/${factCheckId}`}>{factCheckId}</a>)
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export default Debug;
